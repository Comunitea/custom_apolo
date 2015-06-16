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
    promotion_id = fields.Many2one('promos.rules', 'Pomotion')
    discount_assumed = fields.Float('Discount assumed', required=True)
    start_date = fields.Date('Start date', required=True)
    end_date = fields.Date('End date', required=True)
    invoiced_amounts = fields.One2many('sale.joint.promotion.history',
                                       'joint_id', 'Invoiced amounts')

    @api.multi
    def _get_invoice(self, amount):
        user = self.env.user
        journal = self.env['account.journal'].search([('type', '=', 'sale'),
                                                      ('company_id', '=',
                                                       user.company_id.id)],
                                                     limit=1)
        account_id = self.supplier_id.property_account_receivable.id
        invoice = self.env['account.invoice'].create({
            'partner_id': self.supplier_id.id,
            'type': 'out_invoice',
            'journal_id': journal and journal.id or False,
            'account_id': account_id,
            'state': 'draft',
            'number': False,
            'fiscal_position': self.supplier_id.property_account_position.id
        })
        for product_id in amount.keys():
            invoice_line_vals = {
                'name': u'Joint discount',
                'invoice_id': invoice.id,
                'account_id': account_id,
                'price_unit': amount[product_id],
                'quantity': 1,
            }
            if product_id:
                product = self.env['product.product'].browse(product_id)
                invoice_line_vals['product_id'] = product_id
                invoice_line_vals['invoice_line_tax_id'] = [(4, x.id) for x in
                                                            product.taxes_id],
            self.env['account.invoice.line'].create(invoice_line_vals)

        return invoice

    @api.multi
    def _get_total_discount(self, lines):
        total = 0.0
        for line in lines:
            total += (line.price_unit * line.quantity) * \
                (line.discount / 100) * (self.discount_assumed / 100)
        return total

    @api.multi
    def get_discount_amount(self, date_start, date_end):
        partners = self.env['res.partner'].search(
            [('id', 'child_of', self.promotion_id.customer_ids._ids),
             ('is_company',  '=', True)])
        amount_to_invoice = {}
        for partner in partners:
            invoice_partner = self.env['res.partner'].search(
                [('parent_id', '=', partner.id),
                 ('is_company',  '=', False)]) + partner
            products = self.env['product.template'].search(
                [('supplier_id', '=', self.supplier_id.id)])
            for product in products:
                lines = self.env['account.invoice.line'].search(
                    [('product_id.product_tmpl_id', '=', product.id),
                     ('invoice_id.state', 'in', ('open', 'paid')),
                     ('invoice_id.date_invoice', '>=', date_start),
                     ('invoice_id.date_invoice', '<=', date_end),
                     ('invoice_id.partner_id', 'in', invoice_partner._ids)])
                amount_to_invoice[product.id] = self._get_total_discount(
                    lines)
                if not amount_to_invoice[product.id]:
                    amount_to_invoice.pop(product.id, False)
        lines = self.env['account.invoice.line'].search(
                        [('invoice_id.state', 'in', ('open', 'paid')),
                         ('invoice_id.date_invoice', '>=', date_start),
                         ('invoice_id.date_invoice', '<=', date_end),
                         ('invoice_id.partner_id', 'in', invoice_partner._ids),
                         ('promotion_line', '=', True)])
        if lines:
            amount_to_invoice[False] = sum([abs(x.price_subtotal)
                                            for x in lines]) * \
                (self.discount_assumed / 100)
        return amount_to_invoice

    @api.multi
    def get_amount(self, date_start, date_end):
        '''Funcion para facilitar el heredar para otro tipo de descuentos,
           No se utiliza campo type porque un campo selection con 1 unica
           opcion falla.
        '''
        if self.promotion_id:
            return self.get_discount_amount(date_start, date_end)
        else:
            return None

    @api.multi
    def create_invoice(self, date_start, date_end):
        invoices = self.env['account.invoice']
        amount_to_invoice = self.get_amount(date_start, date_end)

        if amount_to_invoice:
            invoice = self._get_invoice(amount_to_invoice)
            self.env['sale.joint.promotion.history'].create({
                'date_start': date_start,
                'date_end': date_end,
                'amount': sum(amount_to_invoice.values()),
                'joint_id': self.id})
            invoices += invoice
        return invoices
