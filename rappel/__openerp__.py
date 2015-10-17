# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
    "name": "Rappel management",
    "author": "Pexego",
    "category": "Sale",
    "website": "www.pexego.es",
    "description": """
Rappel Management
=====================================================

    """,
    "images": [],
    "depends": ["base",
                "sale",
                "account",
                "stock",
                "purchase",
                "product",
                "sale_custom_promotion",
                ],
    "data": ["security/rappel_security.xml",
             "rappel_type_view.xml",
             "res_partner_view.xml",
             "sale_promotion_view.xml",
             "wizard/calculate_rappel_wizard.xml",
             "wizard/invoice_rappel_wizard.xml",
             "rappel_view.xml",
             "rappel_menus.xml",
             "security/ir.model.access.csv"],
    "demo": [],
    "test": [],
    "installable": True,
    "application": True,
}
