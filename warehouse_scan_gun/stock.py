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
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class stock_picking_wave(models.Model):
    _inherit ='stock.picking.wave'

    @api.multi
    def get_wave_reports_from_task(self, my_args):

        #import ipdb; ipdb.set_trace()
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
                    'PRODUCTO': op.product_id and op.product_id.name or "",
                    'EAN' :op.ean13,
                    'CANTIDAD': op.product_qty,
                    'LOTE': op.lot_id and op.lot_id.name or "",
                    'PAQUETE': op.pack_id.id and op.pack_id.name or "",
                    'ORIGEN': op.location_id.name_get()[0][1],
                    'DESTINO': 'Salida', #; op.location_dest_id.name_get()[0][1],
                    'PROCESADO': op.to_process,
                    'VISITED': op.visited,
                    'origen_id': op.location_id.id or 0,
                    'destino_id': 0,
                    'paquete_id': op.pack_id.id or 0,
                    'paquete_dest_id' : False,
                    'qty': op.product_qty or 0,
                    'uom': op.uom_id.name or False,
                    'uom_id': op.uom_id.id or False,
                    'uos_qty': op.uos_qty or 0,
                    'uos' :op.uos_id.name or False,
                    'uos_id': op.uos_id.id or False,
                    'origen' : op.location_id.get_short_name(),
                    'destino' : 'D',#op.location_dest_id.get_short_name(),
                    'product_id': op.product_id.id or False,
                    'short_name':op.product_id.short_name or ''
                    }

                ind += 1
                vals[str(ind)] = values

            return vals

class wave_report(models.Model):

    _inherit = 'wave.report'



    @api.multi
    def get_waves_from_task (self, my_args):
        #import ipdb; ipdb.set_trace()
        task_id= my_args.get ('task_id', 0)
        domain = [
            ('id', '=', task_id)
        ]
        task = self.env['stock.task'].search(domain)[0]
        if task:
            wave_id = task.wave_id.id

        type = my_args.get('type', 'ubication')

        domain = [
            ('wave_id', '=', wave_id)
        ]
        wave_obj = self.search(domain)
        vals = {}
        ind = 0
        for op in wave_obj:
            #
            # values = {
            #     'id': op.id,
            #     'pack' : op.product_id or  op.package_id,
            #     'qty' : op.product_qty or op.uos_qty,
            #     'ref' : format(op.picking_id or op.id),
            #     'processed': op.processed,
            #     'origin': op.location_id,
            #     'dest': op.location_dest_id,
            # }
            values = {
                'ID': op.id,
                'PRODUCTO': op.product_id and op.product_id.name or "",
                'CANTIDAD': op.product_qty,
                'LOTE': op.lot_id and op.lot_id.name or "",
                'PAQUETE': op.pack_id.id and op.pack_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': 'Salida', #; op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED': False,
                'origen_id': op.location_id.id or 0,
                'destino_id': 0,
                'paquete_id': op.pack_id.id or 0,
                'qty': op.product_qty or 0,
                'paquete_dest_id' : False,
                'uom' :op.uos_id and op.uos_id.name or "",
                'origen' : op.location_id.get_short_name(),
                'destino' : 'D',#op.location_dest_id.get_short_name()
                'product_id': op.product_id.id or False
                }

            ind += 1
            vals[str(ind)] = values

        return vals


class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    visited = fields.Boolean('Visited', default=False)
    state= fields.Char()
    wave_ok = fields.Boolean('Wave Ok', default = True)
    #state =fields.Many2one('stock.task', 'State', readonly=True,
    #                       related="task_id.state")


    @api.multi
    def get_user_packet_busy(self, my_args):

        packet_id = my_args.get('packet_id', 0)
        domain = [('package_id', '=', packet_id)]
        ops_ids = self.search(domain)
        res = {}
        #miramos si está en tareas de ubi o repo
        if ops_ids:
            for op in ops_ids:
                task = op.task_id
                if task.state == 'assigned':
                    res = {'ref': task.type[0:4] + '/' + str(task.id),
                           'user': task.user.id.name}

        #si está enun poicking. Revisar con un pick
        if not res:

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
                                    'user': task.user.id.name}

        return res





    @api.multi
    def set_wave_ops_values(self, my_args):
        import ipdb; ipdb.set_trace()
        wave_id = my_args.get ('wave_id', 0)
        user_id = my_args.get('user_id', 0)
        field = my_args.get('field', '')
        value = my_args.get ('value', False)
        domain = [
            ('id', '=', wave_id)
        ]
        vals= {field : value}
        wave_reports= self.env['wave.report'].search(domain)
        env2 = wave_reports.env(self._cr, user_id, self._context)
        wave_reports_uid = wave_reports.with_env(env2)
        ops = wave_reports_uid.operation_ids
        ops.write (vals)
        return True


    @api.multi
    def get_ops_from_wave (self, my_args):
        #import ipdb; ipdb.set_trace()
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
                'PRODUCTO': op.product_id and op.product_id.name or "",
                'CANTIDAD': op.product_qty,
                'LOTE': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id.id and op.package_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED': op.visited,
                'origen_id': op.location_id.id or 0,
                'destino_id': op.location_dest_id.id or 0,
                'paquete_id': op.package_id.id or 0,
                'qty': op.product_qty or 0,
                'paquete_dest_id' : False,
                'uom' :op.product_uom_id and op.product_uom_id.name or '',
                'origen' : op.location_id.get_short_name(),
                'destino' : op.location_dest_id.get_short_name(),
                'product_id': op.product_id.id or False,
                'short_name' : op.product_id.short_name or ''

                }
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
        return self.get_ops_from_domain (domain)

    @api.multi
    def get_ops_from_domain (self, domain = False):
        if not domain == False:
            op_obj = self.search(domain)
            vals = {}
            ind = 0
            for op in op_obj:
                values = {
                'ID': op.id,
                'PRODUCTO': op.product_id and op.product_id.name or "",
                'CANTIDAD': op.product_qty,
                'LOTE': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id.id and op.package_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED': False,
                'origen_id': op.location_id.id or 0,
                'destino_id': op.location_dest_id.id or 0,
                'paquete_id': op.package_id.id or 0,
                'qty': op.product_qty or 0,
                'paquete_dest_id' : False,
                'uom' :op.product_uom_id and op.product_uom_id.name or "",
                'origen' : op.location_id.get_short_name(),
                'destino' : op.location_dest_id.get_short_name(),
                'product_id': op.product_id.id or False
                }
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
        #import ipdb; ipdb.set_trace()


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