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
        if self.invoice_to_group:
            partners = self.env['res.partner']
            for calculated in self.rappel_calculated_ids:
                if calculated.customer_id.parent_id and \
                        calculated.customer_id.parent_id not in partners:
                    partners += calculated.customer_id.parent_id
                elif not calculated.customer_id.parent_id and \
                        calculated.customer_id not in partners:
                    partners += calculated.customer_id
            operator = 'child_of'
        else:
            partners = self.env['res.partner'].search(
                [('id', 'in', [x.customer_id.id for x in
                               self.rappel_calculated_ids])])
            operator = '='

        rappels = self.env['rappel.calculated']
        for rappel in self.rappel_calculated_ids:
            if not rappel.invoiced:
                rappels += rappel
        for partner in partners:
            partner_calculated = self.env['rappel.calculated'].search(
                [('id', 'in', self.rappel_calculated_ids._ids),
                 ('customer_id', operator, partner.id), ('invoiced', '=',
                                                         False)])
            if not partner_calculated:
                continue
            journal = self.env['account.journal'].search(
                [('type', '=', 'purchase'),
                 ('company_id', '=', self.env.user.company_id.id)], limit=1)

            invoice_vals = {
                'partner_id': partner.id,
                'journal_id': journal and journal.id or False,
                'account_id': partner.property_account_receivable.id,
                'type': 'in_invoice',
                'state': 'draft',
                'number': False,
                'fiscal_position': partner.property_account_position.id
            }
            invoice = self.env['account.invoice'].create(invoice_vals)
            for rappel in partner_calculated:
                if not rappel.rappel_id.type_id.product_id:
                    raise exceptions.Warning(_('Configure error'),
                                             _('The type %s dont have \
an product configured')
                                             % rappel.rappel_id.type_id.name)
                rappel_obj = rappel.rappel_id.type_id.product_id
                tax_ids = [(4, x.id) for x in rappel_obj.supplier_taxes_id]

                account_id = rappel_obj.property_account_expense.id
                if not account_id:
                    raise exceptions.Warning(_('Account not found'),
                                             _("The rappel \
product not have an account configured."))
                line_vals = {
                    'product_id': rappel_obj.id,
                    'name': u'Rappel ' +
                            rappel.rappel_id
                            .name,
                    'invoice_id': invoice.id,
                    'account_id': account_id,
                    'invoice_line_tax_id': tax_ids,
                    'price_unit': rappel.quantity,
                    'quantity': 1
                }
                if self.invoice_to_group:
                    line_vals['name'] = rappel.customer_id.name
                self.env['account.invoice.line'].create(line_vals)
                rappel.invoiced = True
                rappel.invoice_id = invoice
                invoices += invoice
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if invoices:
            invoices.button_reset_taxes()
            action['domain'] = "[('id','in', \
                                 [" + ','.join(map(str, invoices._ids)) + "])]"
        return action
