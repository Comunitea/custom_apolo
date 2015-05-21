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

MOTIVES = {'scrapping': _('Scrapping'),
           'theft': _('Theft'),
           'loss': _('Loss')}


class ItemManagementItemDeactivate(models.TransientModel):

    _name = "item.management.item.deactivate"

    inactive_motive = fields.Selection([('scrapping', 'Scrapping'),
                                        ('theft', 'Theft'),
                                        ('loss', 'Loss')], 'Inactive motive',
                                       required=True)

    @api.one
    def action_deactive(self):
        active_ids = self._context["active_ids"]
        item_obj = self.env["item.management.item"]
        for item in item_obj.browse(active_ids):
            item.situation = "inactive"
            item.inactive_motive = self.inactive_motive
            item.location_id = False
            item.message_post(body=_('Item was marked to inactive in %s '
                                     'with motive %s') %
                                    (fields.Date.today(),
                                     MOTIVES[self.inactive_motive]))

    @api.model
    def default_get(self, fields_list):
        active_ids = self._context["active_ids"]
        item_obj = self.env["item.management.item"]
        for item in item_obj.browse(active_ids):
            if item.contract_id:
                raise exceptions.Warning(_("Item %s is related to contract %s,"
                                           " please recover it to warehouse.")
                                         % (item.name, item.contract_id.name))
            elif item.situation == "inactive":
                raise exceptions.Warning(_("Item %s already is inactive.")
                                         % item.name)
        return super(ItemManagementItemDeactivate, self).\
            default_get(fields_list)
