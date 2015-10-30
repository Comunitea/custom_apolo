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
                    pack.append (op.result_package_id)
                    my_args ={
                        'package_ids': pack,
                        'user_id':user_id
                    }
                    res = self.print_from_gun(my_args)




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
        t_wzd = self.env['create.tag.wizard'].with_context(context)
        new_wzd = t_wzd.create(vals)
        res = False
        ids = []
        for package_id in package_ids:
            package = self.env['stock.quant.package'].search([('id','=',package_id)])
            if package:
                val = {'package_id' : package.id,
                       'product_id':package.product_id.id or package.quant_ids[0].product_id.id,
                       'default_code':package.product_id.default_code or package.quant_ids[0].product_id.default_code,
                       'lot_id': package.packed_lot_id.id and \
                        package.quant_ids[0].lot_id.id,
                       'wizard_id': new_wzd.id,
                       'removal_date': package.quant_ids[0].lot_id.removal_date,
                       }
                res = new_wzd.write({'tag_ids': [(0,0, val)]})

        if res:

            ctx = dict(context)

            report = self.pool.get('report')
            report.print_document(self._cr, user_id, [12], 'midban_depot_stock.report_stock_tag')

        #
        #     report.with_context(ctx).print_document(self.env['stock.location'].browse([9419]), 'stock.report_location_barcode')
        #
        #
        #
        #
        #
        #
        #     ids=[]
        #     ids.append(new_wzd[0].id)
        #     self.print_tags(ids)
        #     tag_ids=[]
        #     t_tag = self.env['tag']
        #     for item in new_wzd.tag_ids:
        #         vals = {
        #             'product_id': item.product_id.id,
        #             'default_code': item.default_code or False,
        #             'lot_id': item.lot_id and item.lot_id.id or False,
        #             'removal_date': item.removal_date,
        #             'package_id': item.package_id and item.package_id.id or False
        #         }
        #         tag_ids.append(t_tag.create(vals))
        # ctx = dict(context)
        # ctx['active_ids'] = tag_ids
        # ctx['active_model'] = 'tag'
        # new_wzd.write({'printed': True})
        # return self.pool.get("report").get_action(cr, uid, [],'midban_depot_stock.report_stock_tag', context=ctx)
        # report_ = self.env['report'].with_context(ctx)
        #
        # report.get_action ('midban_depot_stock.report_stock_tag')

        return res
