# -*- coding: utf-8 -*-
##############################################################################
#
#    Omar Castiñeira Saavedra Copyright Comunitea SL 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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


class ItemManagementContract(models.Model):

    _name = "item.management.contract"
    _inherit = ['mail.thread']

    name = fields.Char("Code",  required=True, default="/", readonly=True)
    description = fields.Text("Description", required=True, readonly=True,
                              states={'draft': [('readonly', False)]})
    start_date = fields.Date("Start date", readonly=True,
                             states={'draft': [('readonly', False)]})
    end_date = fields.Date("End date", readonly=True,
                           states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'),
                              ('done', 'Finished'), ('cancel', 'Cancelled')],
                             'State', required=True, default="draft",
                             readonly=True, track_visibility='onchange')
    partner_id = fields.Many2one("res.partner", "Customer", required=True,
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    contract_type = fields.Selection([('customer', 'Customer'),
                                      ('transfer', 'Transfer')],
                                     "Contract type", default="customer",
                                     readonly=True, required=True,
                                     states={'draft': [('readonly', False)]})
    item_ids = fields.One2many("item.management.item", "contract_id", "Items",
                               readonly=True)
    owner_agent = fields.Char("Owner agent")
    owner_agent2 = fields.Char("Owner agent 2")
    company_agent = fields.Char("Company agent")
    customer_agent = fields.Char("Customer agent")
    customer_agent_vat = fields.Char("Customer agent vat")
    item_value = fields.Float("Item value")
    customer_local_name = fields.Char("Customer local name")
    customer_local_street = fields.Char("Customer local street")

    @api.one
    def action_active(self):
        self.state = "active"

    @api.one
    def action_done(self):
        self.state = "done"
        if not self.end_date:
            self.end_date = fields.Date.today()
        self.action_remove_items()

    @api.one
    def action_cancel(self):
        if self.item_ids:
            raise exceptions.Warning(_("Cannot cancel a contract with related "
                                       "items."))
        self.state = "cancel"

    @api.one
    def action_set_to_draft(self):
        self.state = "draft"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].\
            get('item.management.contract') or '/'

        new_id = super(ItemManagementContract, self).create(vals)
        return new_id

    @api.one
    def action_remove_items(self):
        for item in self.item_ids:
            item.contract_id = False
            item.customer_id = False
            item.situation = "warehouse"

    @api.multi
    def unlink(self):
        for contract in self:
            if self.state not in ["draft", "cancel"]:
                raise exceptions.Warning(_("Only can delete contracts in draft"
                                           " or cancel state"))
        return super(ItemManagementContract, self).unlink()
