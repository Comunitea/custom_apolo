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
        report_obj = self.env['report']
        report_name = 'custom_documents.report_custom_picking'
        report = report_obj._get_report_from_name(report_name)
        docs = []
        lines = {}
        ind_lines = {}
        tfoot = {}
        totals = {}
        ind_totals = {}
        for pick in self.env[report.model].browse(self._ids):
            docs.append(pick)
            lines[pick.id] = []
            ind_lines[pick.id] = []
            ind_totals[pick.id] = []
            tfoot[pick.id] = {'sum_qty': 0.0, 'sum_net': 0.0}
            pick_date = pick.date.split(' ')[0]
            pd = pick_date.split("-")
            pick_date = pd[2] + "/" + pd[1] + "/" + pd[0]
            totals[pick.id] = {
                'base': '{0:.2f}'.format(pick.amount_untaxed),
                'iva_import': '{0:.2f}'.format(pick.amount_tax),
                'total_doc': '{0:.2f}'.format(pick.amount_total),
                'acc_paid': '{0:.2f}'.format(0.00),
                'total_paid': '{0:.2f}'.format(pick.amount_total - 0.0),
                'pick_date': pick_date
            }
            move_qty = 0.0
            move_net = 0.0
            ind_total_units = {}
            for move in pick.move_lines:
                iva = ""
                sale_line = False
                if move.procurement_id.sale_line_id:
                    sale_line = move.procurement_id.sale_line_id
                    for tax in sale_line.tax_id:
                        if iva:
                            iva += ','
                        iva += str('{0:.2f}'.format(tax.amount * 100))

                lots = []
                for link in move.linked_move_operation_ids:
                    op = link.operation_id
                    op_info = {
                        'lot_name': '',
                        'lot_date': '',
                        'uos_qty': '{0:.2f}'.format(op.uos_qty),
                        'uos_name': op.uos_id and op.uos_id.name or '',
                        'uom_qty': '{0:.2f}'.format(op.product_qty),
                        'uom_name': op.product_uom_id and
                        op.product_uom_id.name or ''
                    }
                    if op.lot_id:
                        op_info['lot_name'] = op.lot_id.name
                        life_date = op.lot_id.life_date
                        life_date = life_date.split(" ")[0]
                        ld = life_date.split("-")
                        life_date = ld[2] + "/" + ld[1] + "/" + ld[0]
                        op_info['lot_date'] = life_date
                        lots.append(op_info)

                pu = 0.0
                if move.procurement_id and move.procurement_id.sale_line_id:
                    pu = move.procurement_id.sale_line_id.price_udv
                dic = {
                    'ref': move.product_id.default_code,
                    'des': move.product_id.name,
                    'iva': iva,
                    'qty': '{0:.2f}'.format(move.product_uos_qty),
                    'unit': move.product_uos.name,
                    'pric_price': '{0:.2f}'.format(pu),
                    'app_price': '{0:.2f}'.format(pu),
                    'net': '{0:.2f}'.format(move.price_subtotal),
                    'lots': lots
                }
                move_qty += move.product_uos_qty
                move_net += move.price_subtotal
                # for i in range(0, 25):
                #     lines[pick.id].append(dic)
                lines[pick.id].append(dic)

                if pick.indirect:
                    prod_code = move.product_id.default_code
                    prod_name = move.product_id.name
                    if move.product_id.seller_ids:
                        supp_info = move.product_id.seller_ids[0]
                        if supp_info.product_name:
                            prod_name = supp_info.product_name
                        if supp_info.product_code:
                            prod_name = supp_info.product_code

                    prod_ean_box = move.product_id.ean14 or ''
                    prod_ean_consum = move.product_id.ean_consum or ''
                    if move.price_subtotal:
                        qty = move.product_uos_qty
                        qty_sc = 0.00
                    else:
                        qty = 0.00
                        qty_sc = move.product_uos_qty
                    unit = move.product_uos.name
                    ind_dic = {
                        'ref': prod_code,
                        'prod': prod_name,
                        'uc': int(move.product_id.un_ca),
                        'ean_box': prod_ean_box,
                        'ean_consum': prod_ean_consum,
                        'qty': qty,
                        'unit': unit,
                        'qty_sc': qty_sc,
                        'unit_sc': unit,
                        'total': move.price_subtotal,
                    }
                    ind_lines[pick.id].append(ind_dic)

                    if unit not in ind_total_units:
                        ind_total_units[unit] = (qty, qty_sc)
                    else:
                        new_qty = ind_total_units[unit][0] + qty
                        new_qty_sc = ind_total_units[unit][1] + qty_sc
                        ind_total_units[unit] = (new_qty, new_qty_sc)

            tfoot[pick.id]['sum_qty'] = '{0:.2f}'.format(move_qty)
            tfoot[pick.id]['sum_net'] = '{0:.2f}'.format(move_net)
            # Calc indirect totals
            i = 1
            rem_num_units = len(ind_total_units.keys())
            total_list = []
            for unit_name in ind_total_units:
                qty_units = ind_total_units[unit_name]
                str_total = 'Total ' + unit_name + ' : ' + \
                    str(qty_units[0])
                str_total_sc = 'Total ' + unit_name + ' S/C : ' + \
                    str(qty_units[1])
                total_list.append(str_total)
                total_list.append(str_total_sc)
                if len(total_list) == 4 or len(total_list) == rem_num_units:
                    if len(total_list) < 4:
                        for r in range(0, 4 - len(total_list)):
                            total_list.append('')
                    ind_totals[pick.id].append(total_list)
                    total_list = []
                    i = 1
                i += 1
                rem_num_units -= 1

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'lines': lines,
            'ind_lines': ind_lines,
            'tfoot': tfoot,
            'totals': totals,
            'ind_totals': ind_totals,
        }
        return report_obj.render(report_name, docargs)
