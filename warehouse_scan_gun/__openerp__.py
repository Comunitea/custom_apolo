# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Javier Colmenero Fernández <javier@comunitea.com>$
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
    'name': 'Warehouse Scan Gun',
    'version': '1.0',
    'category': 'Account',
    'description': """Module to manage the warehouse with a scan gun""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['base',
                'midban_depot_stock',
                'base_report_to_printer'],

    "data": [
        "res_users_view.xml",
        "wave_report_revised.xml",
        "wave_report.xml",
        "product_view.xml",
        "stock_location.xml",
        'security/ir.model.access.csv',
        "data/stock_location.xml"],
    "installable": True
}
