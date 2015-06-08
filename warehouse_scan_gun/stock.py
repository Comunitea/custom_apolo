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


class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    visited = fields.Boolean('Visited', default=False)

    @api.multi
    def set_op_visited(self, my_args):
        """
        Mark operation defined in my_args as visited an the check if remaining
        operations in task are visited to return true in order to finish task
        or False because we need to show the next operation.
        """
        # import ipdb; ipdb.set_trace()
        user_id = my_args.get('user_id', False)
        op_id = my_args.get('op_id', False)
        task_id = my_args.get('task_id', False)
        to_process = my_args.get('to_process', False)

        # Browse with correct uid, an mark as visited
        op_obj = self.browse(op_id)
        env2 = op_obj.env(self._cr, user_id, self._context)
        op_obj_uid = op_obj.with_env(env2)
        op_obj_uid.write({'visited': True, 'to_process': to_process})

        # Check if there is more operations to visit
        task_obj = self.env['stock.task'].browse(task_id)
        for op in task_obj.operation_ids:
            if not op.visited:
                return False
        return True
