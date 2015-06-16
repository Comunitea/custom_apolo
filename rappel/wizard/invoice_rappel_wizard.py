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


from openerp import models, fields, api, exceptions, _
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta

intervals = {
    'monthly': 1,
    'annual': 1,
    'quarterly': 3,
    'semiannual': 6,
}


class invoice_rappel(models.TransientModel):

    _name = "rappel.invoice.wizard"

    @api.model
    def _get_rappels(self):
        context = self.env.context
        if not context or not context['active_ids']:
            return []
        return context['active_ids']

    rappel_calculated_ids = fields.Many2many('rappel.calculated',
                                             'wizard_invoice_rappel_rel',
                                             'rappel_id', 'wizard_id',
                                             'Rappels', default=_get_rappels)
    invoice_to_group = fields.Boolean('Invoice to group', help="Create the \
invoice for the group of sub-partners")

    @api.multi
    def invoice(self):
        invoices = self.env['account.invoice']
        for calculated in self.rappel_calculated_ids:
            partner_qty = {}
            if calculated.rappel_id.invoice_grouped:
                partner_qty[calculated.customer_id.id] = calculated.quantity
            else:
                sub_partners = self.env['res.partner'].search(
                    [('id', 'child_of', calculated.customer_id.id),
                     ('is_company', '=', True)])
                for partner in sub_partners:
                    inv_parnter = self.env['res.partner'].search(
                        [('parent_id', '=', partner.id),
                         ('is_company', '=', False)]) + partner
                    inv_lines = self.env['account.invoice.line'].search(
                        [('invoice_id.date_invoice', '>=',
                          calculated.period_start),
                         ('invoice_id.date_invoice', '<=',
                          calculated.period_end),
                         ('invoice_id.partner_id', 'in', inv_parnter._ids),
                         ('invoice_id.state', 'in', ('open', 'paid')),
                         ('invoice_id.type', '=', 'out_invoice'),
                         ('product_id.product_tmpl_id', 'in',
                          calculated.rappel_id.get_products()),
                         ('tourism', '=', False),
                         ('promotion_line', '=', False)
                         ])
                    partner_consumed = sum([x.price_subtotal
                                            for x in inv_lines])
                    partner_qty[partner.id] = partner_consumed / \
                        calculated.total_consumed * calculated.quantity
                total = sum([x for x in partner_qty.values()])
                if total != calculated.quantity:
                    raise exceptions.Warning(_('Invoice error'),
                                             _('The deal quantity is greater \
than the total quantity'))
            for partner_id in partner_qty.keys():
                if partner_qty[partner_id] == 0:
                    continue
                partner = self.env['res.partner'].browse(partner_id)
                journal = self.env['account.journal'].search(
                    [('type', '=', 'purchase'),
                     ('company_id', '=', self.env.user.company_id.id)],
                    limit=1)
                invoice_vals = {
                    'partner_id': partner_id,
                    'journal_id': journal and journal.id or False,
                    'account_id': partner.property_account_receivable.id,
                    'type': 'in_invoice',
                    'state': 'draft',
                    'number': False,
                    'fiscal_position': partner.property_account_position.id
                }
                invoice = self.env['account.invoice'].create(invoice_vals)
                invoices += invoice
                if not calculated.rappel_id.type_id.product_id:
                    raise exceptions.Warning(_('Configure error'),
                                             _('The type %s dont have \
an product configured') % rappel.rappel_id.type_id.name)
                rappel_obj = calculated.rappel_id.type_id.product_id
                tax_ids = [(4, x.id) for x in rappel_obj.supplier_taxes_id]

                account_id = rappel_obj.property_account_expense.id
                if not account_id:
                    raise exceptions.Warning(_('Account not found'),
                                             _("The rappel \
product not have an account configured."))
                line_vals = {
                    'product_id': rappel_obj.id,
                    'name': u'Rappel ' + calculated.rappel_id.name,
                    'invoice_id': invoice.id,
                    'account_id': account_id,
                    'invoice_line_tax_id': tax_ids,
                    'price_unit': partner_qty[partner_id],
                    'quantity': 1
                }
                self.env['account.invoice.line'].create(line_vals)
                calculated.invoiced = True
                calculated.invoice_ids = [(4, invoice.id)]
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if invoices:
            invoices.button_reset_taxes()
            action['domain'] = "[('id','in', \
                                 [" + ','.join(map(str, invoices._ids)) + "])]"
        return action
