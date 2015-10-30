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


# class StockCameraOrder(models.Model):
#
#     _name = "stock.camera.order"
#     _description = "Sets order of Cameras"
#
#     xy_camera = fields.Char("Camera")
#     aisle_order_ids = fields.One2many('stock.aisle.order', 'ord_cam_id',
#                                       "Aisle Order")
#     sequence = fields.Integer("Order")
#
#
# class StockAisleOrder(models.Model):
#
#     _name = "stock.aisle.order"
#     _description = "Sets order of Cameras"
#
#     ord_cam_id = fields.many2one('stock.camera.order', 'Order Camera')
#     xy_aisle = fields.Char("Camera")
#     orientation = fields.Selection([('pos', 'Positive'), ('neg', 'Negative')],
#                                    'Orentation')
#     sequence = fields.Integer("Order")
