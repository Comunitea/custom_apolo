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
    def create_multipack_from_gun(self, my_args):

        user_id = my_args.get('user_id', False)
        package_ids = my_args.get ('package_id', [])
        vals= {
            'is_multiproduct' : True
        }
        new_package = self.create(vals)
        parent_id = new_package.id

        for package_id in package_ids:
            domain = [('id','=', package_id)]
            package = self.search(domain)
            location_id = package.location_id.id
            vals = {
                'parent_id':parent_id
            }
            package.write(vals)
        new_package.write({'location_id':location_id})
        return new_package.name

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
        package = self.search(domain)
        vals = {'exist':False}

        if package:# and package.quant_ids:
            qty = 0
            if package.quant_ids:
                qtys= [t.qty for t in package.quant_ids if t.product_id.id == package.packed_lot_id.product_id.id]
                for qty_ in qtys:
                    qty+= qty_



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
                'lot': package.packed_lot_id.name or "",
                'product_id' : package.packed_lot_id.product_id.id,
                'product' : package.packed_lot_id.product_id.short_name
                            or package.packed_lot_id.product_id.name or 'Vacío'
                ,
                'packed_qty': package.packed_qty or 0,
                'uom' : package.uom_id.name or '',
                'uom_id': package.uom_id.id or package.packed_lot_id.product_id.uom_id.id or False,
                'is_multiproduct':package.is_multiproduct,
                'qty':qty,
                'uos_id':package.uos_id.id or False,
                'uos':package.uos_id.name or package.uom_id.name,
                'uos_qty': package.uos_qty or package.packed_qty,
                'change': False,
                'picking_location_id':picking_zone_id,
                'picking_location':picking_zone,
                'src_location_bcd': package.location_id.bcd_name or package.location_id.name or False,
                'dest_location_bcd': False,
            }
        return vals

    @api.multi
    def create_package_from_gun(self, my_args):
        user_id= my_args.get("user_id", False)
        values = my_args.get('values', {})
        pack_wzd = self.env['stock.quant.package']
        env2 = pack_wzd.env(self._cr, user_id, self._context)
        wzd_obj_uid = pack_wzd.with_env(env2)
        wzd_obj = wzd_obj_uid.create(values)
        return wzd_obj

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

            }
        return vals

class manual_transfer_wzd(models.TransientModel):

    _inherit = 'manual.transfer.wzd'

    @api.multi
    def do_manual_trasfer_from_gun(self, my_args):
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
