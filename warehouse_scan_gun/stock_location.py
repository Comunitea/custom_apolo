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

class stock_location(models.Model):

    _inherit = "stock.location"

    def saca_cod(self, camara, fila):
        if camara ==1:
            op = {
            1:"01001",
            2:"01002",
            3:"01003",
            4:"0101B",
            5:"0102B",
            6:"0101A",
            7:"0103B",
            8:"0102A",
            9:"0104B",
            10:"0103A",
            11:"0104A",
            12:"0105B",
            13:"0105A",
        }
        if camara ==2:
            op = {
            1:"02200",
            2:"02001",
            3:"02002",
            4:"02003",
            5:"02004"
            }
        if camara ==3:
            op = {
            1:"03001",
            2:"03002",
            3:"03003"}
        if camara ==4:
            op = {
            1:"04401",
            2:"0401B",
            3:"0401A",
            }
        if camara ==5:
            op = {
            1:"0500A",
            2:"0500B",
            3:"0500C",
            4:"0500D",
            5:"05010"}
        try:
            res = op[fila]
        except:
            res = False

        return res


    @api.multi
    def get_old_name(self):
        loc_pool = self.env["stock.location"]
        domain= [('|'), ('zone' ,'=', 'picking'), ('zone', '=', 'storage'),
                 ('usage','=', 'internal'), ('special_location','=', False)]
        ubis = loc_pool.search(domain)
        for loc in ubis:
            strg_cam = "0" + loc.location_id.name[1:2]
            spl = loc.name.split("/")
            old_name = False
            if len(spl)>0:
                strg_cod= self.saca_cod(int(strg_cam), int(spl[0]))
                strg_row = "0" * (2-len(spl[1])) + spl[1]
                if len(spl)==2:
                    strg_altura = "01"
                else:
                    strg_altura = "0" * (2-len(spl[2])) + spl[2]

                cdb_name = strg_cod + strg_row + strg_altura
            else:
                old_name = loc.name

            loc.write({'bcd_name' : old_name})
        return

    bcd_name = fields.Char ("C.D.B. Name")

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
    def get_location_gun_info(self, my_args):
        location_id = my_args.get("location_id", False)
        domain = [('id', '=', location_id)]
        type = my_args.get("type", "")
        location = self.search(domain)
        vals = {'exist':False}
        if location:
            vals = {
                'exist' : True,
                type + 'location_id' : location.id,
                type + 'location' : location.name_get()[0][1],
                'usage':location.usage,
                'zone':location.zone,
                'temp_type_id':location.temp_type_id.id or False,
            }
        return vals
