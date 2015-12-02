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
from openerp import models, fields, api, _, exceptions
#from openerp.exceptions import except_orm
from openerp.tools.float_utils import float_round
import decimal

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    short_name = fields.Char('Short Name', size=25,
                             help="Short name displayed in the gun")

    # @api.constrains('picking_location_id')
    # def _check_picking_location(self):
    #
    #     if self.picking_location_id.default_picking_zone == False:
    #         domain =[('picking_location_id', '=', self.picking_location_id.id),
    #              ('id', '!=', self.id)]
    #         count = self.search(domain)
    #         if count:
    #             raise exceptions.Warning(_('Error!'), _('Picking ubication must be unique or default picking zone.'))


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
                'is_var_coeff': product.is_var_coeff,
                'un_ca': product.un_ca,
                'kg_un':product.kg_un,
                'ca_ma':product.ca_ma,
                'virtual_available': product.virtual_available,
                'picking_location_id':product.picking_location_id.id,
                'picking_location':product.picking_location_id.bcd_name,
                'bcd_picking_location':product.picking_location_id.bcd_name,
                'temp_type_id': product.temp_type.id,
                'qty_available' :product.qty_available
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
                           x.location_id.bcd_name,
                           x.location_id.id,
                           x.package_id.is_multiproduct,
                           x.package_id.packed_qty,
                           x.package_id.uom_id.name,
                           x.package_id.uom_id.id,
                           x.lot_id.id,
                           x.lot_id.name,
                           x.package_id.uos_qty,
                           x.package_id.uos_id.name,
                           x.location.bcd_name)
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
                'location_bcd':pack[12]
            }
            res[str(inc)]=vals

        return res


    #esta es la original OK
    @api.multi
    def get_uom_conversions2(self, uom_qty, product_id = False, uom_id = False):
        # product_id = my_args.get("product_id", False)
        # uom_id = my_args.get("uom_id", False)
        # uom_qty = my_args.get("uom_qty", 0.00)

        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}

        if product_id:
            domain = [('id', '=', product_id)]
            product = self.search(domain)
        else:
            product = self.ensure_one()

        product= self.env['product.product'].browse(product.id).with_context(ctx)

        base_qty = 0.00
        if not uom_id:
            uom_id = product.uom_id.id
        unit_to = self.env['product.uom'].browse(uom_id)




        # if product.log_base_id.id == uom_id:
        #     base_qty = uom_qty
        #     rounding = product.log_base_id.rounding
        #     #si tiene log_box
        #
        # elif product.log_unit_id.id == uom_id:
        #     base_qty = uom_qty * product.kg_un
        #     rounding = product.log_unit_id.rounding or 0.00
        #
        # elif product.log_box_id.id ==uom_id:
        #     base_qty = uom_qty * product.kg_un * product.un_ca
        #     rounding = product.log_box_id.rounding or 0.00

        #base_qty = float_round(base_qty,  precision_rounding = rounding)
        conv =[]
        rest = uom_qty
        rounding = 2
        box_qty=0
        unit_qty=0
        base_qty=0

        if product.log_box_id:

            box_id = product.log_box_id.name
            if product.log_box_id.id == uom_id:
                box_qty = float_round(uom_qty, precision_rounding = product.log_box_id.rounding)
                rest = 0

            # elif product.log_base_id or product.log_unit_id:
            #     #Hay más unidades
            #     box_qty = int(rest / (product.kg_un * product.un_ca))
            #     rest = rest - (box_qty * (product.kg_un * product.un_ca))
            # else:
            #     #no hay más unidades, redondeo a cajas
            #     box_qty = float_round(rest / (product.kg_un * product.un_ca),  precision_rounding = product.log_box_id.rounding)
            #     rest = 0
            box_append = (box_id, float_round(box_qty, precision_rounding = max(product.log_box_id.rounding, 0.01)), product.log_box_id.id, 1)

        else:
            box_append  = (False, 0, False, 1)


        if product.log_unit_id:
            unit_id = product.log_unit_id.name

            if product.log_unit_id.id == uom_id:
                if product.log_box_id and uom_qty >= product.un_ca:
                    box_qty = int(uom_qty/product.un_ca)
                    rest = uom_qty - box_qty * product.un_ca
                    box_append = (product.log_box_id.name, float_round ( box_qty, precision_rounding = max(product.log_box_id.rounding, 0.01)), product.log_box_id.id, 1)

                if (not product.log_box_id or uom_qty < product.un_ca):
                    box_append  = (False, 0, False, 1)
                    rest = uom_qty

            if product.log_base_id:
                unit_qty = int(rest)
                rest = (rest - unit_qty) * product.kg_un
            else:
                unit_qty = float_round(rest,  precision_rounding = product.log_unit_id.rounding)
                rest =0

            unit_append = (unit_id,  float_round ( unit_qty, precision_rounding = max(product.log_unit_id.rounding, 0.01)), product.log_unit_id.id, product.un_ca)
        else:
            unit_append = (False, 0, False, 1)


        if product.log_base_id:

            if product.log_base_id.id == uom_id:
                if product.log_box_id:
                    box_qty = int (rest / (product.un_ca * product.kg_un))
                    unit_qty_ = rest - box_qty
                    box_append = (box_id, box_qty, product.log_box_id.id, 1)
                    rest = unit_qty_
                if product.log_unit_id:
                    unit_qty = int (rest/ (product.kg_un))
                    base_qty_ = rest - unit_qty
                    unit_append = (unit_id, unit_qty, product.log_unit_id.id,  product.un_ca)
                    rest = base_qty


            base_id = product.log_base_id.name
            base_append = (base_id,  float_round (rest, precision_rounding = max(product.log_base_id.rounding, 0.01)),product.log_base_id.id, product.kg_un )
        else:

            base_append = (False, 0, False, 1)

        conv.append(base_append)
        conv.append(unit_append)
        conv.append(box_append)
        print "Conversion para %s de %s de %s. Conv %s/%s" %(uom_qty, unit_to.name, product.name, product.un_ca, product.kg_un)
        print "          >> %s\n"%conv
        return conv

    #Esta es la nueva NO OK
    @api.multi
    def get_uom_conversions(self, uom_qty, product_id = False, uom_id = False):
        # product_id = my_args.get("product_id", False)
        # uom_id = my_args.get("uom_id", False)
        # uom_qty = my_args.get("uom_qty", 0.00)
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}

        if product_id:
            domain = [('id', '=', product_id)]
            product = self.search(domain)
        else:
            product = self.ensure_one()

        product= self.env['product.product'].browse(product.id).with_context(ctx)


        base_qty = 0.00
        if uom_qty < 1:
            uom_qty = uom_qty - 0.001


        decim = decimal.Decimal(str(uom_qty))
        decimales = decim.as_tuple().exponent
        uom_qty += 0.001
        if not uom_id:
            uom_id = product.uom_id.id
        unit_to = self.env['product.uom'].browse(uom_id)

        #base_qty = float_round(base_qty,  precision_rounding = rounding)
        conv =[]
        rest = uom_qty
        rounding = 2
        box_qty=0
        unit_qty=0
        base_qty=0
        unit_id = product.log_unit_id.name
        box_id = product.log_box_id.name
        base_id = product.log_base_id.name
        unit_append = (False, 0, False, 1)
        base_append = (False, 0, False, 1)
        box_append = (False, 0, False, 1)

        if product.log_base_id.id == uom_id:
            rest = uom_qty

        elif product.log_unit_id.id == uom_id:
            rest = uom_qty * product.kg_un

        elif product.log_box_id.id ==uom_id:
            rest = uom_qty * product.kg_un * product.un_ca

        #si hay unidades

        if product.log_box_id:
            if product.log_unit_id or product.log_base_id:
                box_qty = int(rest / (product.kg_un * product.un_ca))
                rest = rest - (box_qty * product.kg_un * product.un_ca)
            else:
                box_qty = rest / (product.kg_un * product.un_ca)

            box_append = (product.log_box_id.name, float_round (box_qty, precision_rounding = product.log_box_id.rounding), product.log_box_id.id, 1)

        if product.log_unit_id:
            if product.log_base_id:
                unit_qty = int(rest /product.kg_un)
                rest = rest - (unit_qty * product.kg_un)
            else:
                unit_qty= rest / product.kg_un
            unit_append = (unit_id, float_round (unit_qty, precision_rounding = product.log_unit_id.rounding), product.log_unit_id.id, product.un_ca)

        if product.log_base_id:
            base_qty = rest
            base_append = (base_id, float_round (base_qty, precision_rounding = product.log_base_id.rounding), product.log_base_id.id, product.kg_un )

        conv.append(base_append)
        conv.append(unit_append)
        conv.append(box_append)
        print "Conversion para %s de %s de %s. Conv %s/%s" %(uom_qty, unit_to.name, product.name, product.un_ca, product.kg_un)
        print "          >> %s\n"%conv
        return conv

    @api.multi
    def get_uom_from_conversions_from_gun(self,my_args):
        units = my_args.get('units', [])
        product_id = my_args.get ('product_id', False)
        uos_id = my_args.get ('uos_id', False)
        return self.get_uom_from_conversions(units, product_id, uos_id)

    @api.multi
    def get_uom_from_conversions(self, units, product_id = False, uos_id = False):

        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}
        if product_id:
            domain = [('id', '=', product_id)]
            product = self.search(domain)
        else:
            product = self.ensure_one()
        if not product:
            return []

        product= self.env['product.product'].browse(product.id).with_context(ctx)
        uom_qty = 0.00
        #Para eliminar periódicos:


        if uos_id:
            uom_id = self.env['product.uom'].browse(uos_id).with_context(ctx) or False
        else:
            uom_id = product.uom_id

        if product.log_base_id.id == uom_id.id:
            uom_qty = units[0]
            uom_qty += float_round(units[1]* product.kg_un,  precision_rounding = product.log_base_id.rounding)
            uom_qty += float_round(units[2]* (product.un_ca * product.kg_un), precision_rounding = product.log_base_id.rounding)

        elif product.log_unit_id.id == uom_id.id:
            uom_qty = units[1]
            uom_qty += float_round(units[0] / product.kg_un, precision_rounding = product.log_unit_id.rounding)
            uom_qty += float_round(units[2] * product.un_ca, precision_rounding = product.log_base_id.rounding)

        elif product.log_box_id.id ==uom_id.id:
            uom_qty = units[2]
            uom_qty += float_round(units[0] / (product.kg_un * product.un_ca),  precision_rounding = product.log_base_id.rounding)
            uom_qty += float_round(units[1] / (product.un_ca),  precision_rounding = product.log_base_id.rounding)
        return uom_qty


    @api.multi
    def get_pack_candidates_from_gun(self, my_args):
        product_id = my_args.get('product_id', False)
        min_qty = my_args.get('min_qty', False)
        return self.get_pack_candidates(product_id, min_qty)

    @api.multi
    def get_pack_candidates(self, product_id, min_qty=False):

        res = []

        # product_id = my_args.get('product_id', False)
        # min_qty = my_args('min_qty', False)
        if product_id:
            t_pack = self.env['stock.quant.package']
            wh = self.env['stock.warehouse'].search([])[0]
            stock_loc = wh.lot_stock_id
            domain = [('product_id', '=', product_id),
                      ('quant_ids', '!=', False),
                      ('location_id', 'child_of', [stock_loc.id])]
            pack_objs = t_pack.search(domain)

            for p in pack_objs:
                if min_qty and p.unreserved_qty < min_qty \
                        or not p.unreserved_qty:
                    continue
                dic = {
                    'package_id': p.id,
                    'package': p.name,
                    'product': p.product_id.name,
                    'unreserved_qty': p.unreserved_qty,
                    'uom': p.uom_id.name,
                    'bcd_name': p.location_id.bcd_name,
                }
                res.append(dic)
        if res:
            res = sorted(res, key=lambda d: d['unreserved_qty'], reverse=True)
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

        picking_location_id = my_args.get("picking_location_id", False)
        product_id = my_args.get("product_id", True)
        write = my_args.get("write", False)

        domain = [('id', '=', product_id)]
        product = self.search(domain)
        res = False
        if product:
            domain_picking = [('id','=', picking_location_id), ('zone','=','picking'), ('temp_type_id', '=', product.temp_type.id)]
            picking_location = self.env['stock.location'].search(domain_picking)

            if picking_location and not write:
                res = True
            if picking_location and write:
                res = product.write ({'picking_location_id': picking_location_id})
        return res
