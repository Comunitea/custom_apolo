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

from openerp import models, api, exceptions, _, fields


class ItemManagementItem(models.Model):

    _inherit = "item.management.item"

    @api.one
    def _get_last_move(self):
        move_obj = self.env["item.management.item.move.sync"]
        move_ids = move_obj.search([('item_id', '=', self.id)], limit=1)
        self.last_move_id = move_ids and move_ids[0] or False

    to_sync = fields.Boolean("To sync", default=True,
                             help="Check it to sync moves with Frigo")
    last_move_id = fields.Many2one('item.management.item.move.sync',
                                   'Last move', compute='_get_last_move',
                                   readonly=True)

    @api.multi
    def write(self, vals):
        if "to_sync" in vals:
            for item in self:
                sync_obj = self.env["item.management.item.move.sync"]
                if not vals["to_sync"]:
                    sync_ids = sync_obj.search([('item_id', '=', item.id)],
                                               limit=1)
                    sync = sync_ids[0]
                    if sync.state == "pending" and \
                            sync.operation_type == "A":
                        sync.unlink()
                    else:
                        raise exceptions.Warning(_("Cannot desynchronize "
                                                   "this item %s because "
                                                   "it is synced with "
                                                   "Frigo yet")
                                                 % item.name)
                else:
                    sync_ids = sync_obj.search([('item_id', '=', item.id)])
                    if not sync_ids:
                        sync_obj.create({'item_id': item.id,
                                         'operation_type': 'A'})
        return super(ItemManagementItem, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(ItemManagementItem, self).create(vals)
        if vals.get('to_sync', False):
            sync_obj = self.env["item.management.item.move.sync"]
            sync_obj.create({'item_id': res.id,
                             'operation_type': 'A'})
        return res

    @api.one
    def unlink(self):
        sync_obj = self.env["item.management.item.move.sync"]
        sync_ids = sync_obj.search([('item_id', '=', self.id)],
                                   limit=1)
        if sync_ids:
            sync = sync_ids[0]
            if sync.state == "pending" and sync.operation_type == "A":
                sync.unlink()
            else:
                raise exceptions.Warning(_("Cannot delete this item %s "
                                           "because it is synced with "
                                           "Frigo") % self.name)
        return super(ItemManagementItem, self).unlink()


class ItemManagementItemAssignContract(models.TransientModel):

    _inherit = "item.management.item.assign.contract"

    @api.one
    def assign_item_to_contract(self):
        super(ItemManagementItemAssignContract, self).assign_item_to_contract()
        self.item_id.refresh()
        sync_obj = self.env["item.management.item.move.sync"]
        sync_obj.create({'item_id': self.item_id.id,
                         'operation_type': self.contract_type == "transfer" and
                         'X' or 'C',
                         'customer_id': self.item_id.customer_id.id,
                         'contract_id': self.item_id.contract_id.id})


class ItemManagementItemDeactivate(models.TransientModel):

    _inherit = "item.management.item.deactivate"

    @api.one
    def action_deactive(self):
        super(ItemManagementItemDeactivate, self).action_deactive()
        active_ids = self._context["active_ids"]
        item_obj = self.env["item.management.item"]
        sync_obj = self.env["item.management.item.move.sync"]
        for item in item_obj.browse(active_ids):
            if item.inactive_motive == "scrapping":
                inactive = "D"
            elif item.inactive_motive == "theft":
                inactive = "R"
            else:
                inactive = "P"
            sync_obj.create({'item_id': item.id,
                             'operation_type': 'B',
                             'inactive_motive': inactive})


class ItemManagementContract(models.Model):

    _inherit = "item.management.contract"

    @api.one
    def action_remove_items(self):
        sync_obj = self.env["item.management.item.move.sync"]
        for item in self.item_ids:
            sync_ids = sync_obj.search([('item_id', '=', item.id)],
                                       limit=1)
            sync = sync_ids[0]
            if sync.state == "pending" and sync.operation_type in ["X", "C"]:
                sync.unlink()
            else:
                sync_obj.create({'item_id': item.id,
                                 'operation_type': 'E'})
        super(ItemManagementContract, self).action_remove_items()
