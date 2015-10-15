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
from openerp.osv import osv

class StockLocation(osv.osv):

    _inherit = "stock.location"

    def _complete_name (self, cr, uid, ids, name, args, context=None):
        #no funciona
        #import ipdb; ipdb.set_trace()
        res = super(stock_location, self)._complete_name(cr, uid, ids, name, args, context=None)
        for m in self.browse(cr, uid, ids, context=context):
            if len(m.bcd_code)==11:
                res[m.id] = m.name
                parent = m.location_id
                while parent:
                    res[m.id] = parent.location_id.name + ' / ' + res[m.id]
                    parent = parent.location_id
            return res


class stock_location(models.Model):

    _inherit = "stock.location"
    #no funciona
    _rec_name = "bcd_name"

    bcd_name = fields.Char ("C.D.B. Name")
    bcd_code = fields.Char("C.D.B. Code", size=25)

    @api.multi
    def get_short_name(self):
        short_name = self.name
        zone ="V"
        if self.zone == 'storage':
            zone = "A"
        if self.zone == 'picking':
            zone = "P"
        short_name = zone + '/' + self.name
        return short_name

    @api.multi
    def is_location_free(self, my_args):
        location_id = my_args.get("location_id", False)
        domain = [('loc_id','=', location_id)]
        packs=self.env['stock.quant'].search(domain)
        busy = False
        if packs:
            busy = True
        domain = [('location_dest_id', '=', location_id),
                  ('processed', '=', 'false'),
                  ('picking_id.state', 'in', ['assigned'])]
        ops=self.env['stock.pack.operation'].search(domain)
        if ops:
             busy = True
        return busy

    @api.multi
    def get_parent_location(self, my_args):
        location_id = my_args.get("location_id", False)
        parent_loc = self.browse[location_id]
        res = False
        if parent_loc:
            res = parent_loc.parent_id.id

        return res

    @api.multi
    def get_location_gun_info(self, my_args):
        #import ipdb; ipdb.set_trace()

        #import ipdb; ipdb.set_trace()

        location_id = my_args.get("location_id", False)
        bcd_code = my_args.get('bcd_code', False)
        if location_id:
            domain = [('id', '=', location_id)]
        elif bcd_code:
            domain= [('bcd_code', '=', bcd_code)]

        type = my_args.get("type", '')
        if type == 'picking':
            #se busca para hacer un picking, con lo que vale de id o delocation:_id
            domain.append(('location_id','=',location_id))

        location = self.search(domain, order = 'id desc')

        location_child_ids = self.search([('location_id', '=', location.id)])
        child = len(location_child_ids)
        childs = False
        if child:
            childs= []
            for loc in location_child_ids:
                childs.append({'bcd_name': loc.bcd_name,
                               'id': loc.id})
        vals = {'exist':False}
        if location:
            vals = {
                'exist' : True,
                type or '' + 'location_id' : location.id,
                type or '' + 'location' : location.name_get()[0][1],
                'usage':location.usage,
                'zone':location.zone,
                'temp_type_id':location.temp_type_id.id or False,
                'bcd_name': location.bcd_name,
                'parent_id': location.location_id.id or False,
                'childs': childs,
            }

        return vals

    @api.multi
    def get_subpicking_zones(self, my_args):
        location_id = my_args.get("location_id", False)
        bcd_code = my_args.get('bcd_code', False)
        domain = False
        if not location_id:
            domain= [('bcd_code', '=', bcd_code)]
            location_id = self.search(domain).id

        domain = [('location_id', '=', location_id)]
        location_ids = self.search(domain)
        res = []
        if location_ids:
            for loc in location_ids:
                res.append ({'id': loc.id,
                             'loc.bcd_name': loc.bcd_name
                             })
        return res

    @api.multi
    def create_picking_sublocation_from_gun(self, my_args):
        pick_zone_id = my_args.get('pick_zone_id', False)
        sub_cols = my_args.get('sub_cols', 0)
        new_loc_ids = self.create_picking_sublocation(pick_zone_id, sub_cols)
        new_locs=[]
        if new_loc_ids:
            for loc in self.search([('id', 'in', new_loc_ids)]):
                new_locs.append({'id': loc.id,'name': loc.bcd_name})
        return new_locs

    @api.multi
    def create_picking_sublocation(self, pick_zone_id, subcolumns):

        #Esta función crea subloc de picking, false si el id no es de picking o no la encuentra
        pick = self.search([('id', '=' , pick_zone_id)])
        new_loc_ids=[]
        if not pick:
            return False
        if pick.zone != 'picking':
            return False
        vals = {
            'usage': 'internal',
            'temp_type_id': pick.temp_type_id.id,
            'width': float(pick.width/subcolumns),
            'length': pick.length,
            'height': pick.height,
            'name': pick.name,
            'location_id': pick.id,
            'zone': 'picking',
            'bcd_code': False, #bcd_code + fila + altura,
            'bcd_name': False, #u'%s %s %s'%(bcd_name, fila, altura),
            'vagon':pick.vagon
        }
        for sub_cols in range(1,subcolumns+1):
            sub_cols_strg = '0' + str(sub_cols)
            vals['name']=u'%s%s%s'%(pick.name, '/', sub_cols)
            vals['bcd_code'] = pick.bcd_code + sub_cols_strg
            vals['bcd_name'] = pick.bcd_name + ' ' + sub_cols_strg
            created_loc = self.env['stock.location'].create(vals)
            new_loc_ids.append(created_loc.id)

        #ADEMAS UNA VEZ CREADO, LA ZONADEBE PASARSE A USAGE = VIEW
        pick.write ({'usage': 'view'})

        #todos los paquetes pasan a la subzona 1 por defecto
        # domain = [('loc_id','=', pick_zone_id)]
        # packs=self.env['stock.quant'].search(domain)
        # packs.write ({'loc_id', '=',new_loc_ids[0]})
        #
        # #todos las ops se con ese destino se pasan al nuevo
        # domain = [('location_dest_id', '=', pick_zone_id),
        #           ('processed', '=', 'false'),
        #           ('picking_id.state', 'in', ['assigned'])]
        # ops=self.env['stock.pack.operation'].search(domain)
        # ops.write ({}'')
        # if ops:
        #      busy = True
        # return busy



        return new_loc_ids