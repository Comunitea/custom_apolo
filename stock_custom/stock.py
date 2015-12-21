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


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    supplier_ref = fields.Char(compute='_get_supplier_reference',
                               search='_search_supp_ref', readonly=1)

    @api.model
    def _search_supp_ref(self, operator, operand):
        sales = self.env['sale.order'].search([('supplier_ref', operator,
                                                operand)])
        return [('group_id', 'in', [x.procurement_group_id.id for x in sales])]

    @api.multi
    def _get_supplier_reference(self):
        for pick in self:
            pick.supplier_ref = pick.sale_id.supplier_ref
