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


class ItemManagementItemMoveSync(models.Model):

    _name = "item.management.item.move.sync"
    _order = "date desc"

    state = fields.Selection([('pending', 'Pending'),
                              ('sync', 'Synchronized')], "State",
                             readonly=True, default="pending")
    item_id = fields.Many2one("item.management.item", "Item", required=True)
    operation_type = fields.Selection([('C', 'Customer lent'),
                                       ('E', 'Customer removed'),
                                       ('A', 'New'), ('B', 'Inactive'),
                                       ('X', 'Concession change'),
                                       ('R', 'Recovered')], 'Operation type',
                                      readonly=True, default="A",
                                      required=True)
    customer_id = fields.Many2one("res.partner", "Customer", readonly=True)
    inactive_motive = fields.Selection([('D', 'Scrapping'),
                                        ('R', 'Theft'),
                                        ('P', 'Loss')], 'Inactive motive',
                                       readonly=True)
    user_id = fields.Many2one("res.users", "User", readonly=True,
                              required=True,
                              default=lambda self: self.env.user)
    date = fields.Date("Date", default=fields.Date.today(), required=True)
    contract_id = fields.Many2one("item.management.contract", "Contract",
                                  readonly=True)
