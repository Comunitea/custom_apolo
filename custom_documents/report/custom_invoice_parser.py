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

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report_name = 'custom_documents.report_custom_invoice'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        lines = {}
        tfoot = {}
        totals = {}
        for inv in self.env[report.model].browse(self._ids):
            docs.append(inv)
            lines[inv.id] = []
            tfoot[inv.id] = {'sum_qty': 0.0, 'sum_net': 0.0}
            idate = inv.date_invoice.split("-")
            inv_date = idate[2] + '/' + idate[1] + '/' + idate[0]
            deliver_man = ''
            if inv.pick_ids and inv.pick_ids[0].route_detail_id:
                detail_route = inv.pick_ids[0].route_detail_id
                if detail_route.commercial_id:
                    deliver_man = detail_route.commercial_id.name
            totals[inv.id] = {
                'inv_date': inv_date,
                'deliver_man': deliver_man,
                'acc_paid': '{0:.2f}'.format(0.00),
                'total_paid': '{0:.2f}'.format(inv.amount_total - 0.0),
            }
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
                # for i in range(0, 25):
                #     lines[pick.id].append(dic)
                lines[inv.id].append(dic)
            tfoot[inv.id]['sum_qty'] = '{0:.2f}'.format(line_qty)
            tfoot[inv.id]['sum_net'] = '{0:.2f}'.format(line_net)

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'totals': totals,
            'tfoot': tfoot,
            'lines': lines,
        }
        return report_obj.render(report_name, docargs)
