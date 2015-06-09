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
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class StockTask(models.Model):
    _inherit = 'stock.task'

    @api.multi
    def get_location_gun_operations(self, my_args):
        """
        Get a location task for a user defined in my args.
        """
        user_id = my_args.get('user_id', False)
        camera_id = my_args.get('camera_id', False)
        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned')
        ]
        task_obj = self.search(domain)
        if task_obj:
            print "Te doy la que tenias"
            return task_obj.id

        vals = {
            'operator_id': user_id,
            'machine_id': False,
            'location_ids': [(4, camera_id, 0)],

            'mandatory_camera': True,
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
        wzd_obj_uid.get_location_task()
        domain = [
            ('user_id', '=', user_id),
            ('state', '=', 'assigned')
        ]
        task_obj = self.search(domain)
        if not task_obj:
            raise except_orm(_("Error"), _("Task not founded after create it"))
        for op in task_obj.operation_ids:
            op.write({'visited': False})
        print "te doy una creada"
        return task_obj.id

    @api.multi
    def get_op_data(self, my_args):
        """
        Return data for next operation not visited.
        """
        # user_id = my_args.get('user_id', False)
        task_id = my_args.get('task_id', False)
        task_obj = self.browse(task_id)
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
                'ORIGEN': op.location_id.name,
                'DESTINO': op.location_dest_id.name,
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
        # import ipdb; ipdb.set_trace()
        for op in task_obj.operation_ids:
            if op.id == op_id:
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
    def gun_finish_task(self, my_args):
        task_id = my_args.get('task_id', False)
        user_id = my_args.get('user_id', False)

        task_obj = self.browse(task_id)
        env2 = task_obj.env(self._cr, user_id, self._context)
        task_obj_uid = task_obj.with_env(env2)

        task_obj_uid.finish_partial_task()
        return True
