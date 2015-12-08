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


class report_custom_batch(models.AbstractModel):

    _name = 'report.stock_picking_batch.report_picking_batch'

    def invoice_vals(self, invoice):
        totals = {}
        lines = {}
        summary = {}
        lines_ga = {}
        tfoot = {}
        totals[invoice.id], lines[invoice.id], summary[invoice.id], \
            lines_ga[invoice.id], tfoot[invoice.id] = self.env['report.custom_documents.report_custom_invoice'].get_invoice_args(invoice)
        return {
            'totals': totals,
            'lines': lines,
            'summary': summary,
            'lines_ga': lines_ga,
            'tfoot': tfoot,
        }

    def picking_vals(self, pick):
        lines = {}
        ind_lines = {}
        tfoot = {}
        totals = {}
        ind_totals = {}  # No se usa, cambio unilever
        ind_totals2 = {}
        lines[pick.id], ind_lines[pick.id], tfoot[pick.id], \
            totals[pick.id], ind_totals2[pick.id] = self.env['report.custom_documents.report_custom_picking'].get_picking_args(pick)
        return {
            'lines': lines,
            'ind_lines': ind_lines,
            'tfoot': tfoot,
            'totals': totals,
            'ind_totals': ind_totals,
            'ind_totals2': ind_totals2,
        }

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report_name = 'stock_picking_batch.report_picking_batch'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        for picking in self.env[report.model].browse(self._ids):
            docs.append(picking)
        docargs = {
            'invoice_vals': self.invoice_vals,
            'picking_vals': self.picking_vals,
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
        }
        return report_obj.render(report_name, docargs)
