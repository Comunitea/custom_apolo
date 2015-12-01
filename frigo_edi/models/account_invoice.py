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
from datetime import datetime, date, timedelta

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'
    # Campos necesarios para cuadre mensual
    frigo_sec = fields.Integer('Frigo sec')
    date_proce = fields.Date('Date proce')


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    tpr_discount = fields.Float('Tpr discount', compute='_get_discount_qties')
    tourism_discount = fields.Float('Tourism discount',
                                    compute='_get_discount_qties')
    supplier_disc_qty = fields.Float('Discounted qty supplier',
                                     compute='_get_discount_qties')
    rest_disc_qty = fields.Float('', compute='_get_discount_qties')

    @api.model
    def _get_week(self, order_date):
        weekday = order_date.weekday()
        monday = order_date + timedelta(days=-weekday)
        sunday = monday + timedelta(days=6)
        return (monday, sunday)

    @api.multi
    def _get_invoice_week(self):
        self.ensure_one()
        if self.invoice_id.date_invoice:
            order_date = datetime.strptime(self.invoice_id.date_invoice, '%Y-%m-%d').date()
        else:
            order_date = date.today()
        return self._get_week(order_date)

    @api.multi
    def _get_applicable_promotions(self, order_line, total_discount):
        self.ensure_one()
        order = order_line.order_id
        joint_promos = self.env['sale.joint.promotion'].search(
            [('start_date', '<=', order.date_order),
             ('end_date', '>=', order.date_order)])
        promo_discounts = []
        for promo in joint_promos:
            if promo.type == 'discount':
                promo_discounts.append(total_discount)
            elif promo.type == 'rappel':
                rappel_product = promo.rappel_id.type_id.product_id
                week = self._get_invoice_week()
                rappel_line = self.search(
                    [('product_id', '=', rappel_product.id),
                     ('invoice_id.date_invoice', '>=', week[0]),
                     ('invoice_id.date_invoice', '<=', week[1]),
                     ('invoice_id.partner_id', '=', self.invoice_id.partner_id.id),
                     ('invoice_id.state', 'in', ('open', 'paid'))
                     ])
                rappel_qty = rappel_line.price_unit
                total_lines = self.search(
                    [('invoice_id.date_invoice', '>=', week[0]),
                     ('invoice_id.date_invoice', '<=', week[1]),
                     ('invoice_id.partner_id', '=', self.invoice_id.partner_id.id),
                     ('invoice_id.state', 'in', ('open', 'paid'))])
                rappel_line_qty = rappel_qty / (len(total_lines) or 1)
                promo_discounts.append(rappel_line_qty)
        return promo_discounts

    @api.one
    def _get_discount_qties(self):
        """
            Se calculan las diferentes cantidades descontadas en distintos
            conceptos para la exportacion edi.
            tpr_discount: Cantidad descontada con promociones.
            tourism_discount: Cantidad descontada en turismo.
            supplier_disc_qty: Descuento asumido por el proveedor,
                               si en la misma semana hay una factura de rappel
                               al mismo cliente se le añade la
                               parte de rappel que asume el proveedor.
            rest_disc_qty: Resto de descuento que no asume el proveedor.
        """
        if self.tourism:
            self.tourism_discount = (self.tourism.tourism_id.guar_price -
                                     self.tourism.agreed_price) * \
                self.product_id.uom_qty_to_uos_qty(self.quantity,
                                                   self.product_id.log_unit_id.id)
        else:
            self.tourism_discount = 0.0
        total_discount = (self.price_unit * self.quantity) * (self.discount / 100)
        if self.promotion_line:
            pricelist = self.invoice_id.partner_id.property_product_pricelist
            price = pricelist.price_get(self.product_id.id, self.quantity)[pricelist.id]
            total_discount += price * self.quantity
        else:
            sale_line = self.stock_move_id.procurement_id.sale_line_id
            discounts = self._get_applicable_promotions(sale_line, total_discount)
            self.supplier_disc_qty = sum([x for x in discounts])
        if not self.supplier_disc_qty:
            self.tpr_discount = total_discount
        self.rest_disc_qty = 0.0
