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


class report_custom_route_detail(models.AbstractModel):

    _name = 'report.custom_documents.report_route_detail'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_documents.report_route_detail')
        route_payments = {}
        totals = {}
        for route_detail in self.env[report.model].browse(self._ids):
            route_payments[route_detail.id] = {}
            totals[route_detail.id] = {}
            for customer in route_detail.customer_ids:
                customer_ = customer.customer_id
                partner = customer_.parent_id and customer_.parent_id.id or \
                    customer_.id
                pickings = self.env['stock.picking'].search(
                    [('picking_type_code', '=', 'outgoing'),
                     ('partner_id', 'child_of', partner),
                     ('route_detail_id', '=', route_detail.id)], limit=1)
                if not pickings:
                    continue
                customer_data = []
                moves = self.env['account.move.line'].search(
                    [('partner_id', 'child_of', partner),
                     ('reconcile_id', '=', False),
                     ('account_id.type', '=', 'receivable')])
                totals[route_detail.id][customer_] = {'debit': 0, 'credit': 0}
                for move in moves:
                    totals[route_detail.id][customer_]['debit'] += move.debit
                    totals[route_detail.id][customer_]['credit'] += move.credit
                    customer_data.append(move)
                route_payments[route_detail.id][customer_] = customer_data
        for route in route_payments.keys():
            if not route_payments[route]:
                route_payments.pop(route, None)
        docargs = {
            'doc_ids': route_payments.keys(),
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'route_payments': route_payments,
            'totals': totals,
            'company': self.env['res.company'].browse(1)
        }
        return report_obj.render('custom_documents.report_route_detail',
                                 docargs)
