# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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
    'name': 'Account customizations',
    'version': '1.0',
    'category': 'Account',
    'description': """Small customizations to account modules""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['base',
                'account_payment',
                'account_voucher',
                'sale',
                'nan_partner_risk'],
    "data": ["account_payment_view.xml",
             "account_voucher_view.xml",
             'sale_view.xml',
             "res_users_view.xml",
             'views/report_invoice.xml'],
    "installable": True
}
