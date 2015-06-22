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

from openerp import models, fields, api, _, workflow
import os
from openerp.addons.depot_edi.wizard.edi_logging import logger
import codecs
from openerp.addons.product.product import check_ean
from datetime import datetime

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

        purchase_uom = uom_obj.search(['|', ('name', '=', "Caja(s)"),
                                       ('name', '=', 'Box(es)')])

        purchase_uom = purchase_uom[0]

        visited_supp_ids = []
        for line in f:
            product_code = str(int(line[:10]))
            product_ids = supp_obj.search([('id', 'in', supplier_product_ids),
                                           ('product_code', '=',
                                            product_code)])
            rappel_group_code = line[10:12]
            rappel_subgroup = self.env['product.rappel.subgroup'].search(
                [('code', '=', rappel_group_code)])
            if rappel_subgroup:
                rappel_subgroup = rappel_subgroup[0]
            else:
                log.error("Rappel subgroup invalid %s for line %s" %
                          (rappel_group_code, line))
                rappel_subgroup = self.env['product.rappel.subgroup']
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
                prod.rappel_subgroup_id = rappel_subgroup.id
                prod.rappel_group_id = rappel_subgroup.group_id.id
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
                create_vals = {'unilever_family_id': family.id,
                               'name': line[50:80].strip(),
                               'rappel_subgroup_id': rappel_subgroup.id,
                               'rappel_group_id': rappel_subgroup.group_id.id,
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
    def parse_indirect_customers_file(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        partner_obj = self.env["res.partner"]
        partners_to_activate = []
        for line in f:
            parts = partner_obj.search([('indirect_customer', '=', True),
                                        ('ref', '=', str(int(line[9:19]))),
                                        '|', ('active', '=', True),
                                        ('active', '=', False)])
            vat = line[119:134].strip()
            valid = False
            if vat:
                valid = partner_obj.simple_vat_check("es", vat)
                if not valid:
                    log.error("Invalid vat %s for line %s" % (vat, line))
            date = datetime.strftime(datetime.strptime(line[1:9], "%Y%m%d"),
                                     "%Y-%m-%d")

            if parts:
                part = parts[0]
                part.name = line[19:49].strip()
                part.street = line[49:79].strip()
                part.city = line[79:109].strip()
                part.zip = line[109:119].strip()
                part.phone = line[135:150].strip()
                part.fax = line[151:166].strip()
                if valid:
                    part.vat = "ES" + vat
                if line[134] == "B":
                    part.state2 = "unregistered"
                    part.comment = (part.comment or "") + \
                        "\nFecha de baja: " + str(date)
                else:
                    part.date = date
                    if part.state2 != "registered" and valid:
                        partners_to_activate.append(part)
            else:
                create_vals = {"name": line[19:49].strip(),
                               "ref": str(int(line[9:19])),
                               "street": line[49:79].strip(),
                               "city": line[79:109].strip(),
                               "zip": line[109:119].strip(),
                               "phone": line[135:151].strip(),
                               "fax": line[151:167].strip(),
                               "is_company": True,
                               "customer": True,
                               "indirect_customer": True}
                if valid:
                    create_vals['vat'] = "ES" + vat
                if line[134] == "B":
                    create_vals["state2"] = "unregistered"
                    create_vals["comment"] = "Fecha de baja: " + str(date)
                else:
                    create_vals["date"] = date
                part = partner_obj.create(create_vals)
                if line[134] != "B" and valid:
                    partners_to_activate.append(part)

            if int(line[167:177]) and int(line[167:177]) != int(line[9:19]):
                parent_part = partner_obj.search([('indirect_customer', '=',
                                                   True),
                                                  ('ref', '=',
                                                   str(int(line[167:177]))),
                                                  '|', ('active', '=', True),
                                                  ('active', '=', False)])
                if parent_part:
                    part.parent_id = parent_part[0].id
                else:
                    parent = partner_obj.\
                        create({"name": line[177:207].strip(),
                                "ref": str(int(line[167:177])),
                                "is_company": True,
                                "customer": True})
                    part.parent_id = parent.id
        partners_to_activate = list(set(partners_to_activate))
        for part in partners_to_activate:
            part.signal_workflow("logic_validated")
            part.signal_workflow("commercial_validated")
            part.signal_workflow("active")
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        os.remove(file_path)
        return

    @api.model
    def parse_purchase_picking_file(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        # Cada linea representa un movimiento del albaran, un fichero puede
        # contener varios albaranes.
        picking_code = ''
        for line in f:
            if not picking_code:
                picking_code = line[117:127]
            pass

    @api.model
    def parse_tourism(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        for line in f:
            """En los ficheros de ejemplo se marca el final del archivo con una
               linea de 0"""
            if line == '0' * 69:
                break
            product_code = line[:10].strip()
            group_code = line[10:16].strip()
            description = line[16:46].strip()
            year = line[46:50].strip()
            sec_price = float(line[50:58])
            min_price = float(line[58:68])
            group = self.env['tourism.group'].search([('name', '=',
                                                       group_code)])
            supplierinfo = self.env['product.supplierinfo'].search(
                [('product_code', '=', product_code)])
            if not supplierinfo:
                log.error("Product with code %s not found." % product_code)
                continue
            if not group:
                group = self.env['tourism.group'].create(
                    {'name': group_code,
                     'description': description,
                     'date_start': '%s-01-01' % year,
                     'date_end': '%s-12-31' % year,
                     'min_price': min_price,
                     'guar_price': sec_price,
                     'supplier_id': supplierinfo.name.id
                     })
            else:
                if group.name != group_code:
                    group.name = group_code
                if group.description != description:
                    group.description = description
                if group.date_start != '%s-01-01' % year:
                    group.date_start = '%s-01-01' % year
                if group.date_end != '%s-12-31' % year:
                    group.date_end = '%s-12-31' % year
                if group.min_price != min_price:
                    group.min_price = min_price
                if group.guar_price != sec_price:
                    group.sec_price = sec_price
                if group.supplier_id != supplierinfo.name:
                    group.supplier_id = supplierinfo.name
            product = supplierinfo.product_tmpl_id
            group.write({'product_ids': [(4, product.id)]})
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        os.remove(file_path)

    @api.model
    def parse_exclusive(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        supplier_products = self.env['product.supplierinfo'].search(
            [('name', 'child_of', [self[0].related_partner_id.id])])
        supplier_product_ids = [x.product_tmpl_id.id for x in
                                supplier_products]
        unlink_products = self.env['product.template'].search(
            [('id', 'in', supplier_product_ids), ('exclusive_ids', '!=',
                                                  False)])
        delete_links = [(3, x.id) for x in unlink_products]
        self.env['res.partner'].search(
            [('customer', '=', True),
             ('exclusive_ids', '!=', False)]).write({'exclusive_ids':
                                                     delete_links})
        for line in f:
            if '0' * 36 in line:
                continue
            customer_code = line[:10].lstrip('0')
            customer = self.env['res.partner'].search([('unilever_code', '=',
                                                        customer_code)])
            if not customer:
                log.error('Customer with unilever code %s not found' %
                          customer_code)
                continue
            product_code = line[10:20].lstrip('0')
            product_info = self.env['product.supplierinfo'].search(
                [('product_code', '=', product_code)])
            if not product_info:
                log.error('product with supplier code %s not found' %
                          product_code)
                continue
            product = product_info.product_tmpl_id
            customer.write({'exclusive_ids': [(4, product.id)]})
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        os.remove(file_path)

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
                elif doc.doc_type.code == 'clp':
                    service.parse_indirect_customers_file(file_path, doc)
                    process = True
                elif doc.doc_type.code == 'alc':
                    service.parse_purchase_picking_file(file_path, doc)
                elif doc.doc_type.code == 'tur':
                    service.parse_tourism(file_path, doc)
                    process = True
                elif doc.doc_type.code == 'lpr':
                    service.parse_exclusive(file_path, doc)
                    process = True
                # No es necesario hacer este desarrollo para el fichero TOR,
                # ya que no lo estan usando. Se hara en otra fase
                # cuando se haya implantado el ERP.
                # elif doc.doc_type.code == 'tor':
                if process:
                    doc.write({'errors': log.get_errors()})
