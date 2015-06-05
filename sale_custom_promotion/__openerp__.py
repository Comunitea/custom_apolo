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
    'name': 'Sale custom promotions',
    'version': '1.0',
    'category': 'Sale',
    'description': """""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['base', 'sale', 'rappel'],
    "data": ['sale_promotion_view.xml',
             'tourism_view.xml',
             'rules_view.xml',
             'sale_view.xml',
             'wizard/invoice_joint_promotion_view.xml',
             'wizard/invoice_tourism_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
