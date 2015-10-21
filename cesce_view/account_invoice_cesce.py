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


class account_invoice_cesce(models.Model):

    _name = 'account.invoice.cesce'
    _auto = False

    @api.one
    @api.depends('partner_id')
    def _get_payment_mode(self):
        self.payment_mode = self.partner_id.customer_payment_mode.name

    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    reference = fields.Char('Partner reference', readonly=True)
    name = fields.Char('Partner name', readonly=True)
    nif = fields.Char('NIF', readonly=True)
    cesce_policy = fields.Char('CESCE policy', readonly=True)
    street = fields.Char('Street', readonly=True)
    city = fields.Char('City', readonly=True)
    zip = fields.Char('ZIP', readonly=True)
    amount = fields.Float('Amount', readonly=True)
    invoice_year = fields.Char('Invoice year', readonly=True)
    payment_mode = fields.Char('Payment mode', compute='_get_payment_mode', readonly=True)
    date_due = fields.Date('Date due')

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE VIEW account_invoice_cesce as (
SELECT MIN(invoiced_amounts.invoice_id) as id, rp.id as partner_id, rp.ref as reference, rp.name as name, rp.cesce_policy as cesce_policy, rp.vat as nif, rp.street as street,
       rp.city as city, rp.zip as zip, SUM(invoiced_amounts.amount) as amount, invoiced_amounts.date_due as date_due, invoiced_amounts.invoice_year::float::int as invoice_year

FROM (SELECT ai.partner_id, SUM(ai.amount_total)  as amount,
             extract(year from ai.date_invoice) as invoice_year,
             MIN(ai.id) as invoice_id, ai.date_due as date_due
      FROM account_invoice ai
      WHERE ai.state in ('open', 'paid') AND ai.type = 'out_invoice'
      GROUP BY ai.partner_id, ai.date_due,  extract(year from ai.date_invoice)

      UNION

      SELECT ai.partner_id, - SUM(ai.amount_total)  as amount,
             extract(year from ai.date_invoice) as invoice_year,
             MIN(ai.id) as invoice_id, ai.date_due as date_due
      FROM account_invoice ai
      WHERE ai.state in ('open', 'paid') AND ai.type = 'out_refund'
      GROUP BY ai.partner_id, ai.date_due, extract(year from ai.date_invoice)) invoiced_amounts
JOIN res_partner rp on invoiced_amounts.partner_id = rp.id

GROUP BY rp.id, rp.ref, rp.name, rp.cesce_policy, rp.vat, rp.street, rp.city, rp.zip, invoiced_amounts.date_due, invoiced_amounts.invoice_year::float::int)
""")
