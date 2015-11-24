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


class ItemManagementRecount(models.Model):

    _name = "item.management.recount"
    _inherit = ['mail.thread']

    name = fields.Char("Name", required=True)
    start_date = fields.Date("Start date", required=True, readonly=True,
                             states={'open': [('readonly', False)]})
    end_date = fields.Date("End date", required=True, readonly=True,
                           states={'open': [('readonly', False)]})
    phase_ids = fields.One2many('item.management.recount.phase', 'recount_id',
                                'Phases', readonly=True,
                                states={'open': [('readonly', False)]})
    state = fields.Selection([("open", "Open"), ("done", "Done")], 'State',
                             default="open", readonly=True,
                             track_visibility='onchange')

    @api.one
    def action_done(self):
        self.state = "done"

    @api.one
    def action_reopen(self):
        self.state = "open"

    @api.multi
    def unlink(self):
        count_obj = self.env["item.management.item.count"]
        for recount in self:
            count_ids = count_obj.search([('recount_id', '=', recount.id)])
            if count_ids:
                raise exceptions.Warning(_("Cannot delete this recount "
                                           "because has counts associated"))
        return super(ItemManagementRecount, self).unlink()


class ItemManagementRecountPhase(models.Model):

    _name = "item.management.recount.phase"

    @api.one
    def _get_counts(self):
        item_obj = self.env["item.management.item"]
        item_ids = item_obj.search([("situation", "!=", "inactive"),
                                    ("purchase_date", '<=',
                                     self.recount_id.end_date)])
        self.total_items = len(item_ids)
        item_ids = [x.id for x in item_ids]
        item_count_obj = self.env["item.management.item.count"]
        recount_ids = item_count_obj.search([('item_id', 'in', item_ids),
                                             ('recount_id', '=',
                                              self.recount_id.id),
                                             ('recount_date', '<=',
                                              self.limit_date)])
        if item_ids:
            self.percent_count = (len(recount_ids) * 100.0) / len(item_ids)
        else:
            self.percent_count = 0

    name = fields.Char("Name")
    limit_date = fields.Date("Limit date")
    description = fields.Text("Description")
    percent_goal = fields.Float("Percent goal")
    total_items = fields.Integer("Items #", compute='_get_counts',
                                 readonly=True)
    recount_id = fields.Many2one("item.management.recount", "Recount")
    percent_count = fields.Float("Percent count", compute='_get_counts',
                                 readonly=True)


class ItemManagementItemCount(models.Model):

    _name = "item.management.item.count"
    _rec_name = "recount_date"
    _order = "recount_date desc"

    item_id = fields.Many2one("item.management.item", "Item", required=True)
    recount_id = fields.Many2one('item.management.recount', 'Recount',
                                 required=True, domain=[('state', '=',
                                                         "open")])
    notes = fields.Text("Notes")
    recount_date = fields.Datetime("Review date", required=True,
                                   default=fields.Datetime.now())
    user_id = fields.Many2one("res.users", "User", required=True,
                              default=lambda self: self.env.user)
