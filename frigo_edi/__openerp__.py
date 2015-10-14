# -*- coding: utf-8 -*-
##############################################################################
#
#    Omar Castiñeira Saavedra Copyright Comunitea SL 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    "name": "Frigo EDI",
    "version": "1.0",
    "author": "Comunitea",
    "category": "EDI",
    "website": "www.comunitea.com",
    "description": """* This module implements Frigo's EDI""",
    "depends": ["depot_edi",
                "midban_partner",
                "item_management",
                "stock",
                "indirect_sale"],
    "data": ["wizard/frigo_edi_wzd.xml",
             "views/res_partner_view.xml",
             "views/edi_menu.xml",
             "views/partner_sync_view.xml",
             "views/sale_export_edi_view.xml",
             "views/res_company_view.xml",
             "security/ir.model.access.csv",
             "data/frigo_edi_data.xml",
             "views/item_move_sync_view.xml",
             "views/item_view.xml",
             "views/edi_view.xml",
             "views/partner_competence_view.xml",
             "views/stock_view.xml",
             "views/res_currency.xml",
             "views/preferential_agreement_view.xml",
             "views/product_unilever_family_view.xml"],
    "installable": True,
    "application": True,
}
