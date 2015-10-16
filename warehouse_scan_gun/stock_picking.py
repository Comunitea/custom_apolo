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
        #import ipdb; ipdb.set_trace()
        res = {}
        domain = [('picking_type_id', '=',5), ('validated', '=', True), ('state', 'not in', ('draft','done','cancel'))]
        route_ids = self.search(domain, order ='route_detail_id, orig_planned_date, min_date, name asc')
        if not route_ids:
            res = False
        #routes_pool = self.env['']
        indx = 1
        before = False
        for x in route_ids:
            if before == x.route_detail_id.id:
                continue
            res[str(indx)] = (x.route_detail_id.id, x.route_detail_id.detail_name_str)
            indx += 1
        return res