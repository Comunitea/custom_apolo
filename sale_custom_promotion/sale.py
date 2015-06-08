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


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    tourism = fields.Boolean('Tourism')

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        res = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            line, account_id)
        res['tourism'] = line.tourism
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
        if uos.like_type == 'boxes':
            unit_price = res['value']['price_unit'] / product.un_ca
        else:
            unit_price = res['value']['price_unit']
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id,
                                                      context)
        tourism_ids = self.pool.get('tourism.line').search(
            cr, uid, [('product', '=', product.id),
                      ('tourism_id.date_start', '<=', date.today()),
                      ('tourism_id.date_end', '>=', date.today()),
                      ('tourism_id.id', 'in', partner.tourism_group_ids._ids),
                      ('tourism_id.state', '=', 'approved')],
            context=context)
        tourism = self.pool.get('tourism.line').browse(cr, uid, tourism_ids,
                                                       context)
        if tourism and unit_price < tourism.min_price:
            if uos.like_type == 'boxes':
                res['value']['price_unit'] = tourism.min_price * product.un_ca
            else:
                res['value']['price_unit'] = tourism.min_price
            res['value']['discount'] = 0
            res['value']['tourism'] = True
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        tourism_ids = self.env['tourism.line'].search(
            [('product', '=', res.product_id.id),
             ('tourism_id.date_start', '<=', date.today()),
             ('tourism_id.date_end', '>=', date.today()),
             ('tourism_id.id', 'in',
              res.order_id.partner_id.tourism_group_ids._ids),
             ('tourism_id.state', '=', 'approved')])
        if tourism_ids:
            if res.price_unit < tourism_ids[0].min_price:
                raise exceptions.Warning(_('Price error'),
                                         _('can not sell below the \
minimum price'))
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        for line in self:
            tourism_ids = self.env['tourism.line'].search(
                [('product', '=', line.product_id.id),
                 ('tourism_id.date_start', '<=', date.today()),
                 ('tourism_id.date_end', '>=', date.today()),
                 ('tourism_id.id', 'in',
                  line.order_id.partner_id.tourism_group_ids._ids),
                 ('tourism_id.state', '=', 'approved')])
            if tourism_ids:
                if line.price_unit < tourism_ids[0].min_price:
                    raise exceptions.Warning(_('Price error'),
                                             _('can not sell below the \
minimum price'))
        return res
