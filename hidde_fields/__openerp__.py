# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
    'name': 'Hidde unnused fields',
    'version': '1.0',
    'category': 'product',
    'description': """""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['base', 'product', 'purchase', 'sale', 'midban_product',
                'midban_depot_stock', 'price_system_variable',
                'midban_ultra_fresh'],
    "data": ['security/hidde_security.xml', 'product_view.xml',
             'purchase_view.xml', 'sale_view.xml'],
    "installable": True
}
