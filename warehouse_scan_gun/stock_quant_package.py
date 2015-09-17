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


class stock_quant_package(models.Model):
    _inherit = 'stock.quant.package'



    @api.multi
    def get_quant_pack_gun_info(self, my_args):
        package_id = my_args.get("package_id", False)
        name = my_args.get('name', False)
        domain = ['|', ('name', '=', name), ('id', '=', package_id)]
        package = self.search(domain)
        vals = {'exist':False}
        if package:
            vals = {
                'exist' : True,
                'package' : package.name,
                'package_id' :package.id,
                'src_location_id' : package.location_id.id,
                'src_location': package.location_id.name_get()[0][1],

            }
        return vals

class product_product (models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_product_gun_info(self, my_args):
        import ipdb; ipdb.set_trace()
        product_ean = my_args.get("product_ean", False)
        domain = [('ean13', '=', product_ean)]
        product = self.search(domain)
        vals = {'exist':False}
        if product:
            vals = {
                'exist' : True,
                'product_id' : product.id,
                'product' : product.name,
            }
        return vals

    @api.multi
    def conv_units_from_gun(self, my_args):

        uom_destino = my_args.get("uom_destino", False)
        uom_origen = my_args.get("uom_origen", False)
        supplier_id = my_args.get("supplier_id", False)
        product_ean = my_args.get("product_ean", False)
        domain = [('ean13', '=', product_ean)]
        product = self.search(domain)
        res = False
        if product:
            res = product._get_unit_ratios(uom_destino, supplier_id) / \
                  product._get_unit_ratios(uom_origen, supplier_id)

        return res


class stock_location(models.Model):

    _inherit = "stock.location"

    @api.multi
    def get_short_name(self):
        short_name = self.name
        zone ="V"
        if self.zone == 'storage':
            zone = "A"
        if self.zone == 'picking':
            zone = "P"
        short_name = zone + '/' + self.name
        return short_name

    @api.multi
    def get_location_gun_info(self, my_args):
        location_id = my_args.get("location_id", False)
        domain = [('id', '=', location_id)]
        type = my_args.get("type", "")
        location = self.search(domain)
        vals = {'exist':False}
        if location:
            vals = {
                'exist' : True,
                type + 'location_id' : location.id,
                type + 'location' : location.name_get()[0][1],
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
            }
        return vals



class manual_transfer_wzd(models.TransientModel):

    _inherit = 'manual.transfer.wzd'


    @api.multi
    def do_manual_trasfer_from_gun(self, my_args):
        """
        Get a task for a user and type defined in my args.
        """
        #import ipdb ; ipdb.set_trace()

        user_id = my_args.get('user_id', False)
        package_id= my_args.get('package_id', False)
        product_id= my_args.get('product_id', False)
        quantity = my_args.get('quantity', 1)
        lot_id = my_args.get('lot_id', False)
        src_location_id= my_args.get('src_location_id', False)
        dest_location_id= my_args.get('dest_location_id', False)
        do_pack = my_args.get('do_pack', 'no_pack')

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
        #import ipdb; ipdb.set_trace()
        t_wzd = self.env['manual.transfer.wzd']
        env2 = t_wzd.env(self._cr, user_id, self._context)
        wzd_obj_uid = t_wzd.with_env(env2)

        # CHANGUING USER ID t_wzd.sudo(user_id) no funciona
        wzd_obj = wzd_obj_uid.create({'pack_line_ids': vals_pack_line_ids})

        if quantity >1 or product_id!=False or lot_id!=False or package_id==False:
            vals = vals_prod_line_ids
            val_ids = 'prod_line_ids'

        else:
            vals = vals_pack_line_ids
            val_ids = 'pack_line_ids'
        #import ipdb; ipdb.set_trace()

        res = wzd_obj.write({val_ids: [(0,0, vals)]})

        wzd_obj.do_manual_transfer()

        return True


        #
