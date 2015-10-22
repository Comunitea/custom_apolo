# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Informáticos All Rights Reserved
#    $Carlos Lombardía Rodríguez$ <carlos@comunitea.com>
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
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _
import time


class custom_invoice_parser(models.AbstractModel):
    """
    """

    _name = 'report.custom_documents.report_custom_invoice'

    def get_invoice_args(self, inv):
        lines = []
        summary = []
        lines_ga = {}
        tfoot = {'sum_qty': 0.0, 'sum_net': 0.0}
        inv_date = ''
        if inv.date_invoice:
            idate = inv.date_invoice.split("-")
            inv_date = idate[2] + '/' + idate[1] + '/' + idate[0]
        deliver_man = ''
        if inv.pick_ids and inv.pick_ids[0].route_detail_id:
            detail_route = inv.pick_ids[0].route_detail_id
            if detail_route.comercial_id:
                deliver_man = detail_route.comercial_id.name
        totals = {
            'inv_date': inv_date,
            'deliver_man': deliver_man,
            'total_invoice': '{0:.2f}'.format(inv.amount_total),
            'acc_paid': '{0:.2f}'.format(0.00),
            'total_paid': '{0:.2f}'.format(inv.amount_total - 0.0),
        }

        if inv.partner_id.inv_print_op == 'give_deliver' or not \
                inv.partner_id.inv_print_op:
            line_qty = 0.0
            line_net = 0.0
            for line in inv.invoice_line:
                iva = ""
                if line.invoice_line_tax_id:
                    for tax in line.invoice_line_tax_id:
                        if iva:
                            iva += ''
                        iva += str('{0:.2f}'.format(int(tax.amount * 100)))
                dic = {
                    'ref': line.product_id.default_code,
                    'des': line.product_id.name,
                    'iva': iva,
                    'qty': '{0:.2f}'.format(line.quantity),
                    'unit': line.uos_id.name,
                    'pric_price': '{0:.2f}'.format(line.price_unit),
                    'app_price': '{0:.2f}'.format(line.price_unit),
                    'net': '{0:.2f}'.format(line.price_subtotal),
                }

                line_qty += line.quantity
                line_net += line.price_subtotal
                lines.append(dic)
            tfoot['sum_qty'] = '{0:.2f}'.format(line_qty)
            tfoot['sum_net'] = '{0:.2f}'.format(line_net)
        elif inv.partner_id.inv_print_op == 'group_by_partner' or \
                inv.partner_id.inv_print_op == 'group_pick':
            for pick in inv.pick_ids:
                part_obj = pick.partner_id

                # Group by partner
                if part_obj not in lines_ga:
                    lines_ga[pick.partner_id] = []
                lines_ga[pick.partner_id].append(pick)

        if inv.partner_id.add_summary:
            prod_group = {}
            for line in inv.invoice_line:
                key = (line.product_id.id, line.uos_id.id)
                iva = ""
                if line.invoice_line_tax_id:
                    for tax in line.invoice_line_tax_id:
                        if iva:
                            iva += ''
                        iva += str('{0:.2f}'.format(int(tax.amount * 100)))
                if key not in prod_group:
                    prod_group[key] = {
                        'code': line.product_id.default_code,
                        'name': line.product_id.name,
                        'qty': line.quantity,
                        'unit': line.uos_id.name,
                        'total': line.price_subtotal,
                        'iva': iva,
                    }
                else:
                    prod_group[key]['qty'] += line.quantity
                    prod_group[key]['total'] += line.price_subtotal

            for key in prod_group:
                prod_group[key]['qty'] = \
                    '{0:.2f}'.format(prod_group[key]['qty'])
                prod_group[key]['total'] =  \
                    '{0:.2f}'.format(prod_group[key]['total'])
            summary = prod_group.values()
        return totals, lines, summary, lines_ga, tfoot

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report_name = 'custom_documents.report_custom_invoice'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        lines = {}  # For give delivery option table
        lines_ga = {}   # For group by fiscal address option table
        tfoot = {}
        totals = {}
        summary = {}

        for inv in self.env[report.model].browse(self._ids):
            docs.append(inv)
            totals[inv.id], lines[inv.id], summary[inv.id], \
                lines_ga[inv.id], tfoot[inv.id] = self.get_invoice_args(inv)

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'totals': totals,
            'tfoot': tfoot,
            'lines': lines,
            'lines_ga': lines_ga,
            'summary': summary,
        }
        return report_obj.render(report_name, docargs)
