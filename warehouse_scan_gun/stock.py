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

from openerp import models, fields, api
import time


class stock_quant(models.Model):

    _inherit = "stock.quant"

    def get_stock_from_output_stock(self,package_id, write = False, quant_id = False):

        #añadimos la cantidad indicada en el paquete leido
        output_stock_loc_id = self.env['stock.warehouse'].browse(1).wh_output_stock_loc_id.id

        domain = [('package_id', '=', package_id)]
        package_id = self.env['stock.quant.package'].search(domain)
        domain = [('product_id', '=', package_id.product_id.id), ('location_id', '=', output_stock_loc_id), ('reservation_id', '=', False)]
        quant_ids = self.env['stock.quant'].sudo().search(domain)
        if write and quant_id:
            res = False
            quant_ids = self.env['stock.quant'].sudo().browse(quant_id)
            values = {
                'package_id': package_id.id,
                'location_id': package_id.location_id.id,

                }
            res = quant_ids.write(values)
            return res
        else:
            res = []
            for quant in quant_ids:
                quant_ = [quant.id, quant.qty, quant.product_id.uom_id.name]
                res.append(quant_)
            return res



class stock_picking_wave(models.Model):
    _inherit ='stock.picking.wave'

    @api.multi
    def get_wave_reports_from_task2(self, my_args):

        #Aquí recargamos la pistola con las oleadas ...
        task_id = my_args.get ('task_id', 0)
        domain = [('id', '=', task_id)]
        wave_id = self.env['stock.task'].search(domain).wave_id.id
        domain=[('id','=',wave_id)]
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}
        self_ = self.env['stock.picking.wave'].with_context(ctx)
        wave = self_.search(domain)


        if wave:

            vals = {}
            ind = 0
            for op in wave.wave_report_ids:

                values = {
                    'id': op.id,
                    'wave_report_id': op.id,
                    'product': op.product_id.name and op.product_id.short_name or "",
                    'default_code' : op.product_id.default_code or '',
                    'CANTIDAD': op.product_qty or 0.00,
                    'lot': op.lot_id and op.lot_id.name or "",
                    'lot_id': op.lot_id.id or False,
                    'package': op.pack_id.id and op.pack_id.name or "",
                    'DESTINO': 'Salida', #; op.location_dest_id.bcd_name,
                    'to_process': op.to_process or False,
                    'VISITED': op.visited or False,
                    'origen_id': op.location_id.id or 0,
                    'destino_id': 0,
                    'pack_id': op.pack_id.id or 0,
                    'paquete_dest_id' : False,
                    'qty': op.product_qty or 0,
                    'uom': op.uom_id.name or False,
                    'uom_id': op.uom_id.id or False,
                    'uom_qty' : op.product_qty or 0.00,
                    'uos_qty': op.uos_qty or op.product_qty or 0,
                    'uos' :op.uos_id.name or op.uom_id.name,
                    'uos_id': op.uos_id.id or op.uom_id.id or False,
                    'origen' : op.location_id.get_short_name(),
                    'origen_bcd' : op.location_id.bcd_name or op.location_id.get_short_name(),
                    'destino' : 'D',#op.location_dest_id.get_short_name(),
                    'product_id': op.product_id.id or False,
                    'to_revised':op.to_revised or False,
                    'is_var_coeff': op.product_id.is_var_coeff or False,
                    'var_coeff_ca':op.product_id.var_coeff_ca or False,
                    'num_ops':len(op.operation_ids) or 1,
                    'packed_qty': op.pack_id.packed_qty or False,
                    'customer_id': op.customer_id.comercial or op.customer_id.name,
                    'ref': op.customer_id.ref or False,
                    'qty_available': op.product_id.qty_available or 0.00,
                    'name':op.wave_id.name or '',
                    'is_package': op.is_package,
                    'origen_bcd_code':op.location_id.bcd_code or ''
                    }
                values['qty_available'] = op.pack_id.packed_qty or 0.00
                # if op.operation_ids:
                #     values['op'] =  op.id
                product = op.product_id or op.pack_id.product_id
                uom_id = product.uom_id.id
                uom_qty = op.product_qty
                if product:
                    if product.is_var_coeff:
                        qty = op.uos_qty
                    else:
                        qty = uom_qty
                values['units'] = product.get_uom_conversions(qty, uom_id = op.uos_id.id)


                uom_destino = product.log_box_id.id or product.log_unit_id.id or product.log_base_id.id
                uom_origen = op.uos_id.id or op.uom_id.id
                values['big_unit'] = product._get_unit_ratios(uom_destino, False) / \
                    product._get_unit_ratios(uom_origen, False)

                ind += 1
                vals[str(ind)] = values

            return vals


    @api.multi
    def get_wave_reports_from_task(self, my_args):

        #Aquí recargamos la pistola con las oleadas ...

        task_id = my_args.get ('task_id', 0)
        domain = [('id', '=', task_id)]
        wave_id = self.env['stock.task'].search(domain).wave_id.id
        domain=[('id','=',wave_id)]
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': 1}
        self_ = self.env['stock.picking.wave'].with_context(ctx)
        wave = self_.search(domain)
        num_to_process = 0
        print u"Actualizamos Oleadas. %s"%wave.name
        if wave:
            vals = {}
            ind = 0
            for wave_report in wave.wave_report_ids:

                values = wave_report.get_wave_report_values()
                if values ['to_process']:
                    num_to_process += 1
                ind += 1
                vals[str(ind)] = values
                print u"Etiqueta %s: %s %s"%(values['package'], values['qty'], values['uom'])

            return vals
