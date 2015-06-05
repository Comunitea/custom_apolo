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


class PromotionsRules(models.Model):

    _inherit = 'promos.rules'

    customer_ids = fields.Many2many(
        'res.partner',
        'partner_rules_rel',
        'rule_id',
        'partner_id',
        'Customers')

    @api.model
    def evaluate(self, promotion_rule, order):
        res = super(PromotionsRules, self).evaluate(promotion_rule, order)
        if res and promotion_rule.customer_ids and order.partner_id not in \
                promotion_rule.customer_ids:
            return False
        return res


class PromotionsRulesConditionsExprs(models.Model):

    _inherit = 'promos.rules.conditions.exps'

    @api.model
    def evaluate(self, expression, order):
        products = []   # List of product Codes
        prod_qty = {}   # Dict of product_code:quantity
        prod_unit_price = {}
        prod_sub_total = {}
        prod_discount = {}
        prod_weight = {}
        prod_net_price = {}
        prod_lines = {}
        for line in order.order_line:
            if line.product_id and not line.tourism:
                product_code = line.product_id.code
                products.append(product_code)
                prod_lines[product_code] = line.product_id
                prod_qty[product_code] = prod_qty.get(product_code, 0.00) + \
                    line.product_uom_qty
#                prod_net_price[product_code] = prod_net_price.get(
#                                                    product_code, 0.00
#                                                    ) + line.price_net
                prod_unit_price[product_code] = prod_unit_price.get(
                    product_code, 0.00) + line.price_unit
                prod_sub_total[product_code] = prod_sub_total.get(product_code,
                                                                  0.00) + \
                    line.price_subtotal
                prod_discount[product_code] = prod_discount.get(product_code,
                                                                0.00) + \
                    line.discount
                prod_weight[product_code] = prod_weight.get(product_code,
                                                            0.00) + \
                    line.th_weight
        return eval(expression.serialised_expr)
