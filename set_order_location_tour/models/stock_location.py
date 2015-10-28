# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Informáticos All Rights Reserved
#    $Javier Colmenero Fernández$ <javier@comunitea.com>
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


class StockLocation(models.Model):

    _inherit = "stock.location"

    xy_camera = fields.Char(compute='_get_coordinates_names', string="Camera",
                            readonly=True, store=True)
    xy_aisle = fields.Char(compute='_get_coordinates_names', string="Aisle",
                          readonly=True, store=True)
    xy_column = fields.Char(compute='_get_coordinates_names', string="Column",
                            readonly=True, store=True)
    xy_height = fields.Char(compute='_get_coordinates_names', string="Height",
                            readonly=True, store=True)

    @api.multi
    @api.depends('bcd_name')
    def _get_coordinates_names(self):
        for loc in self:
            loc.xy_camera = ""
            loc.xy_aise = ""
            loc.xy_column = ""
            loc.xy_height = ""
            if loc.bcd_name:
                bcd_name_parts = loc.bcd_name.split(" ")
                if len(bcd_name_parts) != 4:
                    continue  # Not set if no correct format
                loc.xy_camera = bcd_name_parts[0]
                loc.xy_aisle = bcd_name_parts[1]
                loc.xy_column = bcd_name_parts[2]
                loc.xy_height = bcd_name_parts[3]
