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
import time

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    visited = fields.Boolean('Visited', default=False)
    state= fields.Char()
    wave_ok = fields.Boolean('Wave Ok', default = True)
    op_package_id = fields.Many2one('stock.quant.package', 'Original Pack',  default = False)

    @api.multi
    def get_user_packet_busy(self, my_args):

        packet_id = my_args.get('packet_id', 0)
        domain = [('package_id', '=', packet_id),('task_id.state', '=', 'assigned')]
        ops_ids = self.search(domain)
        res = False
        if ops_ids:
            for op in ops_ids:
                task = op.task_id
                res = {'ref': task.type[0:4] + '/' + str(task.id),
                           'user': task.user_id.name}

        #si está enun poicking. Revisar con un pick
        if not res:
            #import ipdb; ipdb.set_trace()
            tasks_pool = self.env['stock.task']
            picks_pool = self.env['stock.picking']
            domain = [('state', '=','assigned'), ('picking_id', '!=', False)]
            tasks = tasks_pool.search(domain)
            if tasks:
                for task in tasks:
                    domain = [('id','=',task.picking_id)]
                    pick = picks_pool.search(domain)
                    if pick:
                        if packet_id in pick.pack_operation_ids:
                             res = {'ref': pick.name,
                                    'user': task.user_id.name}
        return res

    @api.multi
    def set_wave_ops_values(self, my_args):
        # import ipdb; ipdb.set_trace()
        wave_id = my_args.get ('wave_id', 0)
        op_id = my_args.get('op_id',0)
        user_id = my_args.get('user_id', 0)
        field = my_args.get('field', '')
        value = my_args.get ('value', False)
        domain = [('id', '=', wave_id)]

        vals= {field : value}
        wave_reports= self.env['wave.report'].search(domain)
        env2 = wave_reports.env(self._cr, user_id, self._context)
        wave_reports_uid = wave_reports.with_env(env2)
        ops = wave_reports_uid.operation_ids

        ops.write (vals)
        return True

    @api.multi
    def get_ops_from_wave (self, my_args):
        wave_id = my_args.get ('wave_id', 0)
        type = my_args.get('type', 'ubication')

        domain = [
            ('id', '=', wave_id)
        ]
        wave_reports= self.env['wave.report'].search(domain)
        ops = wave_reports.operation_ids
        vals = {}
        ind = 0
        if ops:
            for op in ops:
                values = {
                'ID': op.id,
                'product': op.product_id and op.product_id.short_name or "",
                'CANTIDAD': op.product_qty,
                'lot': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id.id and op.package_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED': op.visited,
                'origen_id': op.location_id.id or 0,
                'destino_id': op.location_dest_id.id or 0,
                'pack_id': op.package_id.id or 0,
                'qty': op.product_qty or 0,
                'paquete_dest_id' : op.result_package_id.id or False,
                'uom' :op.product_uom_id and op.product_uom_id.name or '',
                'origen' : op.location_id.get_short_name(),
                'origen_bcd' : op.location_id.bcd_name or op.location_id.get_short_name(),
                'destino' : op.location_dest_id.get_short_name(),
                'destino_bcd' : op.location_dest_id.bcd_name or op.location_dest_id.get_short_name(),
                'product_id': op.product_id.id or False,
                'lot_id': op.packed_lot_id.id,
                'qty_available':op.packed_lot_id.product_id.qty_available or 0.00
                 }
                if not op.product_id:
                    domain_package = [('id', '=', op.package_id.id)]
                    package_pool= self.env['stock.quant.package'].search(domain_package)[0]
                    values['lot']=package_pool.packed_lot_id.name
                    values['lot_id'] = package_pool.packed_lot_id.id
                    values['product'] = package_pool.packed_lot_id.product_id.short_name or ""
                    values['product_id'] = package_pool.packed_lot_id.product_id.id or False
                    values['qty_available'] = package_pool.packed_lot_id.product_id.qty_available or 0.00
                ind += 1
                vals[str(ind)] = values
            return vals
        else:
            return False

    @api.multi
    def get_ops_from_task (self, my_args):
        task_id = my_args.get ('task_id', 0)
        domain = [
            ('task_id', '=', task_id)
        ]
        op_obj = self.search(domain)
        if op_obj:
            vals = {}
            ind = 0
            for op in op_obj:
                values = {
                'ID': op.id,
                'id': op.id,
                'product': op.product_id.short_name or op.packed_lot_id.product_id.short_name or op.packed_lot_id.product_id.name,
                'CANTIDAD': op.product_qty,
                'lot': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id.id and op.package_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED': False,
                'origen_id': op.location_id.id or 0,
                'destino_id': op.location_dest_id.id or 0,
                'pack_id': op.package_id.id or 0,
                'qty': op.product_qty or 0,
                'result_package_id' : op.result_package_id.id or False,
                'uom' :op.product_uom_id and op.product_uom_id.name or "",
                'origen' : op.location_id.name_get()[0][1],
                'destino' : op.location_dest_id.name_get()[0][1],
                'origen_bcd' : op.location_id.bcd_name or op.location_id.get_short_name(),
                'destino_bcd' : op.location_dest_id.bcd_name or op.location_dest_id.get_short_name(),
                'product_id': op.product_id.id or op.packed_lot_id.product_id.id or False,
                'lot_id': op.packed_lot_id.id,
                'packed_qty': op.packed_qty or 0,
                'uom_id':op.product_uom_id.id or op.packed_lot_id.product_id.uom_id.id or False,
                'uos_id' :op.uos_id.id or False,
                'uos': op.uos_id.name or '',
                'uos_qty': op.uos_qty or 0,
                'changed': False,
                'paquete': op.package_id.id and op.package_id.name or "",
                'lot': op.packed_lot_id and op.packed_lot_id.name or "",
                'producto': op.product_id.short_name or op.packed_lot_id.product_id.short_name or op.packed_lot_id.product_id.name,
                'to_process': op.to_process,
                'qty_available':op.packed_lot_id.product_id.qty_available or 0.00
                }

                #revisar para palet_multiproducto
                if not op.product_id:
                    domain_package = [('id', '=', op.package_id.id)]
                    package_pool= self.env['stock.quant.package'].search(domain_package)[0]
                    if len(package_pool)==1:
                        values['lot']=package_pool.packed_lot_id.name
                        values['lot_id'] = package_pool.packed_lot_id.id
                        values['product'] = package_pool.packed_lot_id.product_id.short_name or ''
                        values['product_id'] = package_pool.packed_lot_id.product_id.id or False
                        values['uom']=package_pool.packed_lot_id.product_id.uom_id.name
                        values['qty_available'] = package_pool.packed_lot_id.product_id.qty_available or 0.00
                ind += 1
                vals[str(ind)] = values
            return vals
        else:
            return False

    @api.multi
    def set_processed_val (self, my_args):
        op_id = my_args.get('op_id', False)
        state = my_args.get ('state', False)
        domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]
        op_obj = self.search(domain, limit=1)
        if not op_obj:
            raise except_orm(_('Error'),
                             _('No operation founded to set as visited'))

        # Browse with correct uid, an mark as visited
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)

        op_obj_uid.write ({'gun_procces' : state , 'visited' : True})
        return True

    @api.multi
    def check_op_visited (self, my_args):
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)
        forzar = my_args.get('forzar', False)

        domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]

        op_obj = self.search(domain, limit=1)
        if not op_obj:
            raise except_orm(_('Error'),
                             _('No operation founded to set as visited'))
        res = op_obj.visited
        # Browse with correct uid, an mark as visited
        if forzar == True:
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            op_obj_uid.write({'visited': True})
        if op_obj:
            return res
        return res

    @api.multi
    def check_op_to_process (self, op_id):
        domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id), ('to_process', '=', True)]
        op_obj = self.search(domain, limit=1)
        if op_obj:
            return True
        return False

    @api.multi
    def set_op_to_process(self, my_args):
        """
        Mark operation defined in my_args as visited an the check if remaining
        operations in task are visited to return true in order to finish task
        or False because we need to show the next operation.
        """
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)
        task_id = my_args.get('task_id', False)
        to_process = my_args.get('to_process', False)
        if op_id:
        # if op_id = False, only check if any not processed
        # approve_pack_operations2 method maybe delete the original operation
        # so we need to search the new
            domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]
            op_obj = self.search(domain, limit=1)
            if not op_obj:
                raise except_orm(_('Error'),
                                 _('No operation founded to set as to process'))

            # Browse with correct uid, an mark as visited
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            op_obj_uid.write({'to_process': to_process})

            # Check if there is more operations to proccess
        task_obj = self.env['stock.task'].browse(task_id)
        res = False
        for op in task_obj.operation_ids:
            if not op.to_process:
                res =  True
        return res

    @api.multi
    def set_op_visited(self, my_args):
        """
        Mark operation defined in my_args as visited an the check if remaining
        operations in task are visited to return true in order to finish task
        or False because we need to show the next operation.
        """
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)
        task_id = my_args.get('task_id', False)

        if not op_id:
            # if not op_id only check if visited
            # approve_pack_operations2 method maybe delete the original operation
            # so we need to search the new
            domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]
            op_obj = self.search(domain, limit=1)
            if not op_obj:
                raise except_orm(_('Error'),
                                 _('No operation founded to set as visited'))

            # Browse with correct uid, an mark as visited
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            op_obj_uid.write({'visited': True})

            # Check if there is more operations to visit
        task_obj = self.env['stock.task'].browse(task_id)
        for op in task_obj.operation_ids:
            if not op.visited:
                return False
        return True

    @api.multi
    def check_packet_op(self, my_args):

        user_id = my_args.get('user_id', False)
        package_id = my_args.get('paquete', False)
        domain = [('paquete', '=' , package_id), ('state', '=', 'assigned')]
        op_obj = self.search(domain)

        if op_obj:
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            res = {
                'user_id' :op_obj_uid.task_id.user_id,
                'user_name' : user_id.name,
                'op_id' : op_obj_uid.id,
                'task_id' : op_obj_uid.task_id
            }
            return res
        else:
            return False

    @api.multi
    def change_op_values(self, my_args):
        """
        Mark operation defined in my_args as visited an the check if remaining
        operations in task are visited to return true in order to finish task
        or False because we need to show the next operation.
        """
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)

        field_values = my_args.get ('field_values', False)
        domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]
        op_obj = self.search(domain, limit=1)
        if not op_obj:
            raise except_orm(_('Error'),
                            _('No operation founded to set as visited'))

        # Browse with correct uid, an mark as visited
        try:
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            op_obj_uid.write(field_values)
            return True
        except Exception:
            return False
    @api.multi
    def change_op_value(self, my_args):
        """
        Mark operation defined in my_args as visited an the check if remaining
        operations in task are visited to return true in order to finish task
        or False because we need to show the next operation.
        """
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)
        field = my_args.get ('field', False)
        value = my_args.get ('value', False)
        domain = ['|', ('id', '=', op_id), ('old_id', '=', op_id)]
        op_obj = self.search(domain, limit=1)
        if not op_obj:
            raise except_orm(_('Error'),
                            _('No operation founded to set as visited'))

        # Browse with correct uid, an mark as visited
        try:
            env2 = op_obj.env(self._cr, user_id, self._context)
            op_obj_uid = op_obj.with_env(env2)
            op_obj_uid.write({field: value})
            return True
        except Exception:
            return False

