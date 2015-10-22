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


class custom_purchase_order_parser(models.AbstractModel):
    """
    """

    _name = 'report.custom_documents.report_purchase_order'

    @api.multi
    def render_html(self, data=None):
        # import ipdb; ipdb.set_trace()

        report_obj = self.env['report']
        report_name = 'custom_documents.report_purchase_order'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        lines = {}
        totals = {}
        for po in self.env[report.model].browse(self._ids):
            docs.append(po)
            lines[po.id] = []
            totals[po.id] = {
                'n_lines': 0,
                't_pa': 0,
                't_ma': 0,
                't_bo': 0,
                't_un': 0,
                't_ba': 0,
            }
            n_lines = 0
            for line in po.order_line:
                totals[po.id]['n_lines'] += 1
                prod_obj = line.product_id
                supp = prod_obj.get_product_supp_record(po.partner_id.id)
                # import ipdb; ipdb.set_trace()
                ba_un = supp.supp_kg_un
                un_ca = supp.supp_un_ca
                ca_ma = supp.supp_ca_ma
                ma_pa = supp.supp_ma_pa

                logistic_type = prod_obj.get_uom_po_logistic_unit(po.partner_id.id)[0]
                uom_pa = 0
                uom_ma = 0
                uom_bo = 0
                uom_un = 0
                uom_ba = 0

                if logistic_type == 'base':
                    uom_ba = 1
                    uom_un = uom_ba * ba_un
                    uom_bo = uom_un * un_ca
                    uom_ma = uom_bo * ca_ma
                    uom_pa = uom_ma * ma_pa
                elif logistic_type == 'unit':
                    uom_un = 1
                    uom_bo = uom_un * un_ca
                    uom_ma = uom_bo * ca_ma
                    uom_pa = uom_ma * ma_pa

                elif logistic_type == 'box':
                    uom_bo = 1
                    uom_ma = uom_bo * ca_ma
                    uom_pa = uom_ma * ma_pa

                pa = 0 #palet
                ma = 0 #manto (rellano en el informe)
                bo = 0 #caja
                un = 0 #unidad (base en el informe)
                ba = 0 #base (composición en el informe)
                rest_qty = line.product_qty
                # import ipdb; ipdb.set_trace()
                while rest_qty > 0:
                    if rest_qty >= uom_pa:
                        rest_qty -= uom_pa
                        pa += 1
                    elif rest_qty >= uom_ma:
                        rest_qty -= uom_ma
                        ma += 1
                    elif rest_qty >= uom_bo:
                        rest_qty -= uom_bo
                        bo += 1
                    elif rest_qty >= uom_un:
                        rest_qty -= uom_un
                        un += 1
                    else:
                        ba = rest_qty
                        rest_qty -= ba
                un += bo * un_ca
                bo = 0

                dic = {
                    'ref': line.product_id.default_code,
                    'prod': line.product_id.name,
                    'ca_ma': ca_ma,
                    'ma_pa': ma_pa,
                    'pa': pa,
                    'ma': ma,
                    'bo': bo,
                    'un': '{0:.2f}'.format(un),
                    'ba': '{0:.2f}'.format(ba),
                    'n_lines': n_lines,
                }

                totals[po.id]['t_pa'] += pa
                totals[po.id]['t_ma'] += ma
                totals[po.id]['t_bo'] += bo
                totals[po.id]['t_un'] += un
                totals[po.id]['t_ba'] += ba
                lines[po.id].append(dic)

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'lines': lines,
            'totals': totals,
        }
        return report_obj.render(report_name, docargs)
