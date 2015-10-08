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
class reposition_wizard(models.Model):

    _inherit ='reposition.wizard'

    @api.multi
    def create_reposition_from_gun(self, my_args):

        #import ipdb; ipdb.set_trace()

        selected_loc_ids = my_args.get("selected_loc_ids", [])
        limit = my_args.get("limit", 100)
        user_id = my_args.get('user_id', False)
        values = {
            'specific_locations': True,
            'selected_loc_ids':  [(6, 0, selected_loc_ids)],
            'limit': limit,
            'warehouse_id' : 1,
        }
        env2 = self.env(self._cr, 1, self._context)
        wzd_obj= self.with_env(env2)
        wzd_obj_uid= wzd_obj.create(values)

        try:
            res = wzd_obj_uid.get_reposition_list()
        except:
            res = False
        if res:
            picks= res['res_id']
            t_task = self.env["stock.task"].with_env(env2)
            #pausamos la tarea de este usuario
            t_task.search([('user_id','=', user_id), ('paused', '=', False)
                              , ('state','!=','assigned')]).write({'paused':True})
            #creamos una nueva
            vals = {'user_id': user_id,'type': 'reposition',
                    'date_start': time.strftime("%Y-%m-%d %H:%M:%S"),'state': 'assigned',}
            task_id = t_task.create(vals)
            #asignamos las operaciones a la tarea
            t_ops = self.env["stock.pack.operation"].with_env(env2)
            t_ops_pool = t_ops.search([('picking_id','=',picks)])
            res = t_ops_pool.write({'task_id': task_id.id, 'to_process': False})
            if res:
                res=task_id.id
        return res