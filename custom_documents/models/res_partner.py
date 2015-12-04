# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Informáticos All Rights Reserved
#    $Carlos Lombardía Rodríguez$ <carlos@comunitea.com>
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
from openerp import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    INV_PRINT_OPTIONS = [
        ('give_deliver', 'Give in Delivery'),
        ('group_pick', 'Group parent partner, breakdown picks'),
        ('group_by_partner', 'Group parent partner, summary picks'),
    ]
    PICK_PRINT_OPTIONS = [
        ('not_valued', 'Not Valued Picking'),
        ('valued', 'Valued Picking'),
        ('tracked', 'Tracked Picking'),
    ]

    inv_print_op = fields.Selection(INV_PRINT_OPTIONS, 'Invoice Printing',
                                    default="give_deliver")
    pick_print_op = fields.Selection(PICK_PRINT_OPTIONS, 'Pick Printing',
                                     default="not_valued")
    add_summary = fields.Boolean('Add Summary Articles',
                                 help="Add a page to the invoice with the"
                                 " summary of invoiced products")
    supp_name_prod = fields.Boolean('Use supplier names in indirect notes',
                                 help="Use product name of supplier in indirect notes")
    merchantil_info = fields.Text('Mercantil Info.')
