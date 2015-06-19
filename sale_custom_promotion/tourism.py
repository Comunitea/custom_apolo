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

    customer_ids = fields.One2many('tourism.customer', 'tourism_id',
                                   'Customers')
    product_ids = fields.Many2many('product.template', 'tourism_product_rel',
                                   'tourism_id', 'product_id', 'Products')
    date_start = fields.Date('Date start', required=True)
    date_end = fields.Date('Date end', required=True)
    invoice_ids = fields.One2many('account.invoice', 'tourism_id', 'Invoices',
                                  readonly=True)
    name = fields.Char('Code', size=6, required=True)
    description = fields.Char('Description', size=30)
    state = fields.Selection((('new', 'New'), ('validated', 'Validated'),
                             ('approved', 'Approved'), ('cancel', 'Cancel')),
                             'State', default='new')
    min_price = fields.Float('Minimum price', required=True)
    all_exported = fields.Boolean('All customer exported', readonly=True,
                                  compute='_get_exported_customer')
    guar_price = fields.Float('Guaranteed price', required=True)
    qty_estimated = fields.Float('Estimated consumption')

    @api.one
    def _get_exported_customer(self):
        all_exported = True
        for customer in self.customer_ids:
            if not customer.exported:
                all_exported = False
        self.all_exported = all_exported

    @api.one
    def create_invoice(self, date_start, date_end):
        start = date_start > self.date_start and date_start or self.date_start
        end = date_end < self.date_end and date_end or self.date_end
        # total_guaranteed = {'supplier_id': {'product_id': qty, ...}, ...}
        total_guaranteed = {}
        for customer_line in self.customer_ids:
            for product in self.product_ids:
                supplier_id = product.supplier_id.id
                product_id = product.id
                lines = self.env['account.invoice.line'].search(
                    [('invoice_id.partner_id', '=',
                      customer_line.customer_id.id),
                     ('product_id.product_tmpl_id', '=', product_id),
                     ('invoice_id.state', 'in', ('open', 'paid')),
                     ('invoice_id.date_invoice', '>=', start),
                     ('invoice_id.date_invoice', '<=', end)])
                if supplier_id not in total_guaranteed.keys():
                    total_guaranteed[supplier_id] = {product_id: 0.0}
                elif product_id not in total_guaranteed[supplier_id].keys():
                    total_guaranteed[supplier_id][product_id] = 0.0
                for line in lines:
                    if line.uos_id.like_type == 'boxes':
                        unit_price = line.price_unit / line.product_id.un_ca
                    else:
                        unit_price = line.price_unit
                    total_guaranteed[supplier_id][product_id] += unit_price < \
                        customer_line.agreed_price and \
                        customer_line.agreed_price - unit_price or 0.0
        if total_guaranteed:
            user = self.env.user
            journal = self.env['account.journal'].search([('type', '=',
                                                           'sale'),
                                                          ('company_id', '=',
                                                           user.company_id.id)
                                                          ],
                                                         limit=1)
            for supplier_id in total_guaranteed.keys():
                supplier = self.env['res.partner'].browse(supplier_id)
                account_id = supplier.property_account_receivable.id
                invoice = self.env['account.invoice'].create({
                    'partner_id': supplier_id,
                    'type': 'out_invoice',
                    'journal_id': journal and journal.id or False,
                    'account_id': account_id,
                    'state': 'draft',
                    'number': False,
                    'fiscal_position': supplier.property_account_position.id,
                    'tourism_id': self.id,
                })

                for product_id in total_guaranteed[supplier_id].keys():
                    product = self.env['product.template'].browse(product_id)
                    self.env['account.invoice.line'].create({
                        'product_id': product_id,
                        'name': _('Tourism'),
                        'invoice_id': invoice.id,
                        'account_id': account_id,
                        'price_unit':
                        total_guaranteed[supplier_id][product_id],
                        'invoice_line_tax_id': [(4, x.id) for x in
                                                product.taxes_id],
                        'quantity': 1,
                    })
        return True

    @api.multi
    def export_customers(self):
        to_export = self.env['tourism.customer']
        for customer in self.customer_ids:
            if not customer.exported:
                to_export += customer
        edi_obj = self.env["edi"]
        edis = edi_obj.search([])
        for service in edis:
            wzd = False
            for dtype in service.doc_type_ids:
                if dtype.code == "pol":
                    wzd = self.env['edi.export.wizard'].create(
                        {'service_id': service.id})
                    wzd.export_file_pol('tourism.customer', to_export)
                    break
        to_export.write({'exported': True})

    @api.multi
    def validate(self):
        self.write({'state': 'validated'})

    @api.multi
    def approve(self):
        self.write({'state': 'approved'})

    @api.multi
    def cancel(self):
        self.write({'state': 'cancel'})


class TourismCustomer(models.Model):

    _name = 'tourism.customer'

    tourism_id = fields.Many2one('tourism.group', 'Group')
    customer_id = fields.Many2one('res.partner', 'Customer')
    agreed_price = fields.Float('Agreed price')
    agreement_date = fields.Date('Agreement date')
    exported = fields.Boolean('Customer exported')
    product_group = fields.Many2one('product.rappel.group', 'Product group')
    qty_estimated = fields.Float('Estimated consumption')

    @api.multi
    @api.onchange('agreed_price')
    def onchange_agreed_price(self):
        if self.agreed_price and self.agreed_price < self.tourism_id.min_price:
            return {'warning': {'tittle': _('Price error'),
                                'message': _('The agreed price must be higher \
than the minimum price')}}
