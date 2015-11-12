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


class stock_picking_wave(models.Model):
    _inherit ='stock.picking.wave'

    @api.multi
    def get_wave_reports_from_task(self, my_args):

        task_id = my_args.get ('task_id', 0)
        domain = [('id', '=', task_id)]
        wave_id = self.env['stock.task'].search(domain).wave_id.id
        domain=[('id','=',wave_id)]
        wave = self.search(domain)
        if wave:
            vals = {}
            ind = 0
            for op in wave.wave_report_ids:
                values = {
                    'ID': op.id,
                    'product': op.product_id.name and op.product_id.short_name or "",
                    'EAN' :op.ean13,
                    'CANTIDAD': op.product_qty or 0.00,
                    'lot': op.lot_id and op.lot_id.name or "",
                    'PAQUETE': op.pack_id and op.pack_id.name or "",
                    'package': op.pack_id.id and op.pack_id.name or "",
                    'ORIGEN': op.location_id.bcd_name,
                    'DESTINO': 'Salida', #; op.location_dest_id.bcd_name,
                    'PROCESADO': op.to_process or False,
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
                    'num_ops':len(op.operation_ids) or 1,
                    'op': op.operation_ids[0].id or False,
                    'customer_id': op.customer_id.comercial or op.customer_id.name,
                    'ref': op.customer_id.ref or False,
                    'qty_available': op.product_id.qty_available or 0.00,
                    'name':op.wave_id.name or '',
                    'is_package': op.is_package
                    }

                ind += 1
                vals[str(ind)] = values

            return vals
