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
                        'location': quant.location_id.name_get()[0][1],
                        'product_id': quant.product_id.id,
                        'product' : quant.product_id.name,
                        'quantity' : quant.qty,
                        'uom': quant.product_id.uom_id.name
                    }
                res[str(quant.id)]=vals
            return res



class stock_quant_package(models.Model):

    _inherit = 'stock.quant.package'
    @api.multi
    def get_quant_pack_gun_info(self, my_args):
        package_id = my_args.get("package_id", False)
        domain = [('id', '=', package_id)]
        package = self.search(domain)
        vals = {'exist':False}
        if package:
            vals = {
                'exist' : True,
                'package' : package.name,
                'package_id' :package.id,
                'src_location_id' : package.location_id.id,
                'src_location': package.location_id.name_get()[0][1],
                'dest_location_id' : False,
                'dest_location': '',
                'packet_lot_id': package.packed_lot_id.id,
            }
        return vals

class product_product (models.Model):
    _inherit = 'product.product'

    short_name=fields.Char("Short Name", size = 25)
    internal_code = fields.Char("Importation code")

    @api.multi
    def get_product_gun_complete_info(self, my_args):

        id = my_args.get("product_id", False)
        domain = [('id', '=', id)]
        product = self.search(domain)
        vals = {'exist':False}
        if product:
            var_coeff_un_id =False
            var_coeff_ca_id =False
            if product.var_coeff_un:
                var_coeff_un_id = product.log_base_id.id or False
            if product.var_coeff_ca:
                var_coeff_ca_id = product.log_unit_id.id or False
            vals = {
                'exist' : True,
                'product_id' : product.id,
                'product' : product.name,
                'short_name':product.default_code,
                'uom_id': product.uom_id.id,
                'var_coeff_un_id': var_coeff_un_id,
                'var_coeff_ca_id':var_coeff_ca_id,
                'un_ca': product.un_ca,
                'kg_un':product.kg_un,
                'ca_ma':product.ca_ma
            }
        return vals


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
        product_id = my_args.get("product_id", False)
        domain = [('id', '=', product_id)]
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

class wave_reports(models.Model):

    _name = 'wave.reports'
    _order = 'wave_id'

    wave_id = fields.Many2one('wave.report', 'Id wave_report')
    to_revised = fields.Boolean ('To Revised', default = False)
    uos_qty = fields.Float("Uos Qty", default = 0.00)
    uom_qty = fields.Float("Uom Qty", default = 0.00)

    @api.multi
    def set_wave_reports_values(self, my_args):
        """
        Setea una campo con el valor para todas las ops
        de un wave.report
        """
        wave_id = my_args.get('wave_id', False)
        user_id = my_args.get('user_id', False)
        field = my_args.get ('field', False)
        #value =my_args('value', False)

        env2 = self.env(self._cr, user_id, self._context)
        wave_pool = self.with_env(env2)
        wave = wave_pool.browse(wave_id)
        if wave:
            for op in wave.operation.ids:
                res = op.write(field)
        else:
            for op in wave.operation.ids:
                res = op.create({field})
        return res

class wave_report(models.Model):

    _inherit = 'wave.report'

    @api.multi
    def set_wave_op_values(self, my_args):
        """
        Setea una campo con el valor para todas las ops
        de un wave.report
        """
        wave_id = my_args.get('wave_id', False)
        user_id = my_args.get('user_id', False)
        field = my_args.get ('field', False)
        value =my_args('value', False)

        env2 = self.env(self._cr, user_id, self._context)
        wave_pool = self.with_env(env2)
        wave = wave_pool.browse(wave_id)
        if wave:
            for op in wave.operation.ids:
                if field == 'to_process':
                    res = op.write({field : value, 'visited' : True})
                else:
                    res = op.write({field : value})

        else:
            res = False

        return res

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
                'product_id': lot.product_id.id or False
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
