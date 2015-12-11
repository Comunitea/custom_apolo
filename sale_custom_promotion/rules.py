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
from openerp.tools.float_utils import float_is_zero

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
        res = False
        if not promotion_rule.customer_ids or order.partner_id in \
                promotion_rule.customer_ids or (order.partner_id
                and order.partner_id.parent_id in promotion_rule.customer_ids):
            res = super(PromotionsRules, self).evaluate(promotion_rule, order)
        return res

    @api.multi
    def get_discount_subgroups(self):
        self.ensure_one()
        subgroups = self.env['product.rappel.subgroup']
        for expression in self.expressions:
            if expression.attribute == 'subgroup':
                code = expression.value.replace("'", "")
                subgroups += self.env['product.rappel.subgroup'].search([('code', '=', code)])
        return subgroups


class PromotionsRulesActions(models.Model):

    _inherit = 'promos.rules.actions'

    action_type = fields.Selection(selection_add=[('prod_disc_perc_sub',
                                                   'Discount % on Product of \
subgroup')])

    def action_prod_disc_perc(self, cr, uid,
                               action, order, context=None):
        """
        Action for 'Discount % on Product'
        @param cr: Database cr
        @param uid: ID of uid
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        order_line_obj = self.pool.get('sale.order.line')
        for order_line in order.order_line:
            if order_line.product_id.code == eval(action.product_code)\
                    and float_is_zero(order_line.discount, precision_digits=2)\
                    and not order_line.tourism:
                return order_line_obj.write(cr,
                                     uid,
                                     order_line.id,
                                     {
                                      'discount':eval(action.arguments),
                                      },
                                     context
                                     )

    @api.model
    def action_prod_disc_perc_sub(self, action, order):
        order_line_obj = self.env['sale.order.line']
        for order_line in order.order_line:
            if order_line.product_id.rappel_subgroup_id.code == \
                    eval(action.product_code) \
                    and float_is_zero(order_line.discount, precision_digits=2)\
                    and not order_line.tourism:
                order_line.write({'discount': eval(action.arguments)})

    @api.model
    def create_line(self, args):
        args['price_udv'] = args.get('price_unit')
        if args.get('product_id', False):
            lines = self.env['sale.order.line'].search(
                [('product_id', '=', args.get('product_id')),
                 ('order_id', '=', args.get('order_id'))])
            args['product_uos'] = lines[0].product_uos.id
            qty = lines[0].product_id.uom_qty_to_uos_qty(args.get('product_uom_qty'), lines[0].product_uos.id)
            args['product_uos_qty'] = qty
        else:
            args['product_uos'] = args.get('product_uom')
            args['product_uos_qty'] = args.get('product_uom_qty')
        return super(PromotionsRulesActions, self).create_line(args)

class PromotionsRulesConditionsExprs(models.Model):

    _inherit = 'promos.rules.conditions.exps'

    attribute = fields.Selection(selection_add=[('subgroup',
                                                 'Rappel subgroup')])

    @api.model
    def evaluate(self, expression, order):
        products = []   # List of product Codes
        product_ids = []   # List of product ids
        prod_qty = {}   # Dict of product_code:quantity
        prod_unit_price = {}
        prod_sub_total = {}
        prod_discount = {}
        prod_weight = {}
        prod_net_price = {}
        prod_lines = {}
        if expression.attribute == 'subgroup':
            subgroup_products = self.env['product.product'].search(
                [('rappel_subgroup_id.code', '=',
                 eval(expression.value))])._ids
        for line in order.order_line:
            if line.product_id and not line.tourism:
                product_code = line.product_id.code
                products.append(product_code)
                product_ids.append(line.product_id.id)
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

    def serialise(self, attribute, comparator, value):
        if attribute == 'subgroup':
            return 'bool(len([x for x in product_ids if x in subgroup_products]))'
        return super(PromotionsRulesConditionsExprs, self).serialise(
            attribute, comparator, value)
