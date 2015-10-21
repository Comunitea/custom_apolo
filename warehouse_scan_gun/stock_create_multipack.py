# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Javier Colmenero Fernández$ <javier@pexego.es>
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
from openerp import models, fields

from openerp import models, fields, api, exceptions, _
#
#
# class StockCreateMultiPack(models.TransientModel):
#
#     _name = 'stock.picking.create.multipack.line'
#     wizard_id = fields.Many2one('stock.picking.create.multipack', 'Wizard')
#     operation_id = fields.Many2one('stock.pack.operation', 'Operation')
#     product_id = fields.Many2one('product.product', 'Product')
#     lot_id = fields.Many2one('stock.production.lot', 'Lot')
#     pack_id = fields.Many2one('stock.quant.package', 'Source package')
#     qty = fields.Float('Quantity')
#     pack_dest_id = fields.Many2one('stock.quant.package', 'Dest package')
#

class StockCreateMultiPack(models.TransientModel):

    _inherit = 'stock.picking.create.multipack'



    @api.multi
    def create_multipack_from_gun(self, my_args):

        user_id = my_args.get('user_id', False)
        package_ids = my_args.get ('package_id', [])
        package_pool = self.env['stock.quant.package']
        multipack = self.env['stock.picking.create.multipack'].create({'line_ids' : []})

        new_package = multipack.id

        for package_id in package_ids:
            domain = [('id','=', package_id)]
            package = package_pool.search(domain)
            vals = {
                'product_id' : package.product_id.id or False,
                'lot_id': package.packed_lot_id.id or False,
                'pack_id': package.id,
                'qty': package.packed_qty or 0.00,
                #'pack_dest_id': new_package
            }
            wzd_obj = multipack.create({'line_ids': vals})
            res = wzd_obj.write({'line_ids': [(0,0, vals)]})

        res = multipack.create_multipack()#.do_manual_transfer()

        return res

    #
    #
    # @api.multi
    # def create_multipack(self):
    #     for line in self.line_ids:
    #         if line.pack_dest_id:
    #             line.pack_id.write({'parent_id': line.pack_dest_id.id})
    #     picking = self.env['stock.picking'].browse(
    #         self.env.context.get('active_id', False))
    #     picking.delete_picking_package_operations()
    #     picking.do_prepare_partial()
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # @api.model
    # def default_get(self, fields):
    #     res = super(StockCreateMultiPack, self).default_get(fields)
    #     res['line_ids'] = []
    #     picking = self.env['stock.picking'].browse(
    #         self.env.context.get('active_id', False))
    #     if not picking:
    #         return res
    #     if not picking.pack_operation_ids:
    #         picking.do_prepare_partial()
    #
    #     for op in picking.pack_operation_ids:
    #         line_vals = {
    #             'product_id': op.product_id.id or op.package_id.product_id.id,
    #             'operation_id': op.id,
    #             'lot_id': op.lot_id.id or op.packed_lot_id.id,
    #             'pack_id': op.package_id.id,
    #             'qty': op.packed_qty,
    #         }
    #         res['line_ids'].append(line_vals)
    #     return res