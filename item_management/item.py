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


class ItemManagementItem(models.Model):

    _name = "item.management.item"
    _inherit = ['mail.thread']

    name = fields.Char("Item name", required=True)
    type_id = fields.Many2one('item.management.item.type', 'Type',
                              required=True)
    code = fields.Char("Code")
    license_plate = fields.Char("License plate", track_visibility='onchange',
                                size=13, required=True)
    partner_id = fields.Many2one("res.partner", "Owner", required=True)
    purchase_date = fields.Date("Purchase date")
    contract_id = fields.Many2one('item.management.contract', 'Contract',
                                  readonly=True, track_visibility='onchange')
    location_id = fields.Many2one('stock.location', 'Location', readonly=True,
                                  track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', "Customer", readonly=True,
                                  track_visibility='onchange')
    location_date = fields.Datetime('Placement date')
    count_ids = fields.One2many("item.management.item.count", "item_id",
                                "Recounts")
    asset_id = fields.Many2one("account.asset.asset", "Asset")
    capacity = fields.Float('Capacity (l)')
    situation = fields.Selection([('transfer', 'Transfer'),
                                  ('customer', 'Customer'),
                                  ('warehouse', "Warehouse"),
                                  ('inactive', 'Inactive')], 'Situation',
                                 required=True, default="warehouse",
                                 readonly=True, track_visibility='onchange')
    inactive_motive = fields.Selection([('scrapping', 'Scrapping'),
                                        ('theft', 'Theft'),
                                        ('loss', 'Loss')], 'Inactive motive',
                                       readonly=True)
    license_history_ids = fields.\
        One2many("item.management.item.license.plate.history", "item_id",
                 "History", readonly=True)

    @api.multi
    def unlink(self):
        for item in self:
            if self.contract_id:
                raise exceptions.Warning(_("Cannot delete this item because is"
                                           " related to a contract"))
            if self.count_ids:
                raise exceptions.Warning(_("Cannot delete this item because "
                                           "has already been recounted"))
        return super(ItemManagementItem, self).unlink()

    @api.multi
    def write(self, vals):
        if vals.get("license_plate"):
            lp_history_obj = \
                self.env["item.management.item.license.plate.history"]
            for item in self:
                if item.license_plate != vals["license_plate"]:
                    lp_history_obj.create({'item_id': item.id,
                                           'old_license_plate':
                                           item.license_plate})
        return super(ItemManagementItem, self).write(vals)


class ItemManagementItemLicensePlateHistory(models.Model):

    _name = "item.management.item.license.plate.history"
    _order = "date desc, id desc"

    date = fields.Date("Change date", default=fields.Date.today(),
                       required=True, readonly=True)
    item_id = fields.Many2one('item.management.item', 'Item', required=True,
                              readonly=True)
    old_license_plate = fields.Char("License plate", size=13, required=True,
                                    readonly=True)
