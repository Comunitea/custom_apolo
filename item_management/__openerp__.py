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
    'name': 'Physical items management',
    'description': "Allow to manage the movements of phisical items.",
    'version': '1.0',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'depends': ['base',
                'stock',
                'l10n_es_account_asset'],
    'data': ["data/item_contract_sequence.xml",
             "security/ir.model.access.csv",
             "wizard/assign_item_tocontract_view.xml",
             "wizard/item_deactivate_view.xml",
             "wizard/item_internal_move_view.xml",
             "item_contract_view.xml",
             "item_count_view.xml",
             "item_view.xml",
             "report/report_header.xml",
             "report/item_contract_report.xml",
             "report/item_remove_report.xml",
             "item_management_report.xml"],
    'active': False,
    'installable': True,
}
