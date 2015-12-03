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

    indirect_customer = fields.Boolean("Is Indirect Customer", readonly=True,
                                #    default=False) #checked:is indirect customer
                                   related="partner_id.indirect_customer") #checked:is indirect customer

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        """
        If indirect customer get the supplier to the order
        """
        res = super(SaleOrder, self).onchange_partner_id(cr,
                                                         uid,
                                                         ids,
                                                         part,
                                                         context=context)
        partner_t = self.pool.get('res.partner')
        part = partner_t.browse(cr, uid, part, context=context)
        if part and part.indirect_customer and part.supplier_ids:
            res['value']['supplier_id'] = part.supplier_ids[0]
        return res

    @api.onchange('supplier_id')
    def onchange_supplier_id(self):
        self.order_policy = "picking"

    @api.multi
    def action_wait(self):
        for order in self:
            if order.supplier_id \
                    and order.order_policy != "picking":
                order.order_policy = "picking"
        res = super(SaleOrder, self).action_wait()
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
        for order in self:
            if order.procurement_group_id and order.supplier_id:
                pick_obj = self.env["stock.picking"]
                pick_ids = pick_obj.search([('group_id', '=',
                                             order.procurement_group_id.id)])
                if pick_ids:
                    pick_ids.write({"invoice_state": 'none',
                                    "supplier_id": order.supplier_id.id,
                                    "indirect": True})
                for pick in pick_ids:
                    if pick.picking_type_code == 'outgoing' and order.supplier_id.supplier_seq_id:
                        supp_seq = order.supplier_id.supplier_seq_id
                        seq = order.supplier_id.supplier_seq_id.next_by_id(supp_seq.id)
                        pick.name = seq
        return res
