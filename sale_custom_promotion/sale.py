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
from datetime import date
from openerp.tools.float_utils import float_compare



class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    tourism = fields.Many2one('tourism.customer', 'Tourism')

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        res = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            line, account_id)
        res['tourism'] = line.tourism.id
        res['promotion_line'] = line.promotion_line
        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        res = super(SaleOrderLine, self).product_id_change(
            cr, uid, ids, pricelist, product, qty=qty, uom=uom,
            qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order,
            packaging=packaging, fiscal_position=fiscal_position, flag=flag,
            context=context)
        if not product or not partner_id:
            return res
        if res.get('value', {}).get('product_uos', False):
            uos = self.pool.get('product.uom').browse(
                cr, uid, res['value']['product_uos'], context)
        else:
            uos = self.pool.get('product.uom').browse(
                cr, uid, uos, context)
        product = self.pool.get('product.product').browse(cr, uid, product,
                                                          context)
        unit_price = res['value']['price_unit']
        tourism_ids = self.pool.get('tourism.customer').search(
            cr, uid, [('customer_id', '=', partner_id),
                      ('tourism_id.date_start', '<=', date.today()),
                      ('tourism_id.date_end', '>=', date.today()),
                      ('tourism_id.id', 'in', product.tourism_ids._ids),
                      ('tourism_id.state', '=', 'approved')],
            context=context)
        if tourism_ids:
            tourism = self.pool.get('tourism.customer').browse(cr, uid,
                                                               tourism_ids[0],
                                                               context)
            if tourism and unit_price != tourism.get_box_price(product):

                res['value']['price_unit'] = tourism.get_box_price(product)
                res['value']['discount'] = 0
                res['value']['tourism'] = tourism.id
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.tourism:
            if float_compare(res.price_unit * (res.discount and res.discount
                / 100 or 1), res.tourism.get_box_price(res.product_id),
                             precision_digits=2) == -1:
                raise exceptions.Warning(_('Price error'),
                                         _('can not sell below the \
minimum price'))
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        for line in self:
            if line.tourism:
                # se introduce comparacion con float_compare
                print "Compara por turismo"
                if float_compare(line.price_unit * (line.discount and
                                                       line.discount /
                                      100 or 1) ,
                                 line.tourism.get_box_price(
                                     line.product_id), precision_digits=2):
                    raise exceptions.Warning(_('Price error'),
                                             _('can not sell below the \
minimum price'))
        return res


from openerp.osv import orm, fields


class SaleOrder(orm.Model):
    '''
    Sale Order
    '''
    _inherit = 'sale.order'

    def clear_existing_promotion_lines(self, cursor, user,
                                        order_id, context=None):
        """
        Sobrescrita para que no ponga el descuento a 0 antes de aplicarlas
        """
        order = self.browse(cursor, user, order_id, context)
        order_line_obj = self.pool.get('sale.order.line')
        #Delete all promotion lines
        order_line_ids = order_line_obj.search(cursor, user,
                                            [
                                             ('order_id', '=', order.id),
                                             ('promotion_line', '=', True),
                                            ], context=context
                                            )
        if order_line_ids:
            order_line_obj.unlink(cursor, user, order_line_ids, context)
        #Clear discount column
        order_line_ids = order_line_obj.search(cursor, user,
                                            [
                                             ('order_id', '=', order.id),
                                            ], context=context
                                            )
        for line in order_line_obj.browse(cursor, user, order_line_ids, context):
            if line.orig_qty:
                order_line_obj.write(cursor, user, [line.id], {'product_uom_qty': line.orig_qty}, context)
        # if order_line_ids:
        #     order_line_obj.write(cursor, user,
        #                          order_line_ids,
        #                          {'discount':0.00},
        #                          context=context)
        return True
