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
from openerp import sql_db
import threading
import time
import logging
_logger = logging.getLogger(__name__)

class StockTask(models.Model):
    _inherit = 'stock.task'

    @api.multi
    def create_task_from_gun(self, my_args):

        user_id = my_args.get('user_id', False)
        from_gun = True
        task_obj = self.env['stock.task']
        env2 = task_obj.env(self._cr, user_id, self._context)
        new_task = task_obj.with_env(env2)
        vals = {
            'user_id': user_id,
            'from_gun': True
        }
        task_id = new_task.create(vals)

        return task_id.id

    @api.multi
    def add_loc_operation_from_gun(self, my_args):

        user_id = my_args.get('user_id', False)
        pack_id = my_args.get('pack_id', False)
        task_id = my_args.get('task_id', False)
        from_gun = True
        domain = [('id', '=', task_id)]
        task_obj = self.env['stock.task'].search(domain)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task = task_obj.with_env(env2)
        message = ''
        op_id = False
        try:
            op_id = task.add_loc_operation (pack_id)
        except:
            message = u'paquete no encontrado'
        return op_id, message

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

        task_obj = self.search([('user_id', '=', user_id), ('paused', '=', False)])
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)
        task_obj_uid.write ({'paused':True})

        if not pause_state:
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
        ref =''
        for task in task_obj:
            if task.operation_ids:
                ref = task.operation_ids[0].picking_id.name
            if task.type == 'picking':
                num_ops = len(task.wave_id.wave_report_ids)
            else:
                num_ops = len(task.operation_ids)
            values = {
                'id': task.id,
                'type' : task.type,
                'paused' : task.paused,
                'ref' : task.wave_id.name or task.picking_id.name or ref or '',
                'ops': num_ops,
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
        date_planned= my_args.get('date_planned', False)
        route_id= my_args.get('route_id', False)
        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned'),
            ('paused', '=', False),
        ]
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': user_id}
        self_ = self.env['stock.task'].with_context(ctx)
        task_obj = self.search(domain).with_context(ctx)
        if task_obj:
            print "Te doy la que tenias"
            return task_obj.id
        trans_route_id = False
        if route_id:
            route_detail= self.env['route.detail'].search([('id', '=', route_id)])
            date_planned= route_detail.date
            route_id = route_detail.route_id.id

        vals = {
            'operator_id': user_id,
            'machine_id': machine_id,
            'location_ids': [],
            'mandatory_camera': False,
            'print_report': False,
            #'date_planned':date_planned,
            'trans_route_id':route_id,
            'date_planned': date_planned,
            'max_loc_ops': 12,
            'min_loc_replenish': 5,
            'location_ids': [(6, 0, camera_id)]
            # 'warehouse_id':
            # 'trans_route_id':
            # 'date_planned':
        }
        t_wzd = self.env['assign.task.wzd'].with_context(ctx)
        # CHANGUING USER ID t_wzd.sudo(user_id) no funciona

        env2 = t_wzd.env(self._cr, user_id, ctx)
        wzd_obj= t_wzd.with_env(env2)
        wzd_obj_uid= wzd_obj.create(vals)
        #for camera in camera_id:
        #    wzd_obj_uid.location_ids =[(4, camera, 0)]

        if task_type == 'ubication':
            wzd_obj_uid.get_location_task()
        elif task_type == 'reposition':
            wzd_obj_uid.get_reposition_task()
        elif task_type == 'picking':
            task_id = wzd_obj_uid.with_context(gun=True).get_picking_task()

        print "te doy una creada: Id" +str(task_id)
        return task_id

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
                'product': op.product_id and op.product_id.name or "",
                'CANTIDAD': str(op.product_qty),
                'lot': op.packed_lot_id and op.packed_lot_id.name or "",
                'PAQUETE': op.package_id and op.package_id.name or "",
                'ORIGEN': op.location_id.bcd_name,
                'DESTINO': op.location_dest_id.bcd_name,
                'PROCESADO': op.to_process,
                'VISITED' :op.visited,
                'origen_id': op.location_id.id,
                'destino_id': op.location_dest_id.id,
                'pack_id': op.package_id.id,
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
        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)
        run = my_args.get('run', False)
        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        for op_ in task_obj_uid.operation_ids:
            #si se mueve pause a run no se pone a false to_process
            #if not run:
                #op_.to_process = False
            op_.visited = False

        return True

    @api.multi
    def gun_finish_task(self, my_args):
        #new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        task_id = my_args.get('task_id', False)
        task_obj = self.browse(task_id)
        task_obj.write({'state':'process'})
        uid, context = self.env.uid, self.env.context
        thread = threading.Thread(
            target=self._gun_finish_task, args=(my_args,))
        thread.start()
        return True

    @api.model
    def _gun_finish_task(self, my_args):
        _logger.debug("CMNT ENTRA EN EL HILO!!!!!!!!! args %s",
                       my_args)
        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        with api.Environment.manage():  # class function
            uid, context = self.env.uid, self.env.context
            env = api.Environment(new_cr, user_id, context)
            #self.env = env
            task_obj = env['stock.task'].browse(task_id)
            #env2 = task_obj.env(self._cr, user_id, self._context)
            #task_obj_uid = task_obj.with_env(env2)
            try:
                res = task_obj.finish_partial_task()
            except Exception:
                _logger.debug("CMNT EXCEPCION EN EL HILO!!!!!!!!! args %s",
                       Exception)
                new_cr.rollback()
                new_cr.close()
            new_cr.commit()
            new_cr.close()
            return {}

    @api.multi
    def gun_cancel_task(self, my_args):

        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)

        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        task_obj_uid.cancel_task()
        return True

    @api.multi
    def gun_finish_picking_task(self, my_args):

        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)

        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        task_obj_uid.finish_partial_task()
        return True

    from_gun = fields.Boolean("Created from gun", default = "False")
