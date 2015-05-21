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

from openerp import models, fields, api


class ItemManagementItemAssignContract(models.TransientModel):

    _name = "item.management.item.assign.contract"

    item_id = fields.Many2one("item.management.item", "Item", required=True,
                              domain=[('contract_id', '=', False),
                                      ('situation', '=', 'warehouse')])
    location_date = fields.Datetime("Location date", required=True,
                                    default=fields.Datetime.now())
    contract_type = fields.Selection([('customer', 'Customer'),
                                      ('transfer', 'Transfer')],
                                      "Contract type", readonly=True)

    @api.one
    def assign_item_to_contract(self):
        contract_obj = self.env["item.management.contract"]
        contract_id = self.env.context["active_ids"][0]
        contract = contract_obj.browse(contract_id)
        self.item_id.contract_id = contract.id
        self.item_id.situation = contract.contract_type
        self.item_id.customer_id = contract.partner_id.id
        self.item_id.location_id = False
        self.item_id.location_date = self.location_date

    @api.model
    def default_get(self, fields_list):
        active_id = self._context["active_ids"][0]
        contract_obj = self.env["item.management.contract"]
        contract = contract_obj.browse(active_id)
        res = super(ItemManagementItemAssignContract, self).\
            default_get(fields_list)
        res['contract_type'] = contract['contract_type']
        return res
