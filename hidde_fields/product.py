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
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    price_kg = fields.Float('Price Kg',
                            groups='hidde_fields.group_show_unnused')
    sec_margin = fields.Float('Security Margin', readonly=True,
                              digits_compute=dp.get_precision
                              ('Product Price'),
                              groups='hidde_fields.group_show_unnused')
    margin = fields.Float('Margin ', groups='hidde_fields.group_show_unnused')
    cmc = fields.Float('CMC', digits_compute=dp.get_precision('Product Cost'),
                       readonly=True, groups='hidde_fields.group_show_unnused')
    mes_type = fields.Selection((('fixed', 'Fixed'), ('variable', 'Variable')),
                                'Measure Type',
                                groups='hidde_fields.group_show_unnused')
