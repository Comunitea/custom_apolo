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
from openerp import models, fields, tools, api, exceptions, _
from datetime import datetime

class AccountInvoiceFrigoExport(models.Model):

    _name = 'account.invoice.frigo.export'
    _auto = False

    frigo_code = fields.Char('COD_CONCE')
    sequence = fields.Integer('SECUENCIA')
    ai_number = fields.Char('NUM_DOCUM')
    id = fields.Integer('IDENT_REG')
    date_invoice = fields.Date('FECHA_DOCUM')
    date_proce = fields.Date('FECHA_PROCESO')
    reference = fields.Char('COD_CLIENTE')
    product_code = fields.Char('COD_PRODUCTO_ANT')
    product_name = fields.Char('DESC_PRODUCTO')
    qty = fields.Float('UDS_VENTA')
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice line')
    precio_bruto = fields.Float('VENTAS_BRUTAS', compute='_get_precio_bruto')
    tpr_discount = fields.Float('IMP_DTO_PROD', related='invoice_line_id.tpr_discount')
    tourism_discount = fields.Float('IMP_DTO_TURISMO', related='invoice_line_id.tourism_discount')
    supplier_disc_qty = fields.Float('IMP_DTO_UNILEVER', related='invoice_line_id.supplier_disc_qty')
    rest_disc_qty = fields.Float('IMP_DTO_CONCE', related='invoice_line_id.rest_disc_qty')

    amount_untaxed = fields.Float('IMP_FACT_SINIVA')
    create_date = fields.Date('CREATION_DATE')
    week = fields.Integer('SEMANA', compute='_get_week')
    cod_j = fields.Char('COD_JERARQUIA13')

    @api.one
    def _get_precio_bruto(self):
        partner = self.invoice_id.partner_id
        pricelist = partner.property_product_pricelist
        price = pricelist.price_get(self.invoice_line_id.product_id.id, self.qty or 1.0,
                                    partner.id)[pricelist.id]
        self.precio_bruto = price * self.qty

    @api.one
    def _get_week(self):
        self.week = datetime.strftime(datetime.strptime(self.date_invoice, "%Y-%m-%d"), "%W")


    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE VIEW account_invoice_frigo_export as (
SELECT comp.frigo_code as frigo_code, ai.frigo_sec as sequence, replace(ai.number, '/', '') as ai_number,
       ail.id as id, ai.date_invoice as date_invoice, ai.date_proce as date_proce,
       rp.ref as reference, ps.product_code as product_code, ps.product_name as product_name,
       ail.quantity as qty, ail.price_subtotal as amount_untaxed, ai.create_date as create_date, puf.code as cod_j,
       ai.id as invoice_id, ail.id as invoice_line_id

FROM account_invoice_line ail
     join account_invoice ai on ail.invoice_id = ai.id
     join res_company comp on ai.company_id = comp.id
     join res_partner rp on ai.partner_id = rp.id
     join product_product pp on ail.product_id = pp.id
     join product_template pt on pp.product_tmpl_id = pt.id
     join product_unilever_family puf on pt.unilever_family_id = puf.id
     join product_supplierinfo ps on pp.product_tmpl_id = ps.product_tmpl_id


where ai.frigo_sec != 0
group by comp.frigo_code, ai.frigo_sec, ai.number, ail.id, ai.date_invoice,
         ai.date_proce, rp.ref, ps.product_code, ps.product_name, ail.quantity, ail.price_subtotal, ai.create_date, puf.code,
         ai.id)
""")
