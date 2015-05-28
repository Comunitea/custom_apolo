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
from openerp import models, fields, api


class sale_joint_promotion_history(models.Model):

    _name = 'sale.joint.promotion.history'

    date_start = fields.Date('Start')
    date_end = fields.Date('End')
    amount = fields.Float('Amount')
    joint_id = fields.Many2one('sale.joint.promotion', 'Joint promotion')


class sale_joint_promotion(models.Model):

    _name = 'sale.joint.promotion'

    supplier_id = fields.Many2one('res.partner', 'Supplier', required=True)
    category_id = fields.Many2one('product.category', 'Category',
                                  required=True)
    discount = fields.Float('Discount', required=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    discount_assumed = fields.Float('Discount assumed', required=True)
    active = fields.Boolean('Active', default=True)
    invoiced_amounts = fields.One2many('sale.joint.promotion.history',
                                       'joint_id', 'Invoiced amounts')

    @api.one
    def deactivate(self):
        self.active = False

    @api.one
    def activate(self):
        self.active = True

    @api.multi
    def _get_invoice(self, amount):
        user = self.env.user
        journal = self.env['account.journal'].search([('type', '=',
                                                       'purchase_refund'),
                                                      ('company_id', '=',
                                                       user.company_id.id)],
                                                     limit=1)
        account_id = self.supplier_id.property_account_payable.id
        invoice = self.env['account.invoice'].create({
            'partner_id': self.supplier_id.id,
            'type': 'in_refund',
            'journal_id': journal and journal.id or False,
            'account_id': account_id,
            'state': 'draft',
            'number': False,
            'fiscal_position': self.supplier_id.property_account_position.id
        })
        for product_id in amount.keys():
            product = self.env['product.product'].browse(product_id)
            self.env['account.invoice.line'].create({
                'product_id': product_id,
                'name': u'Joint discount',
                'invoice_id': invoice.id,
                'account_id': account_id,
                'price_unit': amount[product_id],
                'invoice_line_tax_id': [(4, x.id) for x in
                                        product.supplier_taxes_id],
                'quantity': 1,
            })
        return invoice

    @api.multi
    def _get_total_discount(self, lines):
        total = 0.0
        for line in lines:
            total += (line.price_unit * line.quantity) * \
                (line.discount / 100) * (self.discount_assumed / 100)
        return total

    @api.multi
    def create_invoice(self, date_start, date_end):
        products = self.env['product.template'].search([('categ_id', '=',
                                                        self.category_id.id)])
        amount_to_invoice = {}
        for product in products:
            if product.seller_ids and \
                    product.seller_ids[0].name == self.supplier_id:
                lines = self.env['account.invoice.line'].search(
                    [('product_id.product_tmpl_id', '=', product.id),
                     ('invoice_id.state', 'in', ('open', 'paid')),
                     ('invoice_id.date_invoice', '>=', date_start),
                     ('invoice_id.date_invoice', '<=', date_end),
                     ('discount', '>=', self.discount)])
                amount_to_invoice[product.id] = self._get_total_discount(lines)
                if not amount_to_invoice[product.id]:
                    amount_to_invoice.pop(product.id, False)
        if amount_to_invoice:
            invoice = self._get_invoice(amount_to_invoice)
            self.env['sale.joint.promotion.history'].create({
                'date_start': date_start,
                'date_end': date_end,
                'amount': sum(amount_to_invoice.values()),
                'joint_id': self.id})
            return invoice
        return False
