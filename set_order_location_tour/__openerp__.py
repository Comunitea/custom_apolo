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

{
    "name": "Set Order Locations Tour",
    "version": "1.0",
    "author": "Comunitea",
    "category": "Custom",
    "website": "www.comunitea.com",
    "description": """
    Provides a way of set the order of stock locations generating a special
    number over the sequence field and provides a way of seting the sequence.
    """,
    "images": [],
    "depends": [
        "stock",
        "warehouse_scan_gun",  # Because BCD code
        "midban_depot_stock",  # Because sequence field, camera, picking zone
    ],
    "data": [
        'views/stock_location_view.xml',
        'wizard/wizard_order_locations_view.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
}
