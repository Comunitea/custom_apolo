# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Informáticos All Rights Reserved
#    $Carlos Lombardía Rodríguez$ <carlos@comunitea.com>
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
    "name": "Custom Documents",
    "version": "1.0",
    "author": "Comunitea",
    "category": "Custom",
    "website": "www.comunitea.com",
    "description": """

    """,
    "images": [],
    "depends": [
        "stock_valued_picking",
        "stock_picking_review",
        "stock_picking_batch",
        "depot_invoice",
        "process_sale_order",
        "stock",
        "account",
        "midban_product",
        "midban_partner",
    ],
    "data": ['views/res_partner_view.xml',
             #  'views/custom_assets.xml', NO ME FUNCIONA en esta revision
             'views/custom_reports.xml',
             'views/res_users_view.xml',
             'views/res_partner_view.xml',
             'qweb_report/report_custom_picking.xml',
             'qweb_report/report_custom_picking_batch.xml',
             'qweb_report/report_custom_invoice.xml',
             'qweb_report/report_purchase_order.xml'],
    "demo": [],
    "test": [],
    "installable": True,
}
