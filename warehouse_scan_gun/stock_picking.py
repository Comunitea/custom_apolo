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

class stock_picking(models.Model):
    _inherit ='stock.picking'

    @api.multi
    def get_routes_menu(self):

        res = {}
        domain = [('picking_type_id', '=',5), ('validated_state', '=', 'loaded'), ('state', 'not in', ('draft','done','cancel'))]
        route_ids = self.search(domain)#,  order ='name asc')
        if not route_ids:
            res = False
        indx = 1
        name_pool = []
        for x in route_ids:
            name = x.route_detail_id.detail_name_str
            id = x.route_detail_id.id
            if not name in name_pool:
                res[str(indx)] = (id, name)
                name_pool.append(name)
                indx += 1
        return res


    @api.multi
    def get_packs_in_same_picking(self, my_args):

        user_id = my_args.get('user_id', 1)
        package_id = my_args.get ('package_id', False)
        domain = [('state', '=', 'assigned'), ('task_type', '=', 'ubication')]
        pick_pool = self.search(domain)
        res = {}
        vals =[]
        pick_obj= False
        for pick in pick_pool:
            for op in pick_pool.pack_operation_ids:
                if op.package_id.id == package_id:
                    pick_obj = pick
                    break
            if pick_obj:
                break

        if pick_obj:
            res['pick'] = pick_obj.name
            res['pick_id'] = pick_obj.id
            for op in pick_obj.pack_operation_ids:
                vals.append({'id':op.id, 'package':op.package_id.name, 'package_id': op.package_id.id, 'selected':True})
            res['ops']= vals
        return res


    @api.multi
    def create_multipack_from_pick(self, my_args):
        user_id = my_args.get('user_id', 1)
        pick_id= my_args.get ('pick', False)
        ops = my_args.get('ops', [])
        pick_pool = self.browse(pick_id)
        res = False
        ctx = {'lang': 'es_ES', 'tz': 'Europe/Madrid', 'uid': user_id, 'active_id': pick_id}
        self_ = self.env['stock.picking.create.multipack'].with_context(ctx)
        multipack_wzd= self_.create({})
        #multipack_wzd.default_get(['line_ids'])
        vals={}
        new_package_id = self.env['stock.quant.package'].create(vals)

        for line in multipack_wzd.line_ids:
            if line.operation_id.id in ops:
                line.pack_dest_id = new_package_id
            else:
                line.unlink()

        res = multipack_wzd.create_multipack()

        return new_package_id.name

    # @api.multi
    # def do_transfer(self):
    #     """
    #     Overwrited print tags
    #     """
    #     # Se impr4men todos los que result_package_id y distinto de pack en destino
    #     package_ids=[]
    #     for pick in self:
    #         for op in pick.pack_operation_ids:
    #             #miramos paquete en destino
    #             location_dest = self.env['stock.location'].browse(op.location_dest_id.id)
    #             pack = location_dest.get_package_of_lot(op.lot_id.id or op.package_id.packed_lot_id.id)
    #             if not pack and op.result_package_id.id:
    #                     package_ids.append (op.result_package_id.id)
    #
    #     print_wzd = self.env['create.tag.wizard']
    #     my_args = {'user_id': 1,'package_ids':package_ids}
    #
    #     res = super(stock_picking, self).do_transfer()
    #
    #     print_wzd.print_from_gun(my_args)