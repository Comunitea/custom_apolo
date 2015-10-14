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


class custom_picking_parser(models.AbstractModel):
    """
    """

    _name = 'report.custom_documents.report_custom_picking'

    @api.multi
    def render_html(self, data=None):
        # import ipdb; ipdb.set_trace()

        report_obj = self.env['report']
        report_name = 'custom_documents.report_custom_picking'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        lines = {}
        tfoot = {}
        totals = {}
        for pick in self.env[report.model].browse(self._ids):
            docs.append(pick)
            lines[pick.id] = []
            tfoot[pick.id] = {'sum_qty': 0.0, 'sum_net': 0.0}
            totals[pick.id] = {
                'base': 0.0,
                'iva': 0.0,
                'iva_import': 0.0,
                'rec': 0.0,
                'imp_rec': 0.0,
                'total_doc': 0.0,
                'acc_paid': 0.0,
                'total_paid': 0.0,
            }
            for move in pick.move_lines:
                iva = ""
                sale_line = False
                if move.procurement_id.sale_line_id:
                    sale_line = move.procurement_id.sale_line_id
                    for tax in sale_line.tax_id:
                        if iva:
                            iva += ','
                        iva += str(tax.amount * 100)

                dic = {
                    'ref': move.product_id.default_code,
                    'des': move.product_id.name,
                    'iva': iva,
                    'qty': move.product_uos_qty,
                    'unit': move.product_uos.name,
                    'pric_price': move.order_price_unit,
                    'app_price': move.order_price_unit,
                    'net': move.price_subtotal,
                }
                lines[pick.id].append(dic)
                tfoot[pick.id]['sum_qty'] += dic['qty']
                tfoot[pick.id]['sum_net'] += dic['net']
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'lines': lines,
            'tfoot': tfoot,
            'totals': totals,
        }
        return report_obj.render(report_name, docargs)
