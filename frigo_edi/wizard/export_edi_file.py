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

from openerp import models, fields, api, tools, exceptions, _
from mako.template import Template
from mako.lookup import TemplateLookup
import os
from datetime import datetime


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


class ExportEdiFile(models.TransientModel):

    _inherit = "edi.export.wizard"

    @api.multi
    def export_files(self):
        if self.env.context.get("doc_type", False):
            active_model = self.env.context["active_model"]
            active_ids = self.env.context["active_ids"]
            if active_ids:
                objs = self.env[active_model].browse(active_ids)
            else:
                objs = False
            doc_type = self.env.context["doc_type"]
            func_name = "self.export_file_" + doc_type + \
                "(active_model, objs)"
            exec_dic = locals()
            exec_dic["active_model"] = active_model
            exec_dic["active_objs"] = objs
            eval(func_name, exec_dic)
        else:
            super(ExportEdiFile, self).export_files()

    @api.model
    def export_file_cli(self, active_model, objs=False):
        mod = self.env[active_model]
        doc_obj = self.env["edi.doc"]
        if not objs:
            objs = mod.search([("state", "=", "pending")])
        if not objs:
            return
        doc_type_obj = self.env["edi.doc.type"]
        doc_type = doc_type_obj.search([("code", '=', "cli")])[0]
        last_cli_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_cli_file:
            count = last_cli_file.count + 1
        else:
            count = 1
        tmp_name = "export_cli.txt"
        filename = "%sCLI%s.%s" % (self.env.user.company_id.frigo_code,
                                   str(len(objs)).zfill(4),
                                   str(count).zfill(4))
        templates_path = self.addons_path('frigo_edi') + os.sep + 'wizard' + \
            os.sep + 'templates' + os.sep
        mylookup = TemplateLookup(input_encoding='utf-8',
                                  output_encoding='utf-8',
                                  encoding_errors='replace')
        tmp = Template(filename=templates_path + tmp_name,
                       lookup=mylookup, default_filters=['decode.utf8'])

        objs = [o for o in objs]
        doc = tmp.render_unicode(o=objs, datetime=datetime).encode('utf-8',
                                                                   'replace')
        file_name = self[0].service_id.output_path + os.sep + filename
        f = file(file_name, 'w')
        f.write(doc)
        f.close()
        file_obj = self.create_doc(filename, file_name, doc_type)
        file_obj.count = count
        for obj in objs:
            obj.state = 'sync'

    @api.model
    def export_file_med(self, active_model, objs=False):
        mod = self.env[active_model]
        doc_obj = self.env["edi.doc"]
        if not objs:
            objs = mod.search([("state", "=", "pending")])
        if not objs:
            return
        doc_type_obj = self.env["edi.doc.type"]
        doc_type = doc_type_obj.search([("code", '=', "med")])[0]
        last_med_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_med_file:
            count = last_med_file.count + 1
        else:
            count = 1
        tmp_name = "export_med.txt"
        filename = "%sMED%s.%s" % (self.env.user.company_id.frigo_code,
                                   str(len(objs)).zfill(4),
                                   str(count).zfill(4))
        templates_path = self.addons_path('frigo_edi') + os.sep + 'wizard' + \
            os.sep + 'templates' + os.sep
        mylookup = TemplateLookup(input_encoding='utf-8',
                                  output_encoding='utf-8',
                                  encoding_errors='replace')
        tmp = Template(filename=templates_path + tmp_name,
                       lookup=mylookup, default_filters=['decode.utf8'])

        objs = [o for o in objs]
        doc = tmp.render_unicode(o=objs, datetime=datetime).encode('utf-8',
                                                                   'replace')
        file_name = self[0].service_id.output_path + os.sep + filename
        f = file(file_name, 'w')
        f.write(doc)
        f.close()
        file_obj = self.create_doc(filename, file_name, doc_type)
        file_obj.count = count
        for obj in objs:
            obj.state = 'sync'

    @api.model
    def export_file_sto(self):
        doc_type_obj = self.env["edi.doc.type"]
        doc_obj = self.env["edi.doc"]
        doc_type = doc_type_obj.search([("code", '=', "sto")])[0]
        last_sto_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_sto_file:
            count = last_sto_file.count + 1
        else:
            count = 1
        sinfo_obj = self.env["product.supplierinfo"]
        sinfo_ids = sinfo_obj.search([('name', 'child_of', [self[0].service_id.
                                                            related_partner_id.
                                                            id])])

        if sinfo_ids:
            products = list(sinfo_ids)
            tmp_name = "export_sto.txt"
            rows = (len(products) / 9) + 2
            filename = "%sSTO%s.%s" % (self.env.user.company_id.frigo_code,
                                       str(rows).zfill(4), str(count).zfill(4))
            templates_path = self.addons_path('frigo_edi') + os.sep + \
                'wizard' + os.sep + 'templates' + os.sep
            mylookup = TemplateLookup(input_encoding='utf-8',
                                      output_encoding='utf-8',
                                      encoding_errors='replace')
            tmp = Template(filename=templates_path + tmp_name,
                           lookup=mylookup, default_filters=['decode.utf8'])

            products = list(chunks(products, 9))
            doc = tmp.render_unicode(products=products, datetime=datetime,
                                     user=self.env.user).encode('utf-8',
                                                                'replace')
            file_name = self[0].service_id.output_path + os.sep + filename
            f = file(file_name, 'w')
            f.write(doc)
            f.close()
            file_obj = self.create_doc(filename, file_name, doc_type)
            file_obj.count = count

    @api.model
    def export_file_mef(self):
        doc_type_obj = self.env["edi.doc.type"]
        doc_obj = self.env["edi.doc"]
        doc_type = doc_type_obj.search([("code", '=', "mef")])[0]
        last_mef_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_mef_file:
            count = last_mef_file.count + 1
        else:
            count = 1
        item_obj = self.env["item.management.item"]
        items = item_obj.search([('partner_id', 'child_of',
                                  [self[0].service_id.related_partner_id.id])]
                                )

        if items:
            items = list(items)
            tmp_name = "export_mef.txt"
            filename = "%sMEF%s.%s" % (self.env.user.company_id.frigo_code,
                                       str(len(items)).zfill(4),
                                       str(count).zfill(4))
            templates_path = self.addons_path('frigo_edi') + os.sep + \
                'wizard' + os.sep + 'templates' + os.sep
            mylookup = TemplateLookup(input_encoding='utf-8',
                                      output_encoding='utf-8',
                                      encoding_errors='replace')
            tmp = Template(filename=templates_path + tmp_name,
                           lookup=mylookup, default_filters=['decode.utf8'])

            doc = tmp.render_unicode(items=items, datetime=datetime,
                                     user=self.env.user).encode('utf-8',
                                                                'replace')
            file_name = self[0].service_id.output_path + os.sep + filename
            f = file(file_name, 'w')
            f.write(doc)
            f.close()
            file_obj = self.create_doc(filename, file_name, doc_type)
            file_obj.count = count

    @api.model
    def export_file_rme(self, active_model, objs=False):
        doc_obj = self.env["edi.doc"]
        if not objs:
            return
        doc_type_obj = self.env["edi.doc.type"]
        doc_type = doc_type_obj.search([("code", '=', "rme")])[0]
        last_rme_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_rme_file:
            count = last_rme_file.count + 1
        else:
            count = 1
        tmp_name = "export_rme.txt"
        filename = "%sRME%s.%s" % (self.env.user.company_id.frigo_code,
                                   str(len(objs)).zfill(4),
                                   str(count).zfill(4))
        templates_path = self.addons_path('frigo_edi') + os.sep + 'wizard' + \
            os.sep + 'templates' + os.sep
        mylookup = TemplateLookup(input_encoding='utf-8',
                                  output_encoding='utf-8',
                                  encoding_errors='replace')
        tmp = Template(filename=templates_path + tmp_name,
                       lookup=mylookup, default_filters=['decode.utf8'])
        objs2 = []
        for o in objs:
            if not o.license_history_ids:
                raise exceptions.Warning(_("Any license history to export in "
                                           "%s") % o.name)
            objs2.append(o)
        doc = tmp.render_unicode(o=objs2, datetime=datetime,
                                 user=self.env.user).encode('utf-8', 'replace')
        file_name = self[0].service_id.output_path + os.sep + filename
        f = file(file_name, 'w')
        f.write(doc)
        f.close()
        file_obj = self.create_doc(filename, file_name, doc_type)
        file_obj.count = count

    @api.model
    def export_file_rco(self, active_model, objs=False):
        doc_obj = self.env["edi.doc"]
        if not objs:
            return
        doc_type_obj = self.env["edi.doc.type"]
        doc_type = doc_type_obj.search([("code", '=', "rco")])[0]
        last_rco_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_rco_file:
            count = last_rco_file.count + 1
        else:
            count = 1
        tmp_name = "export_rco.txt"
        filename = "%sRCO%s.%s" % (self.env.user.company_id.frigo_code,
                                   str(len(objs)).zfill(4),
                                   str(count).zfill(4))
        templates_path = self.addons_path('frigo_edi') + os.sep + 'wizard' + \
            os.sep + 'templates' + os.sep
        mylookup = TemplateLookup(input_encoding='utf-8',
                                  output_encoding='utf-8',
                                  encoding_errors='replace')
        tmp = Template(filename=templates_path + tmp_name,
                       lookup=mylookup, default_filters=['decode.utf8'])
        objs2 = []
        for o in objs:
            if not o.ref_history_ids:
                raise exceptions.Warning(_("Any ref history to export in "
                                           "%s") % o.name)
            objs2.append(o)
        doc = tmp.render_unicode(o=objs2, datetime=datetime,
                                 user=self.env.user).encode('utf-8', 'replace')
        file_name = self[0].service_id.output_path + os.sep + filename
        f = file(file_name, 'w')
        f.write(doc)
        f.close()
        file_obj = self.create_doc(filename, file_name, doc_type)
        file_obj.count = count

    @api.model
    def export_file_alb(self, active_model, objs=False):
        mod = self.env[active_model]
        doc_obj = self.env["edi.doc"]
        if not objs:
            objs = mod.search([("sync", "=", False), ('indirect', '=', True),
                               ('state', '=', 'done'),
                               ('picking_type_code', 'in', ['outgoing',
                                                            'incoming'])])
        if not objs:
            return

        doc_type_obj = self.env["edi.doc.type"]
        doc_type = doc_type_obj.search([("code", '=', "alb")])[0]
        last_alb_file = doc_obj.search([("doc_type", '=', doc_type.id)],
                                       order="date desc", limit=1)
        if last_alb_file:
            count = last_alb_file.count + 1
        else:
            count = 1
        tmp_name = "export_alb.txt"
        objs2 = []
        for pick in objs:
            if not pick.indirect:
                raise exceptions.Warning(_("Picking %s isn't an indirect "
                                           "sale") % pick.name)
            elif pick.state != "done":
                raise exceptions.Warning(_("Picking %s isn't in done "
                                           "state") % pick.name)
            for move in pick.move_lines:
                if move.state == "done":
                    objs2.append(move)
        if objs2:
            filename = "%sALB%s.%s" % (self.env.user.company_id.frigo_code,
                                       str(len(objs2) + len(objs) + 1).
                                       zfill(4), str(count).zfill(4))
            templates_path = self.addons_path('frigo_edi') + os.sep + \
                'wizard' + os.sep + 'templates' + os.sep
            mylookup = TemplateLookup(input_encoding='utf-8',
                                      output_encoding='utf-8',
                                      encoding_errors='replace')
            tmp = Template(filename=templates_path + tmp_name,
                           lookup=mylookup,
                           default_filters=['decode.utf8'])

            doc = tmp.render_unicode(objs=objs, datetime=datetime,
                                     user=self.env.user).encode('utf-8',
                                                                'replace')
            file_name = self[0].service_id.output_path + os.sep + filename
            f = file(file_name, 'w')
            f.write(doc)
            f.close()
            file_obj = self.create_doc(filename, file_name, doc_type)
            file_obj.count = count
            for obj in objs:
                obj.sync = True

    @api.model
    def export_weekly_files(self):
        edi_obj = self.env["edi"]
        edis = edi_obj.search([])
        for service in edis:
            wzd = False
            for dtype in service.doc_type_ids:
                if dtype.code in ["cli", "med", "sto", "mef", "alb"]:
                    wzd = self.create({'service_id': service.id})
                    wzd.export_file_cli("res.partner.sync")
                    wzd.export_file_med("item.management.item.move.sync")
                    wzd.export_file_sto()
                    wzd.export_file_mef()
                    wzd.export_file_alb("stock.picking")
                    break