# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _


class TourismGroup(models.Model):

    _name = 'tourism.group'

    customer_ids = fields.Many2many('res.partner', 'tourism_partner_rel',
                                    'tourism_id', 'partner_id', 'Customers')
    line_ids = fields.One2many('tourism.line', 'tourism_id', 'Products')
    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    state = fields.Selection((('new', 'New'), ('validated', 'Validated'),
                             ('approved', 'Approved')), 'State', default='new')

    @api.one
    def create_invoice(self, date_start, date_end):
        start = date_start > self.date_start and date_start or self.date_start
        end = date_end < self.date_end and date_end or self.date_end
        lines = self.env['account.invoice.line'].search(
            [('product_id.product_tmpl_id', '=', self.product.id),
             ('invoice_id.state', 'in', ('open', 'paid')),
             ('invoice_id.date_invoice', '>=', start),
             ('invoice_id.date_invoice', '<=', end)])
        total_guaranteed = 0.0
        for line in lines:
            if line.uos_id.like_type == 'boxes':
                unit_price = line.price_unit / line.product_id.un_ca
            else:
                unit_price = line.price_unit
            total_guaranteed += line.price_unit < self.guar_price and  \
                self.guar_price - line.price_unit or self.guar_price
        if total_guaranteed:
            user = self.env.user
            journal = self.env['account.journal'].search([('type', '=',
                                                           'sale'),
                                                          ('company_id', '=',
                                                           user.company_id.id)
                                                          ],
                                                         limit=1)
            account_id = self.supplier_id.property_account_receivable.id
            invoice = self.env['account.invoice'].create({
                'partner_id': self.supplier_id.id,
                'type': 'out_invoice',
                'journal_id': journal and journal.id or False,
                'account_id': account_id,
                'state': 'draft',
                'number': False,
                'fiscal_position':
                self.supplier_id.property_account_position.id
            })
            self.env['account.invoice.line'].create({
                'product_id': self.product.id,
                'name': _('Tourism'),
                'invoice_id': invoice.id,
                'account_id': account_id,
                'price_unit': total_guaranteed,
                'invoice_line_tax_id': [(4, x.id) for x in
                                        self.product.taxes_id],
                'quantity': 1,
            })
        return True


class TourismLine(models.Model):

    _name = 'tourism.line'

    product = fields.Many2one('product.template', 'Product')
    supplier_id = fields.Many2one('res.partner', 'Supplier',
                                  compute='_get_supplier_id', store=True)
    min_price = fields.Float('Minimum price')
    guar_price = fields.Float('Guaranteed price')
    tourism_id = fields.Many2one('tourism.group', 'Group')

    @api.depends('product.seller_ids')
    def _get_supplier_id(self):
        if self.product.seller_ids:
            self.supplier_id = self.product.seller_ids[0].name
        else:
            self.supplier_id = False
