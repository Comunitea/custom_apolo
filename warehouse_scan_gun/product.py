# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Javier Colmenero Fernández$ <javier@comunitea.com>
#    $Kiko Sánchez <kiko@comunitea.com>
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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    short_name = fields.Char('Short Name', size=25,
                             help="Short name displayed in the gun")

class product_product (models.Model):

    _inherit = 'product.product'

    @api.multi
    def get_product_gun_complete_info(self, my_args):
        id = my_args.get("product_id", False)
        ean = my_args.get('ean', False)
        domain = []
        if ean:
            domain = [('ean13', '=', ean)]
        if id:
            domain = [('id', '=', id)]
        product = self.search(domain)
        vals = False
        if domain and product:
            var_coeff_un_id =False
            var_coeff_ca_id =False
            if product.var_coeff_un:
                var_coeff_un_id = product.log_base_id.id or False
            if product.var_coeff_ca:
                var_coeff_ca_id = product.log_unit_id.id or False
            vals = {
                'exist' : True,
                'product_id' : product.id,
                'product' : product.short_name or product.name,
                'uom_id': product.uom_id.id,
                'uom':product.uom_id.name,
                'var_coeff_un_id': var_coeff_un_id,
                'var_coeff_ca_id':var_coeff_ca_id,
                'un_ca': product.un_ca,
                'kg_un':product.kg_un,
                'ca_ma':product.ca_ma,
                'virtual_available': product.virtual_available,
                'picking_location_id':product.picking_location_id.id,
                'picking_location':product.picking_location_id.name_get()[0][1],
                'temp_type_id': product.temp_type.id
            }
        return vals

    @api.multi
    def get_packets_for_ean(self, my_args):
        # operations = [x.operation_id for x in
        #                          move.linked_move_operation_ids]
        #            operations = list(set(operations))

        id = my_args.get("product_id", False)
        packets = []
        if not id:
            return packets
        domain = [('product_id', '=', id), ('package_id', '!=', False), ('qty', "!=", 0)]
        stock_quants = self.env['stock.quant'].search(domain)
        if stock_quants:
            packets = [(
                           x.package_id.id,
                           x.package_id.name,
                           x.location_id.name_get()[0][1],
                           x.location_id.id,
                           x.package_id.is_multiproduct,
                           x.package_id.packed_qty,
                           x.package_id.uom_id.name,
                           x.package_id.uom_id.id,
                           x.lot_id.id,
                           x.lot_id.name,
                           x.package_id.uos_qty,
                           x.package_id.uos_id.name)
                       for x in stock_quants
                       if x.location_id.usage=='internal']
            packets =list(set(packets))
        inc=0
        res={}
        for pack in packets:
            inc+=1
            pack_=pack[8]
            qtys = self.env['stock.production.lot'].browse([pack_]).get_lot_qty()
            vals = {
                'package_id': pack[0],
                'package': pack[1],
                'location': pack[2],
                'location_id':pack[3],
                'is_multiproduct': pack[4],
                'packed_qty': qtys,
                'uom':pack[6],
                'uom_id':pack[7],
                'lot_id':pack[8],
                'lot':pack[9],
                'uos_qty':pack[10],
                'uos':pack[11],
            }
            res[str(inc)]=vals

        return res

    @api.multi
    def conv_units_from_gun(self, my_args):

        uom_destino = my_args.get("uom_destino", False)
        uom_origen = my_args.get("uom_origen", False)
        supplier_id = my_args.get("supplier_id", False)
        product_id = my_args.get("product_id", False)
        domain = [('id', '=', product_id)]
        product = self.search(domain)
        res = False
        if product:
            res = product._get_unit_ratios(uom_destino, supplier_id) / \
                  product._get_unit_ratios(uom_origen, supplier_id)

        return res

    @api.multi
    def check_picking_zone(self, my_args):
        #import ipdb; ipdb.set_trace()

        picking_location_id = my_args.get("picking_location_id", False)
        product_id = my_args.get("product_id", True)
        write = my_args.get("write", False)

        domain = [('id', '=', product_id)]
        product = self.search(domain)
        res = False
        if product:
            domain_picking = [('id','=', picking_location_id), ('zone','=','picking'), ('temp_type_id', '=', product.temp_type)]
            picking_location = self.env['stock.picking.location'].search(domain_picking)

            if picking_location and not write:
                res = True
            if picking_location and write:
                res = product.write ({'picking_location_id': picking_location_id})
        return res

