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


class create_tag_wizard(models.TransientModel):
    _inherit = "create.tag.wizard"


    @api.multi
    def print_task_from_gun(self, my_args):

        task_id= my_args.get("task_id", False)
        user_id = my_args.get("user_id", False)
        context = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': user_id}
        task_pool = self.env['stock.task'].with_context(context)
        pack= []
        task = task_pool.search([('id', '=', task_id)])
        if task.type !='picking':
            for op in task.operation_ids:
                if op.result_package_id:
                    pack.append (op.result_package_id.id)
                    my_args ={
                        'package_ids': pack,
                        'user_id':user_id
                    }

        res = self.print_from_gun(my_args)
        return res



    @api.multi
    def print_from_gun(self, my_args):
        package_ids= my_args.get("package_ids", [])
        user_id = my_args.get("user_id", False)
        vals={
            'show_print_report':True,
            'printed': True,
            'tag_exist': True
        }
        context = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': user_id, 'params': {'action': 439}}
        t_wzd = self.env['tag'].with_context(context)
        res = False
        ids = []

        for package_id in package_ids:
            item = self.env['stock.quant.package'].search([('id','=',package_id)])
            if item:
                vals = {
                    'product_id': item.product_id.id or False,
                    'default_code': item.product_id.default_code or "",
                    'lot_id': item.packed_lot_id.id or False,
                    'removal_date': item.packed_lot_id.removal_date,
                    'package_id': item.id or False,
                    'company_id':  self.env['res.partner'].browse([1]).id,


                }
                res=True
                ids.append(t_wzd.create(vals).id)
        if res:
            ctx = dict(context)
            report = self.pool.get('report')
            report.print_document(self._cr, user_id, ids, 'midban_depot_stock.report_stock_tag')

        return res
