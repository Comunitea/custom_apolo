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
from openerp import fields, models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _

class StockTask(models.Model):
    _inherit = 'stock.task'

    gun_begin = fields.Boolean('Tarea Comenzada desde Pistola', default = False)


    @api.multi
    def reset_to_process(self, my_args):
        for op in self.operation_ids:
             op.to_process = False
             op.visited = False
             op.gun_procces = False

    @api.multi
    def set_task_pause_state(self, my_args):
        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)
        pause_state = my_args.get ('pause_state', False)

        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)
        task_obj_uid.paused = pause_state


        return True

    @api.multi
    def get_task_assigned(self, my_args):
        user_id = my_args.get('user_id', False)
        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned')
        ]
        task_id = False
        task_obj = self.search(domain)
        vals = {}
        ind = 0
        for task in task_obj:

            values = {
                'id': task.id,
                'type' : task.type,
                'paused' : task.paused,
                'ref' : (task.wave_id.name or task.picking_id.name or (task.type[0:4] + '/' +  str(task.id))).capitalize(),
                #'name': task.name,
                'ops': len(task.operation_ids) or len(task.wave_id.wave_report_ids),
                'wave_id': task.wave_id.id or False
            }
            if task.paused:
                ind += 1
                vals[format(ind)] = values
            else:

                vals[format(0)] = values
                task_id = task.id
        return task_id, vals

    @api.multi
    def get_task_of_type(self, my_args):
        """
        Get a task for a user and type defined in my args.
        """
        user_id = my_args.get('user_id', False)
        camera_id = my_args.get('camera_id', False)
        task_type = my_args.get('task_type', False)
        machine_id = my_args.get('machine_id', False)
        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned'),
            ('paused', '=', False),
        ]
        task_obj = self.search(domain)
        if task_obj:
            print "Te doy la que tenias"
            return task_obj.id

        vals = {
            'operator_id': user_id,
            'machine_id': machine_id,
            'location_ids': [(4, camera_id, 0)],
            'mandatory_camera': True,
            'print_report': False,
            # 'max_loc_ops':
            # 'min_loc_replenish':
            # 'warehouse_id':
            # 'trans_route_id':
            # 'date_planned':
        }
        t_wzd = self.env['assign.task.wzd']
        # CHANGUING USER ID t_wzd.sudo(user_id) no funciona
        wzd_obj = t_wzd.create(vals)
        env2 = wzd_obj.env(self._cr, user_id, self._context)
        wzd_obj_uid = wzd_obj.with_env(env2)
        #import ipdb; ipdb.set_trace()
        if task_type == 'ubication':
            wzd_obj_uid.get_location_task()
        elif task_type == 'reposition':
            wzd_obj_uid.get_reposition_task()
        elif task_type == 'picking':
            wzd_obj_uid.get_picking_task()

        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned'),
            ('type', '=', task_type),
            ('paused', '=', False),
        ]
        task_obj = self.search(domain)
        if not task_obj:
            return False
            raise except_orm(_("Error"), _("Task not founded after create it"))
        for op in task_obj.operation_ids:
            op.write({'visited': False})
        print "te doy una creada: Id" +str(task_obj.id)
        return task_obj.id

    @api.multi
    def check_task_ops_finished(self, my_args):
        task_id = my_args.get('task_id', False)
        #user_id = my_args.get('user_id', False)
        domain= [('task_id', '=', task_id), ('to proccess', '=', True)]
        ops = self.env['stock.pack.operation'].search(domain)
        if not ops:
            return True
        return False

    @api.multi
    def get_op_data(self, my_args):
        """
        Return data for next operation not visited.
        """
        user_id = my_args.get('user_id', False)
        task_id = my_args.get('task_id', False)
        task_obj = self.browse(user_id)
        op_data = {}
        for op in task_obj.operation_ids:
            if op.visited:
                continue
            op_data = {
                'ID': op.id,
                'PRODUCTO': op.product_id and op.product_id.name or "",
                'CANTIDAD': str(op.product_qty),
                'LOTE': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id and op.package_id.name or "",
                'ORIGEN': op.location_id.name_get()[0][1],
                'DESTINO': op.location_dest_id.name_get()[0][1],
                'PROCESADO': op.to_process,
                'VISITED' :op.visited,
                'origen_id': op.location_id.id,
                'destino_id': op.location_dest_id.id,
                'paquete_id': op.package_id.id,
                'origen' : op.location_id.get_short_name(),
                'destino' : op.location_dest_id.get_short_name()

            }
        return op_data

    @api.multi
    def check_scan(self, my_args):
        res = False
        task_id = my_args.get('task_id', False)
        scan_code = my_args.get('scan', False)
        mode = my_args.get('mode', False)
        op_id = my_args.get('op_id')
        task_obj = self.browse(task_id)
        op_obj = False
        for op in task_obj.operation_ids:
            if op.id == op_id or op.old_id == op_id:
                op_obj = op
                break
        if not op_obj:
            raise except_orm(_("Error"),
                             _("Operation not founded in the task"))

        if mode == "pack_prod":
            if op_obj.package_id:
                if op.package_id.name == scan_code:
                    res = True
            elif op.product_id and not op_obj.package_id:
                if op.product_id.ean13 == scan_code:
                    res = True
        elif mode == "location":

            if op.location_dest_id.name == scan_code:
                res = True
        return res

    @api.multi
    def gun_begin_task(self, my_args):
        #import ipdb; ipdb.set_trace()
        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)
        run = my_args.get('run', False)
        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        for op_ in task_obj_uid.operation_ids:
            #si se mueve pause a run no se pone a false to_process
            if not run:
                op_.to_process = False
            op_.visited = False
        task_obj_uid.gun_begin = True
        return True

    @api.multi
    def gun_finish_task(self, my_args):


        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)

        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        task_obj_uid.finish_partial_task()
        return True


