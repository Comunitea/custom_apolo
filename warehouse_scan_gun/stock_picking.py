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
        warehouse = self.env['stock.warehouse'].search([('pick_type_id', '!=', False)])
        pick_type_ids= []
        for wh in warehouse:
            pick_type_ids.append (wh.pick_type_id.id)
        domain = [('picking_type_id', 'in',pick_type_ids),('pack_operation_ids', '!=', False),
                  ('validated_state', '=', 'loaded'), ('state', 'not in', ('draft','done','cancel'))]
        route_ids = self.search(domain, order = 'route_detail_id')#.detail_name_str')#,  order ='name asc')
        if not route_ids:
            res = False
        indx = 1
        name_pool = []
        for x in route_ids:
            transporter = x.route_detail_id.comercial_id.name or False
            name = x.route_detail_id.detail_name_str
            id = x.route_detail_id.id
            ops_to_process = 0# self.get_free_waves(id)
            print u"Nombre Ruta: %s para %s "%(name, transporter)
            # print u"%s > Nombre para id=%s: %s >> %s (%s)"\
            #       %(indx, x.route_detail_id.id, x.route_detail_id.comercial_id.name, x.route_detail_id.detail_name_str, ops_to_process)
            # name_ = name_.replace(' ', '-')
            # name_ = name_.split("-")
            # if len(name_) == 4:
            #     route, year, month, day =  name_
            #     name = u"%s %s %s"%(route, day, month)
            # else:
            #     name = x.route_detail_id.detail_name_str or "Sin Nombre"

            if not name in name_pool:
                res[str(indx)] = (id, name, transporter, ops_to_process)
                name_pool.append(name)
                indx += 1

        return res

    def get_free_waves(self, route_id):

        pick_obj = self.env['stock.picking']
        # wave_obj = self.env['stock.picking.wave']
        # task_obj = self.env["stock.task"]
        # oper_obj = self.pool.get("stock.pack.operation")
        warehouse = self.env['stock.warehouse'].search([('pick_type_id', '!=', False)])
        pick_type_ids= []
        for wh in warehouse:
            pick_type_ids.append (wh.pick_type_id.id)

            domain = [('picking_type_id', 'in', pick_type_ids),
                      ('route_detail_id', '=', route_id),
                      ('state', 'not in', ('draft','done','cancel')),
                      ('validated_state', '=', 'loaded')
                      ]

        pickings_to_wave = pick_obj.search(domain)
        ops_to_process = 0
        for pick in pickings_to_wave:
            domain = [('to_process', '=', False), ('picking_id', '=', pick.id),('task_id', '=', False)]
            ops_to_process += len(self.env['stock.pack.operation'].search(domain))

        return ops_to_process



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