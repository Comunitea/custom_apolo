# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez$ <kiko@comunitea.com>
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
from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
class stock_quant(models.Model):
        _inherit = 'stock.quant'

        @api.multi
        def get_quant_pack_gun_info(self, my_args):

            package_id = my_args.get("package_id", False)
            domain = [('package_id', '=', package_id)]
            quants = self.search(domain)
            res={}
            vals = {}
            for quant in quants:
                if quant:
                    vals = {
                        'exist' : True,
                        'quant' : quant.name,
                        'quant_id' :quant.id,
                        'location_id' : quant.location_id.id,
                        'location': quant.location_id.bcd_name,
                        'product_id': quant.product_id.id,
                        'product' : quant.product_id.short_name or quant.product_id.name,
                        'quantity' : quant.qty,
                        'uom': quant.product_id.uom_id.name
                    }
                res[str(quant.id)]=vals
            return res

        @api.multi
        def get_quant_pack_gun_info_resumen(self, my_args):

            package_id = my_args.get("package_id", False)
            domain = [('package_id', '=', package_id)]
            quants = self.search(domain)

            vals = {}
            indice = 0
            for quant in quants:
                indice+=1
                ind = str(quant.product_id.id)

                if ind in vals.keys() and 'qty' in vals[ind].keys():
                    qty =vals[ind]['qty'] + quant.qty
                else:
                    qty = quant.qty

                values={
                    'id':package_id,
                    'product_id':  quant.product_id.id or False,
                    'product': quant.product_id.short_name or quant.product_id.name,
                    'uom': quant.product_id.uom_id.name,
                    'qty':qty}
                vals[ind]=values
            return values

class stock_quant_package(models.Model):

    _inherit = 'stock.quant.package'


    @api.multi
    def create_package_from_gun(self, my_args):
        user_id= my_args.get("user_id", False)
        values = my_args.get('values', {})
        pack_wzd = self.env['stock.quant.package']
        env2 = pack_wzd.env(self._cr, user_id, self._context)
        wzd_obj_uid = pack_wzd.with_env(env2)
        wzd_obj = wzd_obj_uid.create(values)
        return wzd_obj.id

    # @api.multi
    # def create_package_from_gun(self, my_args):
    #
    #     user_id = my_args.get('user_id', False)
    #     pack_wzd = self.env['stock.quant.package']
    #     env2 = pack_wzd.env(self._cr, user_id, self._context)
    #     wzd_obj_uid = pack_wzd.with_env(env2)
    #     wzd_obj = wzd_obj_uid.create()
    #
    #     return wzd_obj


    @api.multi
    def create_multipack_from_gun(self, my_args):

        user_id = my_args.get('user_id', False)
        package_ids = my_args.get ('package_id', [])

        res = False
        if package_ids:
            #creo un paquete nuevo, multiproducto
            vals= {
            'is_multiproduct' : True
            }
            new_package = self.create(vals)
            parent_id = new_package.id

            #el primer paquete marca la ubicación y el piking
            #si hay un pauqte de la lista que no tiene ese picking o esa ubicación
            #lo borro de la lista
            domain = [('result_package_id', '=', package_ids[0]), ('picking_id.picking_type_id', '=',1)]
            pack = self.env['stock.pack.operation'].search(domain)
            picking_in = pack.picking_id
            group_id = picking_in.group_id.id
            domain = [('group_id','=',group_id), ('picking_type_id', '=',6)]
            picking_ubi = self.env['stock.picking'].search(domain)

            #si no tiene operaciones hago el do_prepare_partial
            if not picking_ubi.pack_operation_ids:
                picking_ubi.do_prepare_partial()

            #escribo en todas las operaciones de ubicación de la lista de paquetes
            #un result package_id del paquete creado
            domain = [('package_id', 'in', package_ids), ('picking_id', '=', picking_ubi.id)]
            ops = self.env['stock.pack.operation'].search(domain)
            ops.write({'result_package_id':parent_id})

            #creo una lista con los paquetes que si están en la lista realmente
            list_ids = []
            for op in ops:
                list_ids.append(op.package_id.id)
            #seteo todos los paquetes de la lista parent_id al paquete nuevo
            domain = [('id', 'in', list_ids)]
            packs = self.search(domain)
            packs.write({'parent_id':parent_id})

            #saco el picking del primer paquete
            # y hago
            picking_ubi.delete_picking_package_operations()
            picking_ubi.do_prepare_partial()

            res = new_package.name
        return res


    @api.multi
    def check_package_for_picking_change(self, my_args):
        # user_id = my_args.get('user_id', False)
        # product_id = my_args.get ('product_id', False)
        package_id = my_args.get ('package_id', False)
        qty_to_move = my_args.get ('qty_to_move', False)
        res = False
        package = self.env['stock.quant.package'].browse (package_id)
        if package and package.unreserved_qty >= qty_to_move:
            res = True
        return res



    @api.multi
    def get_parent_package(self, my_args):

        package_id = my_args.get('package_id', False)
        package = self.browse(package_id)
        package_id = False
        if package:
            package_id = package.parent_id.id
        return package_id


    @api.multi
    def get_package_gun_info(self, my_args):
        name = my_args.get('name', False)
        domain=[('name', 'ilike', '%' + name)]
        package = self.search(domain)
        package_id = False
        if package:
            package_id = package[0].id
        return package_id

    @api.multi
    def get_pack_gun_info(self, my_args):
        package_id = my_args.get("package_id", False)
        domain = [('id', '=', package_id)]
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}
        self_ = self.env['stock.quant.package'].with_context(ctx)
        package = self_.search(domain).with_context(ctx)
        vals = {'exist':False}
        if package:# and package.quant_ids:
            qty = 0
            # if package.quant_ids:
            #     qtys= [t.qty for t in package.quant_ids if t.product_id.id == package.packed_lot_id.product_id.id]
            #     for qty_ in qtys:
            #         qty+= qty_
            #


            picking_zone_id = False
            picking_zone = ''

            if not package.is_multiproduct:
                if package.product_id:
                    picking_zone_id = package.product_id.picking_location_id.id or False
                    picking_zone = package.product_id.picking_location_id.bcd_name or\
                               package.product_id.picking_location_id.name or False
                else:
                    picking_zone_id = package.packed_lot_id.product_id.picking_location_id.id or False
                    picking_zone = package.packed_lot_id.product_id.picking_location_id.bcd_name or\
                               package.packed_lot_id.product_id.picking_location_id.name or False


            vals = {
                'exist' : True,
                'package' : package.name,
                'package_id' :package.id,
                'src_location_id' : package.location_id.id,
                'src_location': package.location_id.bcd_name or package.location_id.name or False,
                'dest_location_id' : False,
                'dest_location': False,
                'lot_id': package.packed_lot_id.id or False,
                'lot': package.packed_lot_id.name or "Lote",
                'product_id' : package.packed_lot_id.product_id.id,
                'product' : package.packed_lot_id.product_id.short_name
                            or package.packed_lot_id.product_id.name or 'Producto',
                'ref' : package.product_id.default_code or package.packed_lot_id.product_id.default_code or '',
                'parent_id' : package.parent_id.id or False,
                'parent_package': package.parent_id.name or '',
                'packed_qty': package.packed_qty or 0,
                'packed_lot_id': package.packed_lot_id.id or False,
                'packed_lot' : package.packed_lot_id.name or 'Lote',

                'uom' : package.uom_id.name or '',
                'uom_id': package.uom_id.id or package.packed_lot_id.product_id.uom_id.id or False,
                'is_multiproduct':package.is_multiproduct,
                'qty':package.packed_qty or 0.0,
                'uos_id':package.uos_id.id or False,
                'uos':package.uos_id.name or package.uom_id.name,
                'uos_qty': package.uos_qty or package.packed_qty,
                'change': False,
                'picking_location_id':picking_zone_id,
                'picking_location':picking_zone,
                'src_location_bcd': package.location_id.bcd_name or package.location_id.name or False,
                'dest_location_bcd': False,
                'life_date': package.packed_lot_id.life_date or '00/00/0000'}
            if package.children_ids:
                picking_zone_id = package.children_ids[0].product_id.picking_location_id.id
                picking_zone = 'Zona de Multipalets'
                vals = {
                    'exist' : True,
                    'package' : package.name,
                    'package_id' :package.id,
                    'src_location_id' : package.location_id.id or False,
                    'src_location': package.location_id.bcd_name or package.location_id.name or False,
                    'dest_location_id' : False,
                    'dest_location': False,
                    'lot_id': False,
                    'lot': "MultiPack",
                    'ref':'Multi',
                    'packed_lot_id': package.packed_lot_id.id or False,
                    'packed_lot' : package.packed_lot_id.name or 'Lote',
                    'parent_id' : package.parent_id.id or False,
                    'parent_package': package.parent_id.name or '',
                    'product_id' : False,
                    'product' : 'MultiProducto',
                    'packed_qty': package.packed_qty or 0,
                    'uom' : package.children_ids[0].product_id.uom_id.name or '',
                    'uom_id': package.children_ids[0].product_id.uom_id.id or False,
                    'is_multiproduct':package.is_multiproduct,
                    'qty':0,
                    'uos_id':package.uos_id.id or False,
                    'uos':package.uos_id.name or package.uom_id.name or False,
                    'uos_qty': package.uos_qty or package.packed_qty or 0.00,
                    'change': False,
                    'picking_location_id':picking_zone_id or False,
                    'picking_location':picking_zone,
                    'src_location_bcd': package.location_id.bcd_name or package.location_id.name or False,
                    'dest_location_bcd': False,
                }

        return vals

class stock_production_lot(models.Model):

    _inherit = "stock.production.lot"

    @api.multi
    def get_lot_gun_info(self, my_args):
        lot_id = my_args.get("lot_id", False)
        domain = [('id', '=', lot_id)]
        lot = self.search(domain)
        vals = {'exist':False}
        if lot:
            vals = {
                'exist' : True,
                'lot_id' : lot.id,
                'lot' : lot.name,
                'product_id': lot.product_id.id or False,
                'product': lot.product_id.short_name and  lot.product_id.name ,
                'ref': lot.product_id.default_code

            }
        return vals

class manual_transfer_wzd(models.TransientModel):

    _inherit = 'manual.transfer.wzd'

    @api.multi
    def do_manual_transfer_from_gun(self, my_args):
        """
        Get a task for a user and type defined in my args.
        """
        user_id = my_args.get('user_id', False)
        my_args = my_args.get('vals', {})
        package_id= my_args.get('package_id', False)
        product_id= my_args.get('product_id', False)
        quantity = my_args.get('quantity', 1)
        lot_id = my_args.get('lot_id', False)
        src_location_id= my_args.get('src_location_id', False)
        dest_location_id= my_args.get('dest_location_id', False)
        do_pack = my_args.get('do_pack', 'no_pack')
        package = my_args.get('package', False)

        #miramos paquete en destino
        # location_dest = self.env['stock.location'].browse(dest_location_id)
        # pack = location_dest.get_package_of_lot(lot_id)
        vals_prod_line_ids ={
            'package_id': package_id,
            'product_id': product_id,
            'quantity': quantity,
            'lot_id': lot_id,
            'src_location_id': src_location_id,
            'dest_location_id': dest_location_id,
            'do_pack': do_pack,
        }
        vals_pack_line_ids = {
            'package_id': package_id,
            'src_location_id': src_location_id,
            'dest_location_id': dest_location_id,
            'do_pack': do_pack,
        }

        t_wzd = self.env['manual.transfer.wzd']
        env2 = t_wzd.env(self._cr, user_id, self._context)
        wzd_obj_uid = t_wzd.with_env(env2)

        # CHANGUING USER ID t_wzd.sudo(user_id) no funciona
        wzd_obj = wzd_obj_uid.create({'pack_line_ids': vals_pack_line_ids})
        if product_id: #or product_id!=False or lot_id!=False or package_id==False:
            vals = vals_prod_line_ids
            val_ids = 'prod_line_ids'
        else:
            vals = vals_pack_line_ids
            val_ids = 'pack_line_ids'
        wzd_obj.write({val_ids: [(0,0, vals)]})
        res = wzd_obj.do_manual_transfer()
        return res
