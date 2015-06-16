# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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


class StockMove(models.Model):
    '''Se añade 1 campo pack para crear inventarios correctamente'''

    _inherit = 'stock.move'

    pack_id = fields.Many2one('stock.quant.package', 'Package')


class StockInventoryLine(models.Model):

    _inherit = 'stock.inventory.line'

    @api.model
    def _resolve_inventory_line(self, inventory_line):
        move_id = super(StockInventoryLine, self)._resolve_inventory_line(
            inventory_line)
        move = self.env['stock.move'].browse(move_id)
        move.write({'pack_id': inventory_line.package_id.id})
        return move


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.model
    def quants_move(self, quants, move, location_to, location_from=False,
                    lot_id=False, owner_id=False, src_package_id=False,
                    dest_package_id=False):
        if not dest_package_id:
            dest_package_id = move.pack_id.id
        return super(StockQuant, self).quants_move(quants, move, location_to,
                                                   location_from, lot_id,
                                                   owner_id, src_package_id,
                                                   dest_package_id)
