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

    def get_picking_args(self, pick):
        lines = []
        ind_lines = []
        ind_totals = []
        tfoot = {'sum_qty': 0.0, 'sum_net': 0.0}
        pick_date = pick.date.split(' ')[0]
        pd = pick_date.split("-")
        pick_date = pd[2] + "/" + pd[1] + "/" + pd[0]
        totals = {
            'base': '{0:.2f}'.format(pick.amount_untaxed_acc),
            'iva_import': '{0:.2f}'.format(pick.amount_tax_acc),
            'total_doc': '{0:.2f}'.format(pick.amount_total_acc),
            'acc_paid': '{0:.2f}'.format(0.0),
            'total_paid': '{0:.2f}'.format(pick.amount_total_acc - pick.receipt_amount),
            'pick_date': pick_date
        }
        move_qty = 0.0
        move_net = 0.0
        ind_total_units = {}
        ind_totals_dic = {
            'box_qty': 0.0,
            'box_qty_sc': 0.0,
            'box_qty_p': 0.0,
            'un_qty': 0.0,
            'un_qty_sc': 0.0,
            'un_qty_p': 0.0,
            'tot_un': 0.0,
        }
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
                    'uos_qty': '{0:.4f}'.format(op.uos_qty),
                    'uos_name': op.uos_id and op.uos_id.name or '',
                    'uom_qty': '{0:.4f}'.format(op.product_qty),
                    'uom_name': op.product_uom_id and
                    op.product_uom_id.name or ''
                }
                if op.lot_id:
                    op_info['lot_name'] = op.lot_id.name
                    life_date = op.lot_id.life_date
                    if life_date:
                        life_date = life_date.split(" ")[0]
                        ld = life_date.split("-")
                        life_date = ld[2] + "/" + ld[1] + "/" + ld[0]
                    op_info['lot_date'] = life_date or ''
                    lots.append(op_info)

            pu = 0.0
            p_app = 0.0
            if move.procurement_id and move.procurement_id.sale_line_id:
                pu = move.procurement_id.sale_line_id.price_udv
                p_app = pu * (1 - (move.procurement_id.sale_line_id.discount / 100.0))
            dic = {
                'ref': move.product_id.default_code,
                'des': move.product_id.name,
                'iva': iva,
                'qty': '{0:.4f}'.format(move.accepted_qty),
                'unit': move.product_uos.name,
                'pric_price': '{0:.2f}'.format(pu),
                'app_price': '{0:.2f}'.format(p_app),
                'net': '{0:.2f}'.format(move.price_subtotal_accepted),
                'lots': lots
            }
            move_qty += move.accepted_qty
            move_net += move.price_subtotal_accepted
            lines.append(dic)

            if pick.indirect:
                prod_code = move.product_id.default_code
                prod_name = move.product_id.name
                if move.product_id.seller_ids:
                    supp_info = move.product_id.seller_ids[0]
                    # show_name = supp_info.name.supp_name_prod
                    # if show_name and supp_info.product_name:
                    #     prod_name = supp_info.product_name
                    # if show_name and supp_info.product_code:
                    #     prod_code = supp_info.product_code

                    if supp_info.product_name:
                        prod_name = supp_info.product_name
                    if supp_info.product_code:
                        prod_code = supp_info.product_code

                prod_ean_box = move.product_id.ean14 or ''
                prod_ean_consum = move.product_id.ean_consum or ''
                move_subtotal = move.price_subtotal if move.state != 'done' else move.price_subtotal_accepted
                # ifmove_subtotal = move.price_subtotal if move.state != 'done' else move.price_subtotal_accepted move_subtotal:
                #     qty = move.accepted_qty
                #     qty_sc = 0.00
                # else:
                #     qty = 0.00
                #     qty_sc = move.accepted_qty
                # unit = move.product_uos.name
                # ind_dic = {
                #     'ref': prod_code,
                #     'prod': prod_name,
                #     'uc': int(move.product_id.kg_un),
                #     'ean_box': prod_ean_box,
                #     'ean_consum': prod_ean_consum,
                #     'qty': qty,
                #     'unit': unit,
                #     'qty_sc': qty_sc,
                #     'unit_sc': unit,
                #     'total': move_subtotal,
                # }
                # ind_lines.append(ind_dic)
                box_qty, box_qty_sc, \
                un_qty, un_qty_sc, tot_un = self._get_unilever_units(move)
                ind_totals_dic['box_qty'] += box_qty
                ind_totals_dic['box_qty_sc'] += box_qty_sc
                ind_totals_dic['box_qty_p'] += box_qty + box_qty_sc
                ind_totals_dic['un_qty'] += un_qty
                ind_totals_dic['un_qty_sc'] += un_qty_sc
                ind_totals_dic['un_qty_p'] += un_qty + un_qty_sc
                ind_totals_dic['tot_un'] += tot_un
                # if move_subtotal:
                #     qty = move.accepted_qty
                #     qty_sc = 0.00
                # else:
                #     qty = 0.00
                #     qty_sc = move.accepted_qty
                unit = move.product_uos.name
                ind_dic = {
                    'ref': prod_code,
                    'prod': prod_name,
                    'uc': int(move.product_id.kg_un),
                    'ean_box': prod_ean_box,
                    'ean_consum': prod_ean_consum,
                    # 'qty': qty,
                    # 'unit': unit,
                    # 'qty_sc': qty_sc,
                    # 'unit_sc': unit,
                    'box_qty': box_qty,
                    'box_qty_sc': box_qty_sc,
                    'un_qty': un_qty,
                    'un_qty_sc': un_qty_sc,
                    'total': move_subtotal,
                    'total': tot_un,
                }
                ind_lines.append(ind_dic)
                # if unit not in ind_total_units:
                #     ind_total_units[unit] = (qty, qty_sc)
                # else:
                #     new_qty = ind_total_units[unit][0] + qty
                #     new_qty_sc = ind_total_units[unit][1] + qty_sc
                #     ind_total_units[unit] = (new_qty, new_qty_sc)

        tfoot['sum_qty'] = '{0:.4f}'.format(move_qty)
        tfoot['sum_net'] = '{0:.2f}'.format(move_net)
        # Calc indirect totals
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
            # rem_num_units -= 1
            if len(total_list) == 4:

                ind_totals.append(total_list)
                total_list = []
            else:
                if not rem_num_units:
                    for r in range(0, 4 - len(total_list)):
                        total_list.append('')
                        ind_totals.append(total_list)
                        total_list = []
        # return lines, ind_lines, tfoot, totals, ind_totals
        for k in ind_totals_dic.keys():
            ind_totals_dic[k] = str(int(ind_totals_dic[k]))
        return lines, ind_lines, tfoot, totals, ind_totals_dic

    def _get_unilever_units(self, move):
        box_qty = box_qty_sc = un_qty = un_qty_sc = tot_un = 0.0
        uos = move.product_uos
        prod = move.product_id
        if uos and prod:
            move_subtotal = move.price_subtotal if move.state != 'done' else move.price_subtotal_accepted
            if uos.id == prod.log_base_id.id:
                if move_subtotal:
                    un_qty = move.accepted_qty
                    un_qty_sc = 0.00
                else:
                    un_qty = 0.00
                    un_qty_sc = move.accepted_qty
            else:
                move_subtotal = move.price_subtotal if move.state != 'done' else move.price_subtotal_accepted
                if move_subtotal:
                    box_qty = move.accepted_qty
                    box_qty_sc = 0.00
                else:
                    box_qty = 0.00
                    box_qty_sc = move.accepted_qty
        tot_un = prod.kg_un * box_qty + un_qty
        return int(box_qty), int(box_qty_sc), int(un_qty), int(un_qty_sc), int(tot_un)

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
        ind_totals = {}  # No se usa, cambio unilever
        ind_totals2 = {}
        for pick in self.env[report.model].browse(self._ids):
            docs.append(pick)
            # lines[pick.id], ind_lines[pick.id], tfoot[pick.id], \
            #     totals[pick.id], ind_totals[pick.id] = self.get_picking_args(pick)
            lines[pick.id], ind_lines[pick.id], tfoot[pick.id], \
                totals[pick.id], ind_totals2[pick.id] = self.get_picking_args(pick)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': docs,
            'lines': lines,
            'ind_lines': ind_lines,
            'tfoot': tfoot,
            'totals': totals,
            'ind_totals': ind_totals,
            'ind_t2': ind_totals2,
        }
        return report_obj.render(report_name, docargs)
