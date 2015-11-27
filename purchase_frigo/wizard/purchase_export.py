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
import os
import base64
import xlrd
import xlwt
import xlutils.copy


class PurchaseFrigoExport(models.TransientModel):

    _name = 'purchase.frigo.export'

    def _getOutCell(self, outSheet, colIndex, rowIndex):
        """ HACK: Extract the internal xlwt cell representation. """
        row = outSheet._Worksheet__rows.get(rowIndex)
        if not row: return None

        cell = row._Row__cells.get(colIndex)
        return cell

    def setOutCell(self, outSheet, col, row, value):
        """ Change cell value without changing formatting. """
        # HACK to retain cell style.
        previousCell = self._getOutCell(outSheet, col, row)
        # END HACK, PART I

        outSheet.write(row, col, value)

        # HACK, PART II
        if previousCell:
            newCell = self._getOutCell(outSheet, col, row)
            if newCell:
                newCell.xf_idx = previousCell.xf_idx
        # END HACK


    def _get_qty(self, suppinfo, qty):
        box_ma = suppinfo.supp_ca_ma
        ma_pa = suppinfo.supp_ma_pa
        box_pa = box_ma * ma_pa
        box = 0
        manto = 0
        pallet = 0
        while qty > 0:
            if qty > box_pa:
                new_pallets = int(qty / box_pa)
                qty -= new_pallets * box_pa
                pallet += new_pallets
            elif qty > box_ma:
                new_mantos = int(qty / box_ma)
                qty -= new_mantos * box_ma
                manto += new_mantos
            else:
                box += qty
                qty = 0
        return (manto, pallet, box)

    @api.multi
    def export(self):
        print "A EXPORTAR"
        currdir = os.path.dirname(os.path.realpath(__file__))
        template_dir = currdir + '/../xls_template/template.xls'
        template_wb = xlrd.open_workbook(template_dir, formatting_info=True)
        t_sh1 = template_wb.sheet_by_index(0)
        # Se recojen los datos del template
        # Se busca la linea del producto y se pone la cantidad
        curr_row = 10
        last_row = t_sh1.nrows
        prods_in_file = {}
        finished = False
        while not finished:
            ref_cell = t_sh1.cell(curr_row, 1)
            if not ref_cell.value:
                finished = True
                continue
            prod_code = ref_cell.value
            if ref_cell.ctype in (2, 3):
                prod_code = str(int(prod_code))[:-2]
            prods_in_file[prod_code] = curr_row
            if curr_row < last_row:
                curr_row += 1
            else:
                finished = True

        final_wb = xlutils.copy.copy(template_wb)

        # Adds order data
        sh1 = final_wb.get_sheet(0)
        purchase_id = self._context.get('active_id', False)
        purchase = self.env['purchase.order'].browse(purchase_id)
        self.setOutCell(sh1, 4, 2, self.env.user.company_id.frigo_code)
        self.setOutCell(sh1, 4, 3, purchase.name)
        #self.setOutCell(sh1, 4, 4, 'x')

        for line in purchase.order_line:
            product = line.product_id
            suppinfo = self.env['product.supplierinfo'].search(
                [('product_tmpl_id', '=', product.product_tmpl_id.id),
                 ('name', '=', purchase.partner_id.id)])
            if not suppinfo:
                raise exceptions.Warning(
                    _('Product configuration'),
                    _('The product %s not have supplier data') % product.name)
            prod_code = suppinfo.product_code[:6]
            if prod_code not in prods_in_file.keys():
                raise exceptions.Warning(
                    _('Product not found'),
                    _('Product %s with supplier code %s not found in  xls template') %
                    (product.name, prod_code))
            qties = self._get_qty(suppinfo, line.product_qty)
            self.setOutCell(sh1, 9, prods_in_file[prod_code], qties[0])
            self.setOutCell(sh1, 10, prods_in_file[prod_code], qties[1])
            self.setOutCell(sh1, 11, prods_in_file[prod_code], qties[2])
            formula = 'L%s+K%s*H%s+G%s*J%s' % ((prods_in_file[prod_code] + 1, ) * 5)
            self.setOutCell(sh1, 12, prods_in_file[prod_code], xlwt.Formula(formula))


        #Se guarda el fichero como adjunto
        print "Generado"
        final_wb.save('/tmp/prueba.xls')
        file = open('/tmp/prueba.xls')
        attachment = {
                            'name': 'frigo_purchase.xls',
                            'datas': base64.encodestring(file.read()),
                            'datas_fname': 'frigo_purchase.xls',
                            'res_model': 'purchase.order',
                            'res_id': purchase_id,
                        }
        self.env['ir.attachment'].create(attachment)
        os.remove('/tmp/prueba.xls')
        return {'type': 'ir.actions.act_window_close'}
