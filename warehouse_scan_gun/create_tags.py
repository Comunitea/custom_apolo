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
        for package_id in package_ids:
            package = self.env['stock.quant.package'].search([('id','=',package_id)])
            if package.product_id:
                val = {'package_id' : package.id,
                       'product_id':package.product_id.id,
                       'default_code':package.product_id.default_code,
                       'lot_id': package.quant_ids and \
                        package.quant_ids[0].lot_id and \
                        package.quant_ids[0].lot_id.id,
                       'wizard_id': new_wzd.id,
                       'removal_date': package.quant_ids[0].lot_id.removal_date,
                       }
                res = new_wzd.write({'tag_ids': [(0,0, val)]})
        if res:
            tag_ids=[]
            t_tag = self.env['tag']
            for item in new_wzd.tag_ids:
                vals = {
                    'product_id': item.product_id.id,
                    'default_code': item.default_code or False,
                    'lot_id': item.lot_id and item.lot_id.id or False,
                    'removal_date': item.removal_date,
                    'package_id': item.package_id and item.package_id.id or False
                }
                tag_ids.append(t_tag.create(vals))

            ctx = dict(context)
            report = self.env['report']
            report.print_document(tag_ids[0], 'midban_depot_stock.report_stock_tag')
        return res
