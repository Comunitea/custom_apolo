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
from datetime import datetime, date, timedelta

log = logger("frigo_edi")

class ParseException(Exception):
    pass


class EdiDoc(models.Model):

    _inherit = "edi.doc"

    count = fields.Integer("Seq. count", readonly=True)


class EdiUpdate(models.Model):

    _name = 'edi.update'

    date = fields.Date('Reception date')
    type = fields.Char('Document type')
    name = fields.Char('Document name')
    ref = fields.Reference(selection=[('product.product', 'Product'),
                                      ('res.partner', 'Customer'),
                                      ('tourism.group', 'tourism')], string='Reference')
    changes = fields.Text('Changes')
    ref_2 = fields.Reference(selection=[('product.supplierinfo', 'Product supplier info')],
                                       string='Reference')
    changes_2 = fields.Text('Changes')
    changes_show = fields.Text('Changes', compute='_get_changes')
    state = fields.Selection((('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')),
                             'State', default='draft')

    @api.multi
    def act_done(self):
        self.state = 'done'
        self.ref.write(eval(self.changes))
        if self.ref_2:
            self.ref_2.write(eval(self.changes_2))

    @api.multi
    def act_cancel(self):
        self.state = 'cancel'

    @api.one
    def _get_changes(self):
        changes = ''
        for i in ('', '_2'):
            ref_field = 'ref%s' % i
            changes_field = 'changes%s' % i
            if not self[ref_field] or not self[changes_field]:
                continue
            changes += _(self[ref_field]._description) + '\n'
            changes_dict = eval(self[changes_field])
            for col in changes_dict.keys():
                column = False
                if col in self[ref_field]._columns.keys():
                    column = self[ref_field]._columns[col]
                else:
                    column = self[ref_field]._inherit_fields[col][2]

                if column._type == 'many2one':
                    model = column._obj
                    name = self.env[model].browse(changes_dict[col]).name_get()[0][1]
                    changes += '%s          %s\n' % (_(column.string), name)
                elif column._type in ('one2many', 'many2many'):
                    model = column._obj
                    change_ids = 0
                    if changes_dict[col][0][0] == 4:
                        change_ids = [x[1] for x in changes_dict[col]]
                    elif changes_dict[col][0][0] == 6:
                        change_ids = changes_dict[col][0][2]
                    for m_changes in change_ids:
                        name = self.env[model].browse(m_changes).name_get()[0][1]
                        changes += '%s          %s\n' % (_(column.string), name)
                else:
                    changes += '%s          %s\n' % (_(column.string), changes_dict[col])
        self.changes_show = changes


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
    def parse_tourism(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        errors = False
        tot_vals = {}
        for line in f:
            vals = {}
            """En los ficheros de ejemplo se marca el final del archivo con una
               linea de 0"""
            if '00000000000000000000000000000000000000000000000000000000000000000000' in line:
                break
            product_code = line[:10].strip()[:6]
            group_code = line[10:16].strip()
            description = line[16:46].strip()
            year = line[46:50].strip()
            sec_price = float(line[50:58])
            min_price = float(line[58:68])
            group = self.env['tourism.group'].search([('name', '=',
                                                       group_code)])
            supplierinfo = self.env['product.supplierinfo'].search(
                [('product_code', 'ilike', product_code), ('name', '=', self.related_partner_id.id)])
            if not supplierinfo:
                log.error("Product with code %s not found." % product_code)
                errors = True
                continue
            supplierinfo = supplierinfo[0]
            if not group:
                group = self.env['tourism.group'].create(
                    {'name': group_code,
                     'description': description,
                     'date_start': '%s-01-01' % year,
                     'date_end': '%s-12-31' % year,
                     'min_price': min_price,
                     'guar_price': sec_price,
                     'supplier_id': supplierinfo.name.id,
                     'new': True,
                     })
            elif not group.new and group.id not in tot_vals.keys():
                tot_vals[group.id] = []
                if group.name != group_code:
                    vals['name'] = group_code
                if group.description != description:
                    vals['description'] = description
                if group.date_start != '%s-01-01' % year:
                    vals['date_start'] = '%s-01-01' % year
                if group.date_end != '%s-12-31' % year:
                    vals['date_end'] = '%s-12-31' % year
                if group.min_price != min_price:
                    vals['min_price'] = min_price
                if group.guar_price != sec_price:
                    vals['sec_price'] = sec_price
                if group.supplier_id != supplierinfo.name:
                    vals['supplier_id'] = supplierinfo.name
                tot_vals[group.id].append(vals)
            product = supplierinfo.product_tmpl_id
            if group.id in tot_vals.keys():
                tot_vals[group.id].append({'product_ids': [(4, product.id)]})

            else:
                group.write({'product_ids': [(4, product.id)]})
        if errors:
            raise ParseException('', '')
        elif tot_vals:
            for group in tot_vals.keys():
                final_vals = {}
                prod_ids = []
                for vals in tot_vals[group]:
                    if not len(final_vals.keys()):
                        final_vals = vals
                        if vals.get('product_ids', False):
                            prod_ids = [x[1] for x in final_vals['product_ids']]
                    else:
                        prod_ids += [x[1] for x in vals['product_ids'] if x[1] not in prod_ids]
                if prod_ids:
                    final_vals['product_ids'] = [(6, 0, prod_ids)]
                vals_upd = {'date': datetime.now().date(), 'type': doc.doc_type.code,
                            'name': doc.name, 'ref': 'tourism.group,%s' % group,
                            'changes': final_vals}
                upd = self.env['edi.update'].search([('state', '=', 'draft'), ('name', '=', doc.name), ('ref', '=', 'tourism.group,%s' % group)])
                if upd:
                    upd.write(vals_upd)
                elif not upd:
                    self.env['edi.update'].create(vals_upd)

        self.env['tourism.group'].search([('new', '=', True)]).write({'new': False})
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)


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
        errors = False
        for line in f:
            product_code = line[:10][2:8]
            product_ids = supp_obj.search([('id', 'in', supplier_product_ids),
                                           ('product_code', 'ilike',
                                            product_code)])
            rappel_group_code = line[10:12]
            rappel_subgroup = self.env['product.rappel.subgroup'].search(
                [('code', '=', rappel_group_code)])
            if rappel_subgroup:
                rappel_subgroup = rappel_subgroup[0]
            else:
                log.error("Rappel subgroup invalid %s for line %s" %
                          (rappel_group_code, line))
                errors = True
                continue
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
                                             'S_IVA' + line[106:108] + '_B'),
                                       ('description', '=', 'S_IVA' + line[106:108] + '_B')])
                if stax:
                    stax = stax[0]
            if int(line[106:108]):
                ptax = tax_obj.search(['|', ('name', '=',
                                             'P_IVA' + line[106:108] + '_BC'),
                                       ('description', '=',
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
                vals = {}
                vals2 = {}

                if prod.rappel_subgroup_id.id != rappel_subgroup.id:
                    vals['rappel_subgroup_id'] = rappel_subgroup.id
                if prod.rappel_group_id.id != rappel_subgroup.group_id.id:
                    vals['rappel_group_id'] = rappel_subgroup.group_id.id
                if prod.unilever_family_id.id != family.id:
                    vals['unilever_family_id'] = family.id
                if prod.volume != volume:
                    vals['volume'] = volume
                if prod.weight != weight:
                    vals['weight'] = weight
                if prod.uom_po_id.id != purchase_uom.id:
                    vals2['uom_po_id'] = purchase_uom.id
                if stax:
                    if not prod.taxes_id or prod.taxes_id[0].id != stax.id:
                        vals['taxes_id'] = [(6, 0, [stax.id])]
                if ptax:
                    if not prod.supplier_taxes_id or prod.supplier_taxes_id[0].id != ptax.id:
                        vals['supplier_taxes_id'] = [(6, 0, [ptax.id])]
                if product_ids[0].product_name != line[50:80].strip():
                    vals2['product_name'] = line[50:80].strip()
                if product_ids[0].supp_un_ca != int(line[98:106]):
                    vals2['supp_un_ca'] = int(line[98:106])

                if product_ids[0].supp_kg_un != supplier_kg_un:
                    vals2['supp_kg_un'] = supplier_kg_un
                if product_ids[0].supp_ca_ma != un_ma:
                    vals2['supp_ca_ma'] = un_ma
                if product_ids[0].supp_ma_pa != ma_pa:
                    vals2['supp_ma_pa'] = ma_pa

                product_ids[0].pricelist_ids.unlink()
                plst_sup.create({"suppinfo_id": product_ids[0].id,
                                 "min_quantity": 1,
                                 "price": int(line[80:90]) / 100.0,
                                 "from_date": date.today(),
                                 "to_date": date.today() + timedelta(365),}
                                 )
                if vals:
                    upd_vals = {'date': datetime.now().date(), 'type': doc.doc_type.code,
                                'name': doc.name, 'ref': 'product.product,%s' % prod.id,
                                'ref_2': 'product.supplierinfo,%s' % product_ids[0].id,
                                'changes': vals, 'changes_2': vals2}
                    edi_upd = self.env['edi.update'].search([('state', '=', 'draft'), ('name', '=', doc.name), ('ref', '=', 'product.product,%s' % prod.id)])
                    if edi_upd:
                        edi_upd.write(upd_vals)
                    elif not edi_upd:
                        self.env['edi.update'].create(upd_vals)
            else:
                create_vals = {'unilever_family_id': family.id,
                               'name': line[50:80].strip(),
                               'rappel_subgroup_id': rappel_subgroup.id,
                               'rappel_group_id': rappel_subgroup.group_id.id,
                               'standard_price': int(line[80:90]) / 100.0,
                               'volume': volume,
                               'log_base_id': self.env.ref('product.product_uom_unit').id,
                               'log_unit_id': self.env.ref('midban_product.product_uom_box').id,
                               'uom_id': self.env.ref('midban_product.product_uom_box').id,
                               'weight': weight,
                               'temp_type': self.env.ref('midban_product.tt1').id,
                               'ean14': ean14.rjust(14, "0"),
                               'ean13': ean13_valid and ean13 or False,
                               'type': 'product',
                               'uom_po_id': purchase_uom.id}
                if not ean13_valid:
                    log.error("Ean13 invalid %s for line %s" % (ean13, line))
                    errors = True
                    continue
                if stax:
                    create_vals['taxes_id'] = [(6, 0, [stax.id])]
                if ptax:
                    create_vals['supplier_taxes_id'] = [(6, 0, [ptax.id])]
                prod = prod_obj.create(create_vals)

                sup = supp_obj.create({"name": self[0].related_partner_id.id,
                                       "product_tmpl_id":
                                       prod.product_tmpl_id.id,
                                       "product_name": line[50:80].strip(),
                                       "product_code": product_code,
                                       'supp_kg_un': supplier_kg_un,
                                       'supp_ca_ma': un_ma,
                                       'supp_ma_pa': ma_pa,
                                       'supp_un_ca': int(line[98:106]),
                                       'log_base_id': self.env.ref('product.product_uom_unit').id,
                                       'log_unit_id': self.env.ref('midban_product.product_uom_box').id,
                                    })
                plst_sup.create({"suppinfo_id": sup.id,
                                 "min_quantity": 1,
                                 "price": int(line[80:90]) / 100.0,
                                 "from_date": date.today(),
                                 "to_date": date.today() + timedelta(365)})
        if errors:
            raise ParseException('', '')
        unlink_supp_ids = list(set(supplier_product_ids) -
                               set(visited_supp_ids))
        unlink_supp_ids = supp_obj.browse(unlink_supp_ids)
        unlink_supp_ids.unlink()
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        return

    @api.model
    def parse_indirect_customers_file(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        partner_obj = self.env["res.partner"]
        partners_to_activate = []
        errors = False
        for line in f:
            write = False
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
                    errors = True
                    continue
            date = datetime.strftime(datetime.strptime(line[1:9], "%Y%m%d"),
                                     "%Y-%m-%d")

            if parts:
                write = True
                part = parts[0]
                vals = {}
                if part.name != line[19:49].strip():
                    vals['name'] = line[19:49].strip()
                if part.street != line[49:79].strip():
                    vals['street'] = line[49:79].strip()
                if part.city != line[79:109].strip():
                    vals['city'] = line[79:109].strip()
                if part.zip != line[109:119].strip():
                    vals['zip'] = line[109:119].strip()
                if part.phone != line[135:150].strip():
                    vals['phone'] = line[135:150].strip()
                if part.fax != line[151:166].strip():
                    vals['fax'] = line[151:166].strip()
                if valid and part.vat != 'ES' + vat:
                    vals['vat'] = "ES" + vat
                if line[134] == "B":
                    vals['state2'] = "unregistered"
                    vals['comment'] = (part.comment or "") + \
                        "\nFecha de baja: " + str(date)
                else:
                    if part.date != date:
                        vals['date'] = date
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

            if int(line[167:177]) and int(line[167:177]) != int(line[9:19]):
                parent_part = partner_obj.search([('indirect_customer', '=',
                                                   True),
                                                  ('ref', '=',
                                                   str(int(line[167:177]))),
                                                  '|', ('active', '=', True),
                                                  ('active', '=', False)])
                if parent_part and write and part.parent_id.id != parent_part[0].id:
                    vals['parent_id'] = parent_part[0].id
                elif parent_part:
                    part.parent_id = parent_part[0].id
                else:
                    parent = partner_obj.\
                        create({"name": line[177:207].strip(),
                                "ref": str(int(line[167:177])),
                                "indirect_customer": True,
                                "is_company": True,
                                "customer": True})
                    if write:
                        vals['parent_id'] = parent.id
                    else:
                        part.parent_id = parent.id
            if vals:
                vals_upd = {'date': datetime.now().date(), 'type': doc.doc_type.code,
                            'name': doc.name, 'ref': 'res.partner,%s' % part.id,
                            'changes': vals}
                edi_upd = self.env['edi.update'].search([('state', '=', 'draft'), ('name', '=', doc.name), ('ref', '=', 'res.partner,%s' % part.id)])
                if edi_upd:
                    edi_upd.write(vals_upd)
                elif not edi_upd:
                    self.env['edi.update'].create(vals_upd)
        if errors:
            raise ParseException('', '')
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)
        return

    @api.model
    def parse_purchase_picking_file(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        # Cada linea representa 1 movimiento, para no buscar en cada movimiento
        # el albaran al que pertenece se van guardando en un diccionario con
        # clave purchase_code valor record de picking
        picking_store = {}
        errors = False
        for line in f:
            min_date_str = line[25:33]
            min_date = datetime.strptime(min_date_str, '%Y%m%d')
            product_supplier_code = line[43:53][2:8]
            lot_name = line[71:81].lstrip(' ')
            fab_date = line[81:89]
            life_date = datetime.strptime(line[89:97], '%Y%m%d')
            qty = float(line[97:107])
            purchase_code = line[117:127].rstrip(' ')

            if purchase_code not in picking_store.keys():
                purchase = self.env['purchase.order'].search([('name', '=',
                                                               purchase_code)])
                if not purchase:
                    log.error('Purchase with code %s not found' %
                              purchase_code)
                    errors = True
                    continue
                picking = self.env['stock.picking'].search([('purchase_id',
                                                             '=',
                                                             purchase.id)])
                picking_products = [x.product_id.id for x in
                                    picking.move_lines]
                if len(picking_products) != len(set(picking_products)):
                    log.error(
                        'The picking %s has various moves with the same product. Cannot be procesed' % picking.name)
                    errors = True
                    continue
                picking_store[purchase_code] = PickingFile(picking)
            picking = picking_store[purchase_code]

            if picking.picking.min_date != min_date:
                picking.picking.min_date = min_date
            product_supp = self.env['product.supplierinfo'].search(
                [('product_code', 'ilike', product_supplier_code),
                 ('name', '=', self.related_partner_id.id)])
            if not product_supp:
                log.error('Product with code %s not found' %
                          product_supplier_code)
                errors = True
                continue
            product = product_supp.product_tmpl_id.product_variant_ids[0]
            lot_id = self.env['stock.production.lot'].search(
                [('name', '=', lot_name), ('product_id', '=', product.id)])
            if not lot_id:
                lot_id = self.env['stock.production.lot'].create(
                    {'name': lot_name, 'product_id': product.id})
            if lot_id.life_date != life_date:
                lot_id.life_date = life_date
            picking.add_line(product, lot_id, qty)

        for purchase_code in picking_store.keys():
            picking = picking_store[purchase_code].picking
            operations = self.env['stock.pack.operation'].search(
                [('picking_id', '=', picking.id)])
            operations.unlink()
            picking_file = picking_store[purchase_code]
            for move in picking.move_lines:
                total = picking_file.get_qty_by_product(move.product_id)
                if move.product_uom_qty != total:
                    move.product_uom_qty = total
                    move.product_uos_qty = move.product_id.uom_qty_to_uoc_qty(
                        total, move.product_uos.id, self.related_partner_id.id)
                for line in picking_file.get_line_by_product(move.product_id):
                    vals = {
                        'location_id': move.location_id.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'uos_id': move.product_uos.id,
                        'location_dest_id': move.location_dest_id.id,
                        'picking_id': move.picking_id.id,
                        'lot_id': lot_id.id,
                        'product_qty': line.qty,
                        'uos_qty': move.product_id.uom_qty_to_uoc_qty(
                            line.qty, move.product_uos.id,
                            self.related_partner_id.id)
                    }
                    self.env['stock.pack.operation'].create(vals)

        if errors:
            raise ParseException('', '')
        else:
            doc.write({'state': 'imported',
                       'date_process': fields.Datetime.now()})
            self.make_backup(file_path, doc.file_name)

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
        self.env['partner.rules'].search([('product_id', 'in', supplier_product_ids),
                                          ('partner_id.indirect_customer', '=', True)]).unlink()
        customer_vals = {}
        added = []
        end_line = '0' * 36
        errors = False
        for line in f:
            if end_line in line:
                continue
            customer_code = line[:10].lstrip('0')
            customer = self.env['res.partner'].search([('unilever_code', '=',
                                                        customer_code)])
            if not customer:
                log.error('Customer with unilever code %s not found' %
                          customer_code)
                errors = True
                continue
            elif len(customer) != 1:
                log.error('Varios clientes con el mismo codigo de proveedor %s' % customer_code)
                raise ParseException('', '')
                continue
            product_code = line[10:20][2:8]
            product_info = self.env['product.supplierinfo'].search(
                [('product_code', 'ilike', product_code)])
            if not product_info:
                log.error('product with supplier code %s not found' %
                          product_code)
                errors = True
            elif len(product_info) != 1:
                log.error('Varios productos con el mismo codigo de proveedor %s' % product_code)
                errors = True
                continue
            product = product_info.product_tmpl_id
            start_date = datetime.strptime(line[20:28], '%Y%m%d').date()
            end_date = datetime.strptime(line[28:36], '%Y%m%d').date()
            if customer.id not in customer_vals.keys() and product.id not in added:
                customer_vals[customer.id] = [(0, 0, {'start_date':start_date, 'end_date': end_date,
                                                      'product_id': product.id})]
                added.append(product.id)
            elif product.id not in added:
                customer_vals[customer.id].append((0, 0, {'start_date':start_date, 'end_date': end_date,
                                                          'product_id': product.id}))
                added.append(product.id)

        for customer in self.env['res.partner'].browse(customer_vals.keys()):
            customer.write({'rule_type': 'specific_catalog', 'rule_ids': customer_vals[customer.id]})
        if errors:
            raise ParseException('', '')
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)

    @api.model
    def parse_payment_invoice(self, file_path, doc):
        f = codecs.open(file_path, "r", "ISO-8859-1", 'ignore')
        errors = False
        for line in f:
            invoice = self.env['account.invoice'].search([('name', '=',
                                                           line[7:17])])
            partner_id = self.related_partner_id
            account_id = partner_id.property_account_receivable.id
            if not invoice:
                user = self.env.user
                journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'), ('company_id', '=',
                                             user.company_id.id)], limit=1)

                invoice = self.env['account.invoice'].create({
                    'partner_id': partner_id.id,
                    'type': 'out_invoice',
                    'journal_id': journal and journal.id or False,
                    'account_id': account_id,
                    'name': line[7:17],
                    'origin': line[87:97],
                    'state': 'draft',
                    'number': False,
                    'fiscal_position': partner_id.property_account_position.id,
                })
            product_code = line[20:27][:6]
            product_info = self.env['product.supplierinfo'].search(
                [('product_code', 'ilike', product_code)])
            if not product_info:
                log.error('product with supplier code %s not found' %
                          product_code)
                errors = True
                continue
            product = product_info.product_tmpl_id
            qty = float(line[28:33])
            # Los importes aparecen en el documento multiplicados por 100
            total = float(line[68:77]) / 100
            distribution_expenses = float(line[78:87]) / 100
            unit_price = (total + distribution_expenses) / qty
            self.env['account.invoice.line'].create({
                'product_id': product.id,
                'invoice_id': invoice.id,
                'account_id': account_id,
                'price_unit': unit_price,
                'invoice_line_tax_id': [(4, x.id) for x in
                                        product.taxes_id],
                'quantity': qty,
            })
        if errors:
            raise ParseException('', '')
        doc.write({'state': 'imported', 'date_process': fields.Datetime.now()})
        self.make_backup(file_path, doc.file_name)

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
                try:
                    if doc.doc_type.code == 'pro':
                        service.parse_products_file(file_path, doc)
                        process = True
                    elif doc.doc_type.code == 'clp':
                        service.parse_indirect_customers_file(file_path, doc)
                        process = True
                    elif doc.doc_type.code == 'alc':
                        service.parse_purchase_picking_file(file_path, doc)
                    elif doc.doc_type.code == 'lpr':
                        service.parse_exclusive(file_path, doc)
                        process = True
                    elif doc.doc_type.code == 'abo':
                        service.parse_payment_invoice(file_path, doc)
                        process = True
                    elif doc.doc_type.code == 'tur':
                        service.parse_tourism(file_path, doc)
                        process = True
                except ParseException:
                    process = False
                    doc.write({'state': 'error', 'errors': log.get_errors()})
                # No es necesario hacer este desarrollo para el fichero TOR,
                # ya que no lo estan usando. Se hara en otra fase
                # cuando se haya implantado el ERP.
                # elif doc.doc_type.code == 'tor':
                if process:
                    doc.write({'errors': log.get_errors()})


class MoveFile(object):

    def __init__(self, product, lot, qty):
        self.product = product
        self.lot = lot
        self.qty = qty


class PickingFile(object):

    def __init__(self, picking):
        self.picking = picking
        self.lines = {}

    def add_line(self, product, lot, qty):
        key = (product, lot)
        if key not in self.lines.keys():
            self.lines[key] = qty
        else:
            self.lines[key] += qty

    def get_qty_by_product(self, product):
        total = 0.0
        for key in self.lines.iterkeys():
            if key[0] == product:
                total += self.lines[key]
        return total

    def get_line_by_product(self, product):
        lines = []
        for key in self.lines.iterkeys():
            if key[0] == product:
                lines.append(MoveFile(product, key[1], self.lines[key]))
        return lines
