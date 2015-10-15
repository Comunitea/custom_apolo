# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, exceptions, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.product._common import rounding

intervals = {
    'monthly': 1,
    'annual': 1,
    'quarterly': 3,
    'semiannual': 6,
}


class calculate_rappel_wizard(models.TransientModel):

    _name = "rappel.calculate.wizard"

    date_start = fields.Date('Date start', required=True)
    date_stop = fields.Date('Date stop', required=True)
    customer_ids = fields.Many2many('res.partner', 'rappel_customer_rel',
                                    'rappel_wizard_id', 'customer_id',
                                    'Customers', help='Select customers to \
calculate rappels.  If left blank is calculated for all')

    @api.model
    def _compute_qty_obj(self, from_unit, invoice_line, to_unit):
        conv = invoice_line.product_id._conv_units(from_unit, to_unit, 0)
        return invoice_line.quantity * conv

    @api.multi
    def _get_periods(self, rappel):
        rappel_last_execution = \
            datetime.strptime(rappel.date_start, "%Y-%m-%d")
        if rappel.date_stop:
            rappel_date_stop = datetime.strptime(rappel.date_stop, "%Y-%m-%d")
        else:
            rappel_date_stop = datetime.now() + relativedelta(months=3)
        wiz_date_start = datetime.strptime(self.date_start, "%Y-%m-%d")
        wiz_date_stop = datetime.strptime(self.date_stop, "%Y-%m-%d")
        date_start = rappel_last_execution
        date_stop = rappel_date_stop
        periods = []
        date_aux = date_start
        while date_aux < date_stop:
            start = date_aux
            if rappel.periodicity == 'annual':
                end = date_aux + \
                    relativedelta(years=intervals[rappel.periodicity]) + \
                    relativedelta(days=-1)
                date_aux = date_aux + \
                    relativedelta(years=intervals[rappel.periodicity])
            else:
                end = date_aux + \
                    relativedelta(months=intervals[rappel.periodicity]) + \
                    relativedelta(days=-1)
                date_aux = date_aux + \
                    relativedelta(months=intervals[rappel.periodicity])
            period = (start, end)
            if end <= date_stop and end <= wiz_date_stop and \
                    end >= wiz_date_start:
                periods.append(period)
        return periods

    @api.multi
    def calculate_rappel(self):
        customers = self.customer_ids
        rappels = self.env['rappel'].search([])
        for rappel in rappels:
            for customer in customers and rappel.customer_ids & customers or rappel.customer_ids:
                if (rappel.date_stop and rappel.date_stop >= self.date_start
                        or not rappel.date_stop) and \
                        rappel.date_start < self.date_stop:
                    for period in self._get_periods(rappel):
                        partner_calc = {}
                        interval_start = period[0].date().strftime('%Y-%m-%d')
                        interval_stop = period[1].date().strftime('%Y-%m-%d')
                        if rappel.grouped:
                            inv_lines = self.env['account.invoice.line'].search(
                            [('invoice_id.date_invoice', '>=', interval_start),
                             ('invoice_id.date_invoice', '<=', interval_stop),
                             ('invoice_id.partner_id', 'child_of', customer.id),
                             ('invoice_id.state', 'in', ('open', 'paid')),
                             ('invoice_id.type', '=', 'out_invoice'),
                             ('product_id.product_tmpl_id', 'in',
                              rappel.get_products()),
                             ('tourism', '=', False),
                             ('promotion_line', '=', False)
                             ])
                            partner_calc[customer.id] = inv_lines
                        else:
                            all_partners = self.env['res.partner'].search(
                                [('id', 'child_of', customer.id),
                                 ('is_company', '=', True)])
                            for partner in all_partners:
                                invoice_partners = self.env['res.partner'].search(
                                    [('parent_id', '=', partner.id),
                                     ('is_company', '=', False)]) + partner
                                inv_lines = self.env['account.invoice.line'].search(
                                [('invoice_id.date_invoice', '>=', interval_start),
                                 ('invoice_id.date_invoice', '<=', interval_stop),
                                 ('invoice_id.partner_id', 'in', invoice_partners._ids),
                                 ('invoice_id.state', 'in', ('open', 'paid')),
                                 ('invoice_id.type', '=', 'out_invoice'),
                                 ('product_id.product_tmpl_id', 'in',
                                  rappel.get_products()),
                                 ('tourism', '=', False),
                                 ('promotion_line', '=', False)
                                 ])
                                partner_calc[partner.id] = inv_lines
                        for partner_id in partner_calc.keys():
                            inv_lines = partner_calc[partner_id]
                            to_invoice = 0.0
                            # Se calcula la cantidad a facturar del rappel
                            # para el cliente en el periodo.
                            if rappel.calc_mode == 'fixed':
                                if rappel.calc_amount == 'qty':
                                    to_invoice = rappel.fix_qty
                                else:
                                    total_consumed = sum([x.price_subtotal
                                                          for x in inv_lines])
                                    to_invoice = total_consumed * \
                                        (rappel.fix_qty / 100)
                            else:
                                if rappel.calc_type == 'monetary':
                                    total_consumed = sum([x.price_subtotal
                                                          for x in inv_lines])
                                else:
                                    total_consumed = 0.0
                                    for line in inv_lines:
                                        total_consumed += self._compute_qty_obj(
                                            line.uos_id.id, line,
                                            rappel.uom_id.id)
                                used_section = self.env['rappel.section']
                                for section in rappel.sections:
                                    if section.rappel_until >= \
                                            section.rappel_until and \
                                            section.rappel_from <= \
                                            total_consumed:
                                        used_section = section
                                if not used_section:
                                    continue
                                if rappel.calc_amount == 'qty':
                                    to_invoice = used_section.percent
                                else:
                                    to_invoice = sum([x.price_subtotal
                                                      for x in inv_lines]) * \
                                                    (used_section.percent /
                                                     100)
                            calculations = self.env['rappel.calculated'].search(
                                [('customer_id', '=', customer.id),
                                 ('rappel_id', '=', rappel.id),
                                 ('period_start', '=', period[0].date()),
                                 ('period_end', '=', period[1].date())])
                            if calculations.invoiced:
                                continue
                            calculations.unlink()
                            if to_invoice > 0:
                                self.env['rappel.calculated'].create({
                                    'customer_id': customer.id,
                                    'rappel_id': rappel.id,
                                    'period_start': period[0].date(),
                                    'period_end': period[1].date(),
                                    'quantity': to_invoice,
                                    'total_consumed':
                                    sum([x.price_subtotal for x in inv_lines]),
                                })
        return {'type': 'ir.actions.act_window_close'}
