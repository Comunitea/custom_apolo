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

from openerp import models, fields, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    supplier_id = fields.Many2one("res.partner", "Supplier", readonly=True,
                                  domain=[("is_company", '=', True),
                                          ('supplier', '=', True)],
                                  states={'draft': [('readonly', False)],
                                          'sent': [('readonly', False)]})

    @api.onchange('supplier_id')
    def onchange_supplier_id(self):
        self.order_policy = "picking"

    @api.multi
    def action_wait(self):
        res = super(SaleOrder, self).action_wait()
        for order in self:
            if order.supplier_id:
                order.order_policy = "picking"
        return res

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        res = super(SaleOrder, self).\
            _prepare_order_line_procurement(order, line, group_id=group_id)
        if order.supplier_id:
            res["invoice_state"] == 'none'
        return res

    @api.multi
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        pick_obj = self.env["stock.picking"]
        for order in self:
            if order.procurement_group_id and order.supplier_id:
                pick_ids = pick_obj.search([('group_id', '=',
                                             order.procurement_group_id.id)])
                if pick_ids:
                    pick_ids.write({"invoice_state": 'none',
                                    "supplier_id": order.supplier_id.id,
                                    "indirect": True})
        return res
