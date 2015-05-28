# -*- coding: utf-8 -*-
##############################################################################
#
#    Omar Castiñeira Saavedra Copyright Comunitea SL 2015
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, fields, api, _
import os
from openerp.addons.depot_edi.wizard.edi_logging import logger
import codecs
from openerp.addons.product.product import check_ean

log = logger("frigo_edi")


class EdiDoc(models.Model):

    _inherit = "edi.doc"

    count = fields.Integer("Seq. count", readonly=True)


class Edi(models.Model):

    _inherit = "edi"

    related_partner_id = fields.Many2one("res.partner", "Related partner",
                                         domain=[('is_company', '=', True)])

    @api.model
    def _get_file_type(self, filename):
        ftype = super(Edi, self)._get_file_type(filename)
        if not ftype:
            doc_type_obj = self.env['edi.doc.type']
            if 'PRO' in filename:
                ftype = doc_type_obj.search([('code', '=', 'pro')])[0]
            elif 'ABO' in filename:
                ftype = doc_type_obj.search([('code', '=', 'abo')])[0]
            elif 'TUR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'tur')])[0]
            elif 'ALC' in filename:
                ftype = doc_type_obj.search([('code', '=', 'alc')])[0]
            elif 'CLP' in filename:
                ftype = doc_type_obj.search([('code', '=', 'clp')])[0]
            elif 'LPR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'lpr')])[0]
            elif 'TOR' in filename:
                ftype = doc_type_obj.search([('code', '=', 'tor')])[0]
        return ftype

    @api.model
    def _get_file_name(self, filename, type):
        if type.code in ('pro', 'abo', 'tur', 'alc', 'clp', 'lpr', 'tor'):
            return filename
        else:
            return super(Edi, self)._get_file_name(filename, type)

    @api.model
    def parse_products_file(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        supp_obj = self.env["product.supplierinfo"]
        prod_obj = self.env["product.product"]
        prod_uf = self.env["product.unilever.family"]
        plst_sup = self.env["pricelist.partnerinfo"]
        tax_obj = self.env["account.tax"]
        uom_obj = self.env["product.uom"]
        supplier_products = supp_obj.\
            search([('name', 'child_of', [self[0].related_partner_id.id])])
        supplier_product_ids = [x.id for x in supplier_products]

        purchase_uom = uom_obj.search(['|',('name', '=', "Caja(s)"),
                                       ('name', '=', 'Box(es)')])
        purchase_uom = purchase_uom[0]

        visited_supp_ids = []
        for line in f:
            product_code = str(int(line[:10]))
            product_ids = supp_obj.search([('id', 'in', supplier_product_ids),
                                           ('product_code', '=',
                                            product_code)])

            family = prod_uf.search([("code", '=', line[12:18])])
            if family:
                family = family[0]
            else:
                family = prod_uf.create({"code": line[12:18],
                                         "name": line[18:48] and
                                         line[18:48].strip() or "/"})

            stax = False
            ptax = False
            if int(line[106:108]):
                stax = tax_obj.search(['|', ('name', '=',
                                             'S_IVA' + line[106:108]),
                                       ('code', '=', 'S_IVA' + line[106:108])])
                if stax:
                    stax = stax[0]
            if int(line[106:108]):
                ptax = tax_obj.search(['|', ('name', '=',
                                             'P_IVA' + line[106:108] + '_BC'),
                                       ('code', '=',
                                        'P_IVA' + line[106:108] + '_BC')])
                if ptax:
                    ptax = ptax[0]

            if line[110] == "M":
                volume = float(line[111:119]) / 1000.0
                weight = 0.0
                supplier_kg_un = 0.0
            elif line[110] == "G":
                volume = 0.0
                weight = float(line[111:119]) / 1000.0
                supplier_kg_un = (float(line[111:119]) / 1000.0) / \
                    float(line[98:106])
            else:
                volume = 0.0
                weight = 0.0
                supplier_kg_un = 0.0

            un_pa = int(line[119:123])
            un_ma = int(line[123:127])
            ma_pa = un_pa / un_ma

            ean14 = line[127:141].strip()
            ean13 = line[142:156].strip()[:13].rjust(13, "0")
            ean13_valid = check_ean(ean13)

            if product_ids:
                visited_supp_ids.append(product_ids[0].id)
                prod = product_ids[0].product_tmpl_id.product_variant_ids[0]
                #TODO: Actualizar grupo de rappel line[10:12]
                prod.unilever_family_id = family.id
                product_ids[0].product_name = line[50:80].strip()
                prod.supplier_un_ca = int(line[98:106])
                prod.volume = volume
                prod.weight = weight
                prod.supplier_kg_un = supplier_kg_un
                prod.supplier_ca_ma = un_ma
                prod.supplier_ma_pa = ma_pa
                prod.uom_po_id = purchase_uom.id
                product_ids[0].pricelist_ids.unlink()
                if stax:
                    prod.taxes_id = [(6, 0, [stax.id])]
                if ptax:
                    prod.supplier_taxes_id = [(6, 0, [ptax.id])]

                plst_sup.create({"suppinfo_id": product_ids[0].id,
                                 "min_quantity": 1,
                                 "price": int(line[80:90]) / 100.0})
            else:
                #TODO: Añadir en el create el grupo de rappel line[10:12]
                create_vals = {'unilever_family_id': family.id,
                               'name': line[50:80].strip(),
                               'standard_price': int(line[80:90]) / 100.0,
                               'volume': volume,
                               'weight': weight,
                               'supplier_kg_un': supplier_kg_un,
                               'supplier_ca_ma': un_ma,
                               'supplier_ma_pa': ma_pa,
                               'supplier_un_ca': int(line[98:106]),
                               'ean14': ean14.rjust(14, "0"),
                               'ean13': ean13_valid and ean13 or False,
                               'type': 'product',
                               'uom_po_id': purchase_uom.id}
                if not ean13_valid:
                    log.error("Ean13 invalid %s for line %s" % (ean13, line))
                if stax:
                    create_vals['taxes_id'] = [(6, 0, [stax.id])]
                if ptax:
                    create_vals['supplier_taxes_id'] = [(6, 0, [ptax.id])]
                prod = prod_obj.create(create_vals)

                sup = supp_obj.create({"name": self[0].related_partner_id.id,
                                       "product_tmpl_id":
                                       prod.product_tmpl_id.id,
                                       "product_name": line[50:80].strip(),
                                       "product_code": product_code})
                plst_sup.create({"suppinfo_id": sup.id,
                                 "min_quantity": 1,
                                 "price": int(line[80:90]) / 100.0})

        unlink_supp_ids = list(set(supplier_product_ids) -
                               set(visited_supp_ids))
        unlink_supp_ids = supp_obj.browse(unlink_supp_ids)
        unlink_supp_ids.unlink()
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        os.remove(file_path)
        return

    @api.model
    def process_files(self, path):
        """
        Search all edi docs in error or draft state and process it depending
        on the document type (picking, invoice)
        """
        for service in self:
            domain = [('state', 'in', ['draft', 'error']),
                      ('service_id', '=', service.id)]
            edi_docs = self.env['edi.doc'].search(domain)
            for doc in edi_docs:
                if doc.file_name not in os.listdir(path):
                    log.warning(_("%s: File not found in folder. File: %s")
                                % (service.name, doc.file_name))
                    continue
                log.set_errors("")
                process = False
                file_path = path + os.sep + doc.file_name
                if doc.doc_type.code == 'pro':
                    service.parse_products_file(file_path, doc)
                    process = True
                if process:
                    doc.write({'errors': log.get_errors()})
