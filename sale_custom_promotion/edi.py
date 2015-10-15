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
from openerp import models, fields, api, tools, exceptions, _
from mako.template import Template
from mako.lookup import TemplateLookup
import os
from datetime import datetime


class Edi(models.Model):

    _inherit = "edi"

    @api.model
    def parse_tourism(self, file_path, doc):
        '''Mover parser a otro modulo'''
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
    def process_files(self, path):
        """
        Search all edi docs in error or draft state and process it depending
        on the document type (picking, invoice)
        """
        super(Edi, self).process_files(path)
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
                if doc.doc_type.code == 'tur':
                    service.parse_tourism(file_path, doc)
                    process = True
                if process:
                    doc.write({'errors': log.get_errors()})


class ExportEdiFile(models.TransientModel):

    _inherit = "edi.export.wizard"

    @api.multi
    def export_file_pol(self, active_model, objs=[]):
        """En este fichero se exportan tanto nuevos clientes como liquidaciones."""
        doc_type_obj = self.env["edi.doc.type"]
        doc_obj = self.env["edi.doc"]
        doc_type = doc_type_obj.search([("code", '=', "pol")])[0]
        last_pol_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_pol_file:
            count = last_pol_file.count + 1
        else:
            count = 1

        tmp_name = "export_pol.txt"
        file_len = len(objs)
        filename = "%sPOL%s.%s" % (self.env.user.company_id.frigo_code,
                                   str(file_len).zfill(4),
                                   str(count).zfill(4))
        templates_path = self.addons_path('frigo_edi') + os.sep + 'wizard' + \
            os.sep + 'templates' + os.sep
        mylookup = TemplateLookup(input_encoding='utf-8',
                                  output_encoding='utf-8',
                                  encoding_errors='replace')
        tmp = Template(filename=templates_path + tmp_name,
                       lookup=mylookup, default_filters=['decode.utf8'])
        objs = [o for o in objs]
        if active_model == 'tourism.customer':
            o = objs
            o2 = []
        else:
            o = []
            o2 = objs
        doc = tmp.render_unicode(o=o, o2=o2, datetime=datetime,
                                 user=self.env.user).encode('utf-8', 'replace')
        file_name = self[0].service_id.output_path + os.sep + filename
        f = file(file_name, 'w')
        f.write(doc)
        f.close()
        file_obj = self.create_doc(filename, file_name, doc_type)
        file_obj.count = count
