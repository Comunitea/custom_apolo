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
    "name": "Indirect sales",
    "version": "1.0",
    "author": "Comunitea",
    "category": "EDI",
    "website": "www.comunitea.com",
    "description": """Allow to create indirect sales without invoice""",
    "depends": ["sale_stock",
                "midban_depot_stock"], # Because onchange_partner_id
    "data": ["sale_view.xml",
             "respartner_view.xml",
             "stock_view.xml"],
    "installable": True,
    "application": True,
}
