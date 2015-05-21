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


class ItemManagementItemInternalMove(models.TransientModel):

    _name = "item.management.item.internal.move"

    dest_location_id = fields.Many2one("stock.location", "Dest. location",
                                       required=True)

    @api.one
    def execute_move(self):
        active_ids = self._context["active_ids"]
        item_obj = self.env["item.management.item"]
        for item in item_obj.browse(active_ids):
            item.location_id = self.dest_location_id
            item.situation = "warehouse"

    @api.model
    def default_get(self, fields_list):
        active_ids = self._context["active_ids"]
        item_obj = self.env["item.management.item"]
        for item in item_obj.browse(active_ids):
            if item.contract_id:
                raise exceptions.Warning(_("Item %s is related to contract %s,"
                                           " please move it from there.")
                                         % (item.name, item.contrcat_id.name))
            elif item.situation == "inactive":
                raise exceptions.Warning(_("Item %s is deactivated.")
                                         % item.name)
        return super(ItemManagementItemInternalMove, self).\
            default_get(fields_list)
