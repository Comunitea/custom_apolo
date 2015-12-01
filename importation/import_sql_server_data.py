# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import time
import datetime

UOM_MAP = {"K": "kg",
           "U": "Unit(s)",
           "C": "Box(es)",
           "L": "Liter(s)"}

TYPE_MAP = {"S": "service",
            "L": "product",
            "N": "consu"}

IVA_MAP = {
    "1": ["S_IVA10B", "P_IVA10_BC"],
    "2": ["S_IVA4B", "P_IVA4_BC"],
    "3": ["S_IVA21B", "P_IVA21_BC"],
    "4": ["S_IVA0", "P_IVA0_BC"]
}

TEMP_TYPE_MAP = {
    "D": "Seco",
    "N": "Refrigerado",
    "A": "Congelado"
}

MPAGO_MAP = {
    "1": u"Giro SEPA",
    "2": u"Giro SEPA",
    "3": u"Giro SEPA",
    "4": u"Giro SEPA",
    "5": u"Giro SEPA",
    "6": u"Giro SEPA",
    "7": u"Giro SEPA",
    "8": u"Giro SEPA",
    "9": u"Giro SEPA",
    "10": u"Giro SEPA",
    "11": u"Efectivo",
    "12": u"Giro SEPA",
    "13": False,
    "14": False,
    "15": u"Giro SEPA",
    "16": u"Giro SEPA",
    "17": u"Giro SEPA",
    "18": u"Pago inmediato",
    "19": u"Giro SEPA",
    "20": u"Efectivo",
    "21": u"Giro SEPA",
    "22": u"Giro SEPA",
    "23": u"Transferencia Manual"
}

PPAGO_MAP = {
    "1": u"0 días",
    "2": u"Día 25",
    "3": u"Día 15",
    "4": u"Día 30",
    "5": u"Día 5",
    "6": u"Día 10",
    "7": u"15 días, día 30",
    "8": u"40 días F.Fact.",
    "9": u"45 días F.Fact.",
    "10": u"60 días F.Fact.",
    "11": u"0 días",
    "12": u"Día 20",
    "13": u"0 días",
    "14": u"0 días",
    "15": u"15 días",
    "16": u"50 días F.Fact.",
    "17": u"75 días F.Fact.",
    "18": u"0 días",
    "19": u"30 días F.Fact.",
    "20": u"Contado Riguroso",
    "21": u"15 días F.Fact.",
    "22": u"15 días, día 15",
    "23": u"60 días, día 25"
}

PFISC_MAP = {
    "1": u"Régimen Nacional",
    "2": u"Recargo de Equivalencia",
    "3": u"Régimen Intracomunitario"
}

PLIST_MAP = {
    "6": u"Tarifa a domicilio",
    "1": u"Tarifa rincón",
    "0": u"Tarifa pública"
}

PREF_AGREE_MAP = {
    "A": ("H","IM"),
    "E": ("H","IM"),
    "M": ("H","IM"),
    "P": ("H","IM"),
    "C": ("MC","MC"),
    "O": ("H","IM"),
}

def ustr(text):
    """convierte las cadenas de sql server en iso-8859-1 a utf-8 que es la cofificaciï¿œn de postgresql"""
    return unicode(text.strip(), 'iso-8859-15').encode('utf-8')

class DatabaseImport:
    """
    Importa a OpenERP datos de una base de datos SqlServer.
    """

    def __init__(self, dbname, user, passwd, sql_server_host):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = "localhost"
        self.port = 8069
        self.dbname = dbname
        self.user_name = user
        self.user_passwd = passwd
        self.user_id = 0
        self.sql_server_host = sql_server_host

        #
        # Conectamos con OpenERP
        #
        login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
        self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
        self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

        #
        # Fichero Log de Excepciones
        #
        self.file = open("importation_log.txt", "w")

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        self.file.write("WARNING: %s\n\n\n" % repr(exception))
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del método create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'create', data, context)

            if isinstance(res, list):
                res = res[0]

            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))

    def search(self, model, query, offset=0, limit=False, order=False, context={}, count=False):
        """
        Wrapper del método search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, offset, limit, order, context, count)
            return ids
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))


    def read(self, model, ids, fields, context={}):
        """
        Wrapper del método read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'read', ids, fields, context)
            return data
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))


    def write(self, model, ids, field_values, context={}):
        """
        Wrapper del método write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))


    def unlink(self, model, ids, context={}):
        """
        Wrapper del método unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del método default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, ids, context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, method, ids, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def _getProdCategory_byCode(self, code):
        categ_ids = self.search("product.category", [("code", "=", str(code))])
        return categ_ids and categ_ids[0] or False

    def _getRappelGroup_byCode(self, code):
        group_ids = self.search("product.rappel.group", [("code", "=", code)])
        return group_ids and group_ids[0] or False

    def _getRappelGroup_byInternalCode(self, code):
        group_ids = self.search("product.rappel.group", [("internal_code", "=", code)])
        return group_ids and group_ids[0] or False

    def _getRappelSubgroup_byCode(self, code):
        subgroup_ids = self.search("product.rappel.subgroup", [("code", "=", code)])
        return subgroup_ids and subgroup_ids[0] or False

    def _getRappelSubgroup_byInternalCode(self, code):
        subgroup_ids = self.search("product.rappel.subgroup", [("internal_code", "=", code)])
        return subgroup_ids and subgroup_ids[0] or False

    def _getAgreeType_byCode(self, code):
        agree_ids = self.search("agreement.type", [("code", "=", code)])
        return agree_ids and agree_ids[0] or False

    def _getTaxes(self, tax_name):
        tax_ids = self.search("account.tax", [('description', '=', tax_name)])
        return tax_ids

    def _getTempType_byName(self, temp_name):
        temp_ids = self.search("temp.type", [("name", "=", temp_name)])
        return temp_ids and temp_ids[0] or False

    def _get_bank_by_bic(self, bank_bic):
        bank_ids = self.search("res.bank", [("bic", '=', bank_bic)])
        return bank_ids and bank_ids[0] or False

    def _get_fiscal_position_byname(self, fiscal_name):
        fiscal_ids = self.search("account.fiscal.position", [('name', '=', fiscal_name)], context={'lang': 'es_ES'})
        if not fiscal_ids:
            raise Exception("Ninguna posicion fiscal con el nombre %s" % fiscal_name)
        return fiscal_ids[0]

    def _get_payment_mode_by_name(self, pmode_name):
        if not pmode_name:
            return pmode_name
        else:
            pmode_ids = self.search("payment.mode", [('name', '=', pmode_name),('sale_ok', '=', True)], context={'lang': 'es_ES'})
            if not pmode_ids:
                raise Exception("Ningun modo de pago para ventas con el nombre %s" % pmode_name)
            return pmode_ids[0]

    def _get_payment_term_by_name(self, pterm_name):
        if not pterm_name:
            return pterm_name
        else:
            pterm_ids = self.search("account.payment.term", [('name', '=', pterm_name)], context={'lang': 'es_ES'})
            if not pterm_ids:
                raise Exception("Ningun modo de pago para ventas con el nombre %s" % pterm_name)
            return pterm_ids[0]

    def import_product_category(self, cr):
        parent_categ_map = {}
        cr.execute("select count(*) as count from dbo.adsd_gru")
        row = cr.fetchone()
        print "Numero de categorias padre: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select gru_codi as code, gru_desc as name from dbo.adsd_gru")
        for row in cr:
            categ_vals = {
                "name": ustr(row.name),
                "parent_id": 2,  # Se puede vender,
                "code": str(row.code)
            }
            res = self.search("product.category", [('parent_id', '=', categ_vals['parent_id']),
                                                   ('name', '=', categ_vals['name'])])
            if not res:
                categ_id = self.create("product.category", categ_vals)
                parent_categ_map[row.code] = categ_id
            else:
                parent_categ_map[row.code] = res[0]

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        cont = 0
        cr.execute("select count(*) as count from dbo.adsd_fam")
        row = cr.fetchone()
        print "Numero de categorias: ", (row.count)
        num_rows = row.count
        cr.execute("select fam_codi as code, fam_nomb as name, fam_grup as parent_id_map from dbo.adsd_fam")
        for row in cr:
            categ_vals = {
                "name": ustr(row.name),
                "parent_id": parent_categ_map[row.parent_id_map],
                "code": str(row.code)
            }
            res = self.search("product.category", [('parent_id', '=', categ_vals['parent_id']),
                                                   ('name', '=', categ_vals['name'])])
            if not res:
                self.create("product.category", categ_vals)

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_products(self, cr):
        cr.execute("select count(*) as count from dbo.articulos")
        row = cr.fetchone()
        print "Numero de productos: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select v.articulo as default_code, v.descripcion as name, v.familia as categ_id_map, m.pr1_cenv as temp_type_map, "
                   "v.medida_base as uom_id_map, v.medida_composicion as uomb_map, v.cantidad_composicion as kg_un, m.pr1_tcom as var_coeff_un, "
                   "v.cajas_por_rellano as ca_ma, v.cajas_por_pale / nullif(v.cajas_por_rellano, 0) as ma_pa, v.control_stock as type_map, "
                   "v.codigo_iva as tax_map, v.ean_base as ean14, v.precio_ultima_compra as standard_price, v.bloqueado as active, "
                   "m.medida_peso as weight, m.observaciones_articulo as description, v.tipo_composicion as base_use_sale, v.id as internal_code "
                   "from dbo.articulos v inner join dbo.adsd_art m on m.pr1_codi = v.articulo")
        data = cr.fetchall()
        for row in data:
            uom_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uom_id_map.strip()])])[0]
            uob_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uomb_map.strip()])])[0]
            product_vals = {
                "default_code": str(int(row.default_code)),
                "name": ustr(row.name),
                "categ_id": self._getProdCategory_byCode(row.categ_id_map) or 2,
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "log_unit_id": uom_id,
                "kg_un": row.kg_un,
                "ca_ma": row.ca_ma or 0,
                "ma_pa": row.ma_pa or 0,
                "standard_price": row.standard_price,
                "weight": row.weight,
                "description": (row.description and ustr(row.description) or "") + (row.active != "N" and "\nBLOQUEADO" or ""),
                "unit_use_sale": True,
                "type": TYPE_MAP[row.type_map],
                "purchase_ok": True,
                "sale_ok": True,
                "log_box_id": False,
                "log_base_id": False,
                "cost_method": "average",
                "taxes_id": [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_map))][0]))],
                "supplier_taxes_id": [(6, 0, self._getTaxes(IVA_MAP[str(int(row.tax_map))][1]))],
                "ean14": row.ean14 and ustr(str(int(row.ean14))) or "",
                "temp_type": self._getTempType_byName(row.temp_type_map and TEMP_TYPE_MAP[row.temp_type_map] or TEMP_TYPE_MAP["D"]),
                "var_coeff_un": row.var_coeff_un == "V" and True or False,
                "internal_code": str(int(row.internal_code))
            }
            if uom_id != uob_id:
                product_vals["log_base_id"] = uob_id
                product_vals["base_use_sale"] = row.base_use_sale == "S" and True or False

            res = self.search("product.product", [('default_code', '=', product_vals['default_code']),'|',('active', '=', False),('active', '=', True)])
            if not res:
                prod_id = self.create("product.product", product_vals)
            else:
                prod_id = res[0]

            cr.execute("select top 1 tari_prec as lst_price from dbo.adsd_tari where tari_arti = ? order by tari_desd desc", (row.default_code,))
            row2 = cr.fetchone()
            if row2 and row2.lst_price:
                self.write("product.product", [prod_id], {"lst_price": row2.lst_price})

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_list_price(self, cr, product_code, product_id):
        cr.execute("select top 1 tari_prec as lst_price from dbo.adsd_tari where tari_arti = ? order by tari_desd desc", (product_code,))
        row2 = cr.fetchone()
        if row2 and row2.lst_price:
            self.write("product.product", [product_id], {"lst_price": row2.lst_price})

    def _create_or_update_partner(self, row, unregister_id,parent_id=False):
        partner_ids = self.search("res.partner", [('ref', '=', str(row[0])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
        partner_vals = {'comercial': row[1] and ustr(row[1]) or "",
                        'name': ustr(row[2]),
                        'street': row[3] and ustr(row[3]) or "",
                        'zip': row[4] and ustr(row[4]) or "",
                        'city': row[5] and ustr(row[5]) or "",
                        'phone': row[6] and ustr(row[6]) or "",
                        'fax': row[8] and ustr(row[8]) or "",
                        "customer": True,
                        "comment": row[11] and ustr(row[11]) or "",
                        "email": row[10] and ustr(row[10]) or "",
                        "parent_id": parent_id,
                        "is_company": not parent_id and True or False
                        }
        if row[9]:
            partner_vals['state2'] = "unregistered"
            partner_vals['unregister_reason_id'] = unregister_id[0]
            partner_vals['comment'] += "\nFecha de baja: " + str(row[9])
            partner_vals['active'] = False
        insert_vat = False
        if not partner_ids:
            partner_vals['ref'] = str(row[0])
            partner_id = self.create("res.partner", partner_vals)

            if row[7] and len(ustr(row[7].replace(" ", "").replace("-",""))) == 9:
                insert_vat = True
        else:
            self.write("res.partner", [partner_ids[0]], partner_vals)
            partner_id = partner_ids[0]
            if row[7] and len(ustr(row[7].replace(" ", "").replace("-",""))) == 9:
                partner_data = self.read("res.partner", partner_id, ["vat"])
                if not partner_data["vat"]:
                    insert_vat = True
        if insert_vat:
            vat = u"ES" + ustr(row[7].replace(" ", "").replace("-",""))
            try:
                self.write("res.partner", [partner_id], {'vat': vat})
            except:
                print u"CIF no váĺido en España", row[7]

        return partner_id

    def import_customers(self, cr):
        unregister_reason = u"Baja en importación"
        unregister_id = self.search("unregister.partner.reason", [("name", '=', unregister_reason)])
        cr.execute("select count(*) as count from dbo.LG_clientes")
        row = cr.fetchone()
        print "Numero de clientes: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select vc.cliente as ref, vc.nombre_comercial as comercial, vc.nombre_fiscal as name, vc.direccion as street,vc.codigo_postal as zip,"
                   "vc.poblacion as city, vc.telefono as phone, nullif(nullif(vc.nif, '0T'), '0') as vat_woc, c.cli_nfax as fax, c.fecha_baja as inactive_date,"
                   "c.email_comercial as email, c.observaciones as comment from dbo.LG_clientes vc inner join dbo.adsd_clie c on c.cli_codi = vc.cliente where c.cli_asoc = 0")
        parent_partner_data = cr.fetchall()
        for row in parent_partner_data:
            self._create_or_update_partner(row, unregister_id)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        cr.execute("select vc.cliente as ref, vc.nombre_comercial as comercial, vc.nombre_fiscal as name, vc.direccion as street,vc.codigo_postal as zip,"
                   "vc.poblacion as city, vc.telefono as phone, nullif(nullif(vc.nif, '0T'), '0') as vat_woc, c.cli_nfax as fax, c.fecha_baja as inactive_date,"
                   "c.email_comercial as email, c.observaciones as comment, c.cli_asoc as parent_id_map from dbo.LG_clientes vc "
                   "inner join dbo.adsd_clie c on c.cli_codi = vc.cliente where c.cli_asoc != 0")
        child_partner_data = cr.fetchall()
        while child_partner_data:
            for row in child_partner_data:
                partner_parent_ids = self.search("res.partner", [('ref', '=', str(row[12])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                if partner_parent_ids:
                    self._create_or_update_partner(row, unregister_id, parent_id=partner_parent_ids[0])
                    child_partner_data.remove(row)
                    cont += 1
                    print "%s de %s" % (str(cont), str(num_rows))
                else:
                    print "row: ", row

    def import_suppliers(self, cr):
        cr.execute("select count(*) as count from dbo.adsd_prv")
        row = cr.fetchone()
        print "Numero de proveedores: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select prv_codi as ref, prv_nomb as name, prv_dire as street, prv_cpos as zip, prv_pobl as city, prv_ncif as vat_woc, "
                   "prv_tlfo as phone, prv_nfax as fax, cliente as customer from dbo.adsd_prv")
        supplier_data = cr.fetchall()
        for row in supplier_data:
            partner_ids = self.search("res.partner", [('ref', '=', str(row[0])),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            partner_vals = {'name': ustr(row[1]),
                            'street': row[2] and ustr(row[2]) or "",
                            'zip': row[3] and ustr(row[3]) or "",
                            'city': row[4] and ustr(row[4]) or "",
                            'phone': row[6] and ustr(row[6]) or "",
                            'fax': row[7] and ustr(row[7]) or "",
                            "supplier": True,
                            "is_company": True,
                            }
            if partner_ids:
                partner_id = partner_ids[0]
            if row[8] and row[8] != 800000: #unilever
                customer_ids = self.search("res.partner", [('ref', '=', str(row[8])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                if customer_ids:
                    partner_id = customer_ids[0]
            if not partner_id:
                partner_vals["ref"] = str(row[0])
                partner_id = self.create("res.partner", partner_vals)
            else:
                self.write("res.partner", [partner_id], partner_vals)

            if row[7] and len(ustr(row[5].replace(" ", "").replace("-",""))) == 9:
                vat = u"ES" + ustr(row[5].replace(" ", "").replace("-",""))
                try:
                    self.write("res.partner", [partner_id], {'vat': vat})
                except:
                    print u"CIF no váĺido en España", row[7]

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_indirect_customer(self, cr):
        cr.execute("select count(*) as count from dbo.adsd_clpr")
        row = cr.fetchone()
        print "Numero de clientes indirectos: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select clpr_clie as customer_map, clpr_prov as supplier_map, clpr_copr as unilever_code from dbo.adsd_clpr")
        customer_data = cr.fetchall()
        for row in customer_data:
            customer_ids = self.search("res.partner", [('ref', '=', str(row[0])),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            supplier_ids = self.search("res.partner", [('ref', '=', str(row[1])),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            if customer_ids and supplier_ids:
                vals = {'supplier_ids': [(4,supplier_ids[0])],
                        'indirect_customer': True}
                if row[1] == 2: #unilever
                    vals['unilever_code'] = row[2] and str(int(row[2])) or ""
                self.write("res.partner", [customer_ids[0]], vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))


    def import_rel_product_supplier(self, cr):
        cr.execute("select count(*) as count from dbo.articulos where proveedor != 100")
        row = cr.fetchone()
        print "Numero de proveedores/productos: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select v.articulo as default_code, v.proveedor as supplier_map, v.articulo_proveedor as supplier_code, v.medida_base as uom_id_map, v.medida_composicion as uomb_map,"
                   " v.tipo_composicion as base_use_purchase, v.cantidad_composicion as supp_kg_un, m.pr1_tcom as var_coeff_un, v.cajas_por_rellano as supp_ca_ma, "
                   " v.cajas_por_pale / nullif(v.cajas_por_rellano, 0) as supp_ma_pa from dbo.articulos v inner join dbo.adsd_art m on m.pr1_codi = v.articulo where v.proveedor != 100")
        product_data = cr.fetchall()
        for row in product_data:
            uom_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uom_id_map.strip()])])[0]
            uob_id = self.search("product.uom", [('name', '=', UOM_MAP[row.uomb_map.strip()])])[0]
            supplier_ids = self.search("res.partner", [('ref', '=', str(row.supplier_map)),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            product_ids = self.search("product.product", [('default_code', '=',str(row.default_code)),'|',('active', '=', False),('active', '=', True)])
            if supplier_ids and product_ids:
                product_data = self.read("product.product", product_ids[0], ["product_tmpl_id"])
                supp_info_ids = self.search("product.supplierinfo", [('product_tmpl_id', '=', product_data['product_tmpl_id'][0]),('name', '=', supplier_ids[0])])
                if not supp_info_ids:
                    vals = {"product_tmpl_id": product_data['product_tmpl_id'][0],
                            "name": supplier_ids[0],
                            "product_code": str(row.supplier_code),
                            "log_unit_id": uom_id,
                            "unit_use_purchase": True,
                            "log_box_id": False,
                            "log_base_id": False,
                            "base_use_purchase": False,
                            "supp_kg_un": row.supp_kg_un,
                            "supp_ca_ma": row.supp_ca_ma or 0,
                            "supp_ma_pa": row.supp_ma_pa or 0,
                            "var_coeff_un": row.var_coeff_un == "V" and True or False}

                    if uom_id != uob_id:
                        vals["log_base_id"] = uob_id

                    self.create("product.supplierinfo", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def fix_products(self, cr):
        products_ids = self.search("product.product", [('description', 'like', '%BLOQUEADO%')])
        print "to_fix_products: ", len(products_ids)
        products_data = self.read('product.product', products_ids, ['description'])
        for product in products_data:
            self.write("product.product", [product["id"]], {'description': product["description"].replace("BLOQUEADO", "")})

        cr.execute("select count(*) as count from dbo.articulos where bloqueado  != 'N'")
        row = cr.fetchone()
        print "Numero de productos bloqueados: ", (row.count)
        num_rows = row.count
        cont = 0
        cr.execute("select articulo as default_code, bloqueado as active from dbo.articulos where bloqueado  != 'N'")
        data = cr.fetchall()
        for row in data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row.default_code))),'|',('active', '=', False),('active', '=', True)])
            if product_ids:
                product_data = self.read('product.product', product_ids[0], ['description'])
                self.write("product.product", [product_ids[0]], {'description': product_data["description"] and product_data["description"] + u"\nBLOQUEADO" or "BLOQUEADO"})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_bank_accounts(self, cr):
        cr.execute("select iban_banco + ' ' + cl5_dig1 + ' ' + cl5_dig2 + ' ' + cl5_dig3 + ' ' + cl5_ncta as acc_number, "
                   "cli_codi as customer_id_map, fecha_mandato as signature_date, entidad_bic as bank_bic_map, referencia_mandato as unique_mandate_reference "
                    "from dbo.VWTA_cliente_bancarios where iban_banco != '' and cl5_dig1 != 0 and cl5_dig2 != 0 and cl5_dig3 != 0 and cl5_ncta != ''")
        data = cr.fetchall()
        num_rows = len(data)
        cont = 0
        for row in data:
            try:
                partner_ids = self.search("res.partner", [('ref', '=', str(int(row.customer_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                if partner_ids:
                    acc_vals = {'state': "iban",
                                'acc_number': row.acc_number,
                                'partner_id': partner_ids[0],
                                'bank_bic': row.bank_bic_map or False,
                                'bank': row.bank_bic_map and self._get_bank_by_bic(ustr(row.bank_bic_map)) or False}
                    bank_id = self.create("res.partner.bank", acc_vals)

                    if row.unique_mandate_reference:
                        mandate_vals = {
                            "unique_mandate_reference": row.unique_mandate_reference,
                            "signature_date": row.signature_date and row.signature_date.strftime("%Y-%m-%d %H:%M:%S") or time.strftime("%Y-%m-%d %H:%M:%S"),
                            "recurrent_sequence_type": "recurring",
                            "scheme": "B2B",
                            "type": "recurrent",
                            "partner_bank_id": bank_id
                        }
                        mandate_id = self.create("account.banking.mandate", mandate_vals)
                        self.execute("account.banking.mandate", "validate", [mandate_id])
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))
            except Exception, e:
                print "Exception %s: account %s" % (e, row.acc_number)
                cont += 1
                print "%s de %s" % (str(cont), str(num_rows))

    def import_master_frigo_data(self, cr):
        print "Familas Unilever Clientes"
        cr.execute("select conversion as code, establecimiento as name from dbo.establecimiento_frigo")
        unilever_fam_data = cr.fetchall()
        num_rows = len(unilever_fam_data)
        cont = 0
        for row in unilever_fam_data:
            vals = {'code': str(int(row.code)),
                    'name': ustr(row.name)}
            self.create("res.partner.unilever.family", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        print "Grupos rappel"
        cr.execute("select codigo as internal_code, proveedor as supplier_id_map, descripcion as name, grupo_frigo as code from dbo.grupo_rappel")
        rappel_group_data = cr.fetchall()
        num_rows = len(rappel_group_data)
        cont = 0
        for row in rappel_group_data:
            supplier_ids = self.search("res.partner", [('ref', '=', str(int(row.supplier_id_map))),('supplier', '=', True),'|',('active', '=', True),('active', '=', False)])
            vals = {'internal_code': str(int(row.internal_code)),
                    'name': ustr(row.name),
                    'supplier_id': supplier_ids and supplier_ids[0] or False,
                    'code': row.code != '00' and ustr(row.code) or str(int(row.internal_code))}
            self.create("product.rappel.group", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        print "Subgrupo rappel"
        cr.execute("select codigo as internal_code, descripcion as name, grupo_rappel as group_id_map, informe_frigo as code from dbo.subgrupo_rappel")
        rappel_subgroup_data = cr.fetchall()
        num_rows = len(rappel_subgroup_data)
        cont = 0
        for row in rappel_subgroup_data:
            rappel_group_ids = self.search("product.rappel.group", [('internal_code', '=', str(int(row.group_id_map)))])
            vals = {'internal_code': str(int(row.internal_code)),
                    'name': ustr(row.name),
                    'group_id': rappel_group_ids and rappel_group_ids[0] or False,
                    'code': row.code != '00' and ustr(row.code) or str(int(row.internal_code))}
            self.create("product.rappel.subgroup", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        print "Familas Unilever Productos"
        cr.execute("select codigo as code, descripcion as name from dbo.jerarquia_frigo")
        unilever_fam_data = cr.fetchall()
        num_rows = len(unilever_fam_data)
        cont = 0
        for row in unilever_fam_data:
            vals = {'code': ustr(row.code),
                    'name': ustr(row.name)}
            self.create("product.unilever.family", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_product_frigo_data(self, cr):
        cr.execute("select codigo_ficha as product_id_map, codigo_producto as supplier_code, proveedor as supplier_id_map, descripcion_producto as supplier_name, "
                   "subgrupo_producto as rappel_subgroup_id_map, grupo_rappel as rappel_group_id_map, jerarquia as unilever_family_id_map from dbo.informe_productos "
                   "where codigo_ficha != 0")
        unilever_prod_data = cr.fetchall()
        num_rows = len(unilever_prod_data)
        cont = 0
        for row in unilever_prod_data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', True),('active', '=', False)])
            if product_ids:
                product_data = self.read("product.product", product_ids[0], ["product_tmpl_id"])
                supplier_ids = self.search("res.partner", [('supplier', '=', True),('ref', '=', str(int(row.supplier_id_map))),'|',('active', '=',True),('active','=',False)])
                if supplier_ids:
                    supp_info_ids = self.search("product.supplierinfo", [('product_tmpl_id', '=', product_data["product_tmpl_id"][0]),('name', '=', supplier_ids[0])])
                    if supp_info_ids:
                        supp_vals = {
                            'product_code': row.supplier_code and ustr(str(int(row.supplier_code))) or "",
                            'product_name': row.supplier_name and ustr(row.supplier_name) or ""
                        }
                        self.write("product.supplierinfo", [supp_info_ids[0]], supp_vals)

                vals = {}
                if row.rappel_subgroup_id_map:
                    subgroup_ids = self.search("product.rappel.subgroup", [("code", '=', ustr(row.rappel_subgroup_id_map))])
                    if subgroup_ids:
                        vals["rappel_subgroup_id"] = subgroup_ids[0]
                if row.rappel_group_id_map:
                    group_ids = self.search("product.rappel.group", [("internal_code", '=', str(int(row.rappel_group_id_map)))])
                    if group_ids:
                        vals["rappel_group_id"] = group_ids[0]
                if row.unilever_family_id_map and row.unilever_family_id_map != "00":
                    family_ids = self.search("product.unilever.family", [("code", '=', row.unilever_family_id_map)])
                    if family_ids:
                        vals["unilever_family_id"] = family_ids[0]
                if vals:
                    self.write("product.product", [product_ids[0]], vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_other_prices(self, cr):
        cr.execute("select distinct tari_arti as product_id_map from dbo.adsd_tari where tari_pre1 != 0.0 or tari_pre6 != 0.0")
        product_data = cr.fetchall()
        num_rows = len(product_data)
        cont = 0
        for product in product_data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(product.product_id_map))),'|',('active','=',True),('active','=',False)])
            if product_ids:
                cr.execute("select tari_pre1 as nook_price, tari_pre6 as doorstep_price from dbo.adsd_tari where  (tari_pre1 != 0.0 or "
                           "tari_pre6 != 0.0) and tari_arti = ? order by tari_desd desc", (int(product.product_id_map),))
                prices_data = cr.fetchall()
                nook_price = 0.0
                doorstep_price = 0.0
                for row in prices_data:
                    if nook_price and doorstep_price:
                        break
                    if not nook_price and row.nook_price:
                        nook_price = float(row.nook_price)
                    if not doorstep_price and row.doorstep_price:
                        doorstep_price = float(row.doorstep_price)

                if doorstep_price or nook_price:
                    self.write("product.product", [product_ids[0]], {'nook_price': nook_price,
                                                                     'doorstep_price': doorstep_price})
            cont +=1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_customers_other_data(self, cr):
        cr.execute("select cl3_fpag as payment_type_map, cli_regi as fiscal_position_map, cl3_raf3 as valued_picking, cl3_facl as inv_print_op_map, "
                   "cl3_fdet as  add_summary, cl3_raf2 as pricelist_id_map, trazabilidad as picking_traceability, cli_codi as partner_id_map from dbo.adsd_clie")
        data = cr.fetchall()
        num_rows = len(data)
        cont = 0
        for row in data:
            partner_ids = self.search("res.partner", [('ref', '=', str(int(row.partner_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if partner_ids:
                vals = {'property_account_position': self._get_fiscal_position_byname(PFISC_MAP[str(int(row.fiscal_position_map))]),
                        'property_product_pricelist': self.search("product.pricelist", [('name', '=', PLIST_MAP[str(int(row.pricelist_id_map))])], context={'lang': 'es_ES'})[0]}
                if row.payment_type_map != 0:
                #vals = {}
                    vals["customer_payment_mode"] = self._get_payment_mode_by_name(MPAGO_MAP[str(int(row.payment_type_map))])
                    vals["property_payment_term"] = self._get_payment_term_by_name(PPAGO_MAP[str(int(row.payment_type_map))])
                if row.picking_traceability == 'S':
                    vals['pick_print_op'] = "tracked"
                else:
                    if int(row.valued_picking) == 1:
                        vals["pick_print_op"] = "not_valued"
                    else:
                        vals["pick_print_op"] = "valued"

                if row.add_summary == "A":
                    vals["add_summary"] = True
                    vals["inv_print_op"] = "group_by_partner"
                    vals["invoice_method"] = "c"
                else:
                    #if int(row.payment_type_map) in (11,13,18,20):
                    vals["inv_print_op"] = "give_deliver"
                    #else:
                    #    vals["inv_print_op"] = "group_pick"
                    vals["invoice_method"] = "a"
                self.write("res.partner", [partner_ids[0]], vals)

            cont +=1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_preferential_agree_data(self, cr):
        print "tipos de acuerdos"
        cr.execute("select codigo as  code, concepto + '  '  + descripcion as name from dbo.acuerdos_preferentes")
        agree_type_data = cr.fetchall()
        num_rows = len(agree_type_data)
        cont = 0
        for row in agree_type_data:
            vals = {
                'code': row.code,
                'name': ustr(row.name),
                'rappel_group_id': self._getRappelGroup_byCode(PREF_AGREE_MAP[ustr(row.code)][0]),
                'rappel_subgroup_id': self._getRappelSubgroup_byCode(PREF_AGREE_MAP[ustr(row.code)][1])
            }
            self.create("agreement.type", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        print "acuerdos activos"
        cr.execute("select cliente as customer_id_map, fecha_inicio as init_date, fecha_fin as end_date, fecha_operacion as date, tipo_colaboracion as type_map, "
                   "importe_total as amount, participacion as joint_percentage, consumo_previsto as cons_est, observaciones as note from "
                   "dbo.VW_listado_acuerdos_preferente where anio = 2015 and fecha_fin > getdate()")
        agreements_data = cr.fetchall()
        num_rows = len(agreements_data)
        cont = 0
        for row in agreements_data:
            customer_ids = self.search("res.partner", [('ref', '=', str(int(row.customer_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if customer_ids:
                vals = {
                    'customer_id': customer_ids[0],
                    'init_date': row.init_date.strftime("%Y-%m-%d"),
                    'end_date': row.end_date.strftime("%Y-%m-%d"),
                    'date': row.date.strftime("%Y-%m-%d"),
                    'type': self._getAgreeType_byCode(row.type_map),
                    'amount': float(row.amount),
                    'joint_percentage': float(row.joint_percentage),
                    'cons_est': float(row.cons_est),
                    'note': ustr(row.note),
                    'state': "confirmed"
                }
                agree_id = self.create("preferential.agreement", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_tourism_data(self, cr):
        cr.execute("select codigo_politica as name, descripcion as description, precio_minimo as min_price, precio_asegurado as guar_price "
                   "from dbo.politica_frigo where situacion = 'A' group by codigo_politica, descripcion, precio_minimo, precio_asegurado")
        tourism_data = cr.fetchall()
        num_rows = len(tourism_data)
        cont = 0
        unilever_id = self.search("res.partner", [('ref', '=', '2'),('supplier', '=', True),'|',('active','=',False),('active','=',True)])[0]
        for row in tourism_data:
            tourism_vals = {
                'name': str(int(row.name)),
                'description': ustr(row.description),
                'min_price': float(row.min_price),
                'guar_price': float(row.guar_price),
                'state': 'approved',
                'supplier_id': unilever_id,
                'date_start': "2015-01-01",
                'date_end': "2015-12-31"
            }
            tourism_id = self.create("tourism.group", tourism_vals)
            cr.execute("select codigo_producto as product_id_map from dbo.politica_frigo where codigo_politica = ?", (int(row.name),))
            products_data = cr.fetchall()
            tourism_product_ids = []
            for product_row in products_data:
                supp_ids = self.search("product.supplierinfo", [('product_code', '=', str(int(product_row.product_id_map))),('name', '=', unilever_id)])
                if supp_ids:
                    supp_data = self.read("product.supplierinfo", supp_ids[0], ["product_tmpl_id"])
                    product_ids = self.search("product.product", [('product_tmpl_id', '=', supp_data["product_tmpl_id"][0]),'|',('active','=',True),('active','=',False)])
                    if product_ids:
                        tourism_product_ids.append(product_ids[0])
            if tourism_product_ids:
                self.write("tourism.group", [tourism_id], {'product_ids': [(6, 0, list(set(tourism_product_ids)))]})

            cr.execute("select cliente as customer_id_map, consumo_estimado as qty_estimated, consumo_politica as qty_estimated_tourism, precio as agreed_price, "
                       "grupo as product_rappel_group_map, fecha as agreement_date from dbo.envio_politica where producto = ? order by fecha desc", (int(row.name),))
            customers_data = cr.fetchall()
            customer_ids = []
            for customer_row in customers_data:
                if int(customer_row.customer_id_map) not in customer_ids:
                    customer_ids.append(int(customer_row.customer_id_map))
                    customer_ids = self.search("res.partner", [('ref', '=', str(int(customer_row.customer_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                    if customer_ids:
                        vals = {
                            "customer_id": customer_ids[0],
                            "tourism_id": tourism_id,
                            "agreed_price": float(customer_row.agreed_price),
                            "qty_estimated": float(customer_row.qty_estimated),
                            "qty_estimated_tourism": float(customer_row.qty_estimated_tourism),
                            "agreement_date": customer_row.agreement_date.strftime("%Y-%m-%d"),
                            "product_group": self._getRappelGroup_byCode(ustr(customer_row.product_rappel_group_map))
                        }
                        self.create("tourism.customer", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_giras(self, cr):
        cr.execute("select descripcion as name, fecha_inicio as from_date, fecha_fin as to_date, numero_gira as num from dbo.cabecera_giras where fecha_fin > getdate()")
        giras_data = cr.fetchall()
        num_rows = len(giras_data)
        cont = 0
        for row in giras_data:
            vals = {
                "name": ustr(row.name),
                "from_date": row.from_date.strftime("%Y-%m-%d %H:%M:%S"),
                "to_date": row.to_date.strftime("%Y-%m-%d %H:%M:%S"),
                "login": "and",
                "expected_logic_result": "True",
                "sequence": 1
            }
            promoton_id = self.create("promos.rules", vals)

            cr.execute("select codigo_producto as product_id_map, dcto as discount from dbo.aVW_lista_giras where numero_gira = ?", (int(row.num),))
            promo_lines_data = cr.fetchall()
            for line in promo_lines_data:
                product_ids = self.search("product.product", [('default_code','=',str(int(line.product_id_map))),'|',('active','=',True),('active','=',False)])
                if product_ids:
                    action_vals = {
                        "action_type": "prod_disc_perc",
                        "product_code": "'" + str(int(line.product_id_map)) + "'",
                        "arguments": str(float(line.discount)),
                        "promotion": promoton_id,
                        "sequence": 1
                    }
                    action = self.create("promos.rules.actions", action_vals)

                    rule_vals = {
                        'stop_further': True,
                        'attribute': "product",
                        'comparator': 'in',
                        'value': "'" + str(int(line.product_id_map)) + "'",
                        'promotion': promoton_id,
                        "sequence": 1
                    }
                    self.create("promos.rules.conditions.exps", rule_vals)

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def fix_customer_names(self, cr):
        cr.execute("select cli_nomb as comercial, cli_razo as name, cli_codi as default_code, codigo_agrupa as parent_id from dbo.adsd_clie")
        partners_data = cr.fetchall()
        num_rows = len(partners_data)
        cont = 0
        for row in partners_data:
            partner_ids = self.search("res.partner", [('ref','=',str(int(row.default_code))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if partner_ids:
                vals = {'comercial': ustr(row.comercial),
                        'parent_id': False,
                        'name': ustr(row.name),
                        'is_company': True}
                if int(row.parent_id) != int(row.default_code):
                    partner_data = self.read("res.partner", partner_ids[0], ['parent_id'])
                    parent_ids = self.search("res.partner", [('ref','=',str(int(row.parent_id))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                    if parent_ids and (not partner_data['parent_id'] or parent_ids[0] != partner_data['parent_id'][0]):
                        vals['parent_id'] = parent_ids[0]
                        vals['is_company'] = False

                self.write("res.partner", [partner_ids[0]], vals)

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def fix_product_weight(self, cr):
        cr.execute("select pr1_codi, pr1_capl from dbo.adsd_art where pr1_capl > 0")
        products_data = cr.fetchall()
        cont = 0
        num_rows = len(products_data)
        for row in products_data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row[0]))),'|',('active', '=', True),('active', '=', False)])
            if product_ids:
                self.write("product.product", product_ids, {'weight': row[1] / 1000.0})
            cont += 1
            print "%s de %s" % (str(cont),str(num_rows))

    def import_partner_contacts(self, cr):
        cr.execute("SELECT clf_codi as partner_id_map, clf_dire as street,clf_pobl as city, clf_cpos as zipcode,clf_telf as phone,"
                   "clf_tfax as fax,nombre_contacto as name,carGO as function1,telefono_contacto as mobile,email_contacto as email,"
                   "nombre_contacto2 as name2,carGO2 as function2,telefono_contacto2 as mobile2,email_contacto2 as email2,"
                   "nombre_contacto3 as name3,carGO3 as function3,telefono_contacto3 as mobile3,email_contacto3 as email3 "
                   "FROM dbo.adsd_clf where nombre_contacto != '' or nombre_contacto2 != '' or nombre_contacto3 != ''")
        contacts_data = cr.fetchall()
        num_rows = len(contacts_data)
        cont = 0
        for row in contacts_data:
            partner_ids = self.search("res.partner", [('ref','=',str(int(row.partner_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if partner_ids:
                generic_vals = {}
                if row.street and row.street.strip():
                    generic_vals = {
                        'street': ustr(row.street),
                        'city': row.city and ustr(row.city) or '',
                        'zip': row.zipcode and ustr(row.zipcode) or '',
                        'fax': row.fax and ustr(row.fax) or '',
                        'use_parent_address': False,
                        'parent_id': partner_ids[0],
                        'phone': row.phone and ustr(row.phone) or ''
                    }
                if row.name and row.name.strip():
                    vals1 = {
                        'name': ustr(row.name),
                        'function': row.function1 and ustr(row.function1) or '',
                        'mobile': row.mobile and ustr(row.mobile) or '',
                        'email': row.email and ustr(row.email) or '',
                        'use_parent_address': True
                    }
                    vals1.update(generic_vals)
                    self.create("res.partner", vals1)
                if row.name2 and row.name2.strip():
                    vals2 = {
                        'name': ustr(row.name2),
                        'function': row.function2 and ustr(row.function2) or '',
                        'mobile': row.mobile2 and ustr(row.mobile2) or '',
                        'email': row.email2 and ustr(row.email2) or '',
                        'use_parent_address': True
                    }
                    vals2.update(generic_vals)
                    self.create("res.partner", vals2)
                if row.name3 and row.name3.strip():
                    vals3 = {
                        'name': ustr(row.name3),
                        'function': row.function3 and ustr(row.function3) or '',
                        'mobile': row.mobile3 and ustr(row.mobile3) or '',
                        'email': row.email3 and ustr(row.email3) or '',
                        'use_parent_address': True
                    }
                    vals3.update(generic_vals)
                    self.create("res.partner", vals3)

            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def update_product_sale_price(self, cr):
        cr.execute("select distinct tari_arti as default_code from dbo.adsd_tari")
        products_data = cr.fetchall()
        cont = 0
        num_rows = len(products_data)
        for row in products_data:
            product_ids = self.search('product.product', [('default_code', '=', str(int(row.default_code))),'|',('active','=',True),('active','=',False)])
            if product_ids:
                cr.execute("select top 1 tari_prec as lst_price from dbo.adsd_tari where tari_arti = ? order by tari_desd desc", (int(row.default_code),))
                row2 = cr.fetchone()
                if row2 and row2.lst_price:
                    self.write("product.product", [product_ids[0]], {"lst_price": row2.lst_price})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_customer_unilever_families(self, cr):
        cr.execute("SELECT cliente, familia FROM dbo.envio_clientes group by cliente, familia")
        data = cr.fetchall()
        cont = 0
        num_rows = len(data)
        for row in data:
            partner_ids = self.search("res.partner", [('ref', '=', str(int(row[0]))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if partner_ids:
                unilever_family_ids = self.search("res.partner.unilever.family", [('code', '=', str(int(row[1])))])
                if unilever_family_ids:
                    self.write("res.partner", partner_ids, {'unilever_family_id': unilever_family_ids[0]})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_items_data(self, cr):
        # Tipos de medios
        cr.execute("SELECT med_me01 as type_name FROM dbo.adsd_med")
        type_data = cr.fetchall()
        cont = 0
        num_rows = len(type_data)
        for row in type_data:
            vals = {'name': ustr(row.type_name)}
            rec_ids = self.search("item.management.item.type", [('name', '=', vals["name"])])
            if not rec_ids:
                self.create("item.management.item.type", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        #Medios
        cr.execute("SELECT matricula as license_plate,nombre_medio as name, nombre_medio as type_id_map, fco_nano as purchase_date_year, "
                   "codigo_cliente as partner_id_map, fco_capa as capacity, fco_fent as location_date, fecha_recuento as last_recount_date, "
                   "case when codigo_cliente = 0 then null else fco_cont end as contract_name, "
                   "case when fco_situ = 'T' then 'transfer' else 'customer' end as contract_type "
                   "FROM dbo.VW_medios_no_etiqueta inner join dbo.adsd_fco on fco_marc = matricula")
        items_data = cr.fetchall()
        cont = 0
        num_rows = len(items_data)
        for row in items_data:
            type_ids = self.search("item.management.item.type", [('name', '=', ustr(row.type_id_map))])
            item_vals = {'name': ustr(row.name),
                         'license_plate': ustr(row.license_plate),
                         'type_id': type_ids and type_ids[0] or False,
                         'purchase_date': datetime.date(int(row.purchase_date_year),1,1).strftime("%Y-%m-%d"),
                         'to_sync': False,
                         'capacity': row.capacity and float(str(row.capacity).replace(".","")) or 0.0,
                         'location_date': row.location_date.strftime("%Y-%m-%d %H:%M:%S"),
                         'location_id': not row.partner_id_map and 12 or False, #Stock
                         'partner_id': 1,
                         'situation': row.contract_type == 'transfer' and row.contract_type or (not row.partner_id_map and 'warehouse' or row.contract_type)}
            if row.partner_id_map:
                partner_ids = self.search("res.partner", [('ref', '=', str(int(row.partner_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                if partner_ids:
                    contract_vals = {
                        'name': str(int(row.contract_name)),
                        'description': str(int(row.contract_name)),
                        'partner_id': partner_ids[0],
                        'contract_type': row.contract_type,
                        'start_date': row.location_date.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    contract_id = self.create("item.management.contract", contract_vals)
                    self.execute("item.management.contract", "action_active", [contract_id])
                    item_vals.update({'contract_id': contract_id,
                                      'customer_id': partner_ids[0]})

            item_id = self.create("item.management.item", item_vals)
            if row.last_recount_date and row.last_recount_date >= datetime.datetime(2015,1,1,0,0,0):
                recount_ids = self.search("item.management.recount", [("state", '=', "open")])
                if recount_ids:
                    self.create("item.management.item.count", {'recount_id': recount_ids[0],
                                                               'recount_date': row.last_recount_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                               'item_id': item_id})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_cadena(self, cr):
        cr.execute("select cli_codi as partner_id_map, cli_asoc as parent_id_map from dbo.adsd_clie where cli_asoc != 0")
        child_partners = cr.fetchall()
        cont = 0
        num_rows = len(child_partners)
        for row in child_partners:
            if row.partner_id_map != row.parent_id_map:
                partner_id = self.search("res.partner", [('ref', '=', str(int(row.partner_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                if partner_id:
                    partner_data = self.read("res.partner", partner_id[0], ['parent_id'])
                    if not partner_data['parent_id']:
                        parent_ids = self.search("res.partner", [('ref', '=', str(int(row.parent_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
                        if parent_ids:
                            self.write("res.partner", [partner_id[0]], {'parent_id': parent_ids[0]})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_product_customer_rules(self, cr):
        cr.execute("SELECT cliente as customer_id_map,producto as product_id_map FROM dbo.VW_COLECCION_CLIENTES"
                   " inner join dbo.adsd_clie on dbo.adsd_clie.cli_codi = dbo.VW_COLECCION_CLIENTES.cliente"
                   " where cli_asoc = 0")
        data = cr.fetchall()
        cont = 0
        num_rows = len(data)
        for row in data:
            customer_ids = self.search("res.partner", [('ref', '=', str(int(row.customer_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if customer_ids:
                product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', True),('active', '=', False)])
                if product_ids:
                    try:
                        self.create("partner.rules", {'partner_id': customer_ids[0],
                                                  'product_id': product_ids[0],
                                                  'start_date': '2015-01-01',
                                                  'end_date': '2099-12-31'})
                    except:
                        pass
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_rappels(self, cr):
        cr.execute("SELECT cliente as customer_id_map,dbo.VW_condiciones_rappel.grupo as rappel_group_id_map,dbo.VW_condiciones_rappel.cadena as grouped, "
                   "dbo.VW_condiciones_rappel.contribucion as discount_assumed, dbo.VW_condiciones_rappel.subgrupo as rappel_subgroup_id_map, "
                   "dbo.VW_condiciones_rappel.dcto_fra as promotion, dbo.VW_condiciones_rappel.id as rappel_id,  "
                   "desde as start_date, hasta as end_date, nombre_cliente as name FROM dbo.VW_condiciones_rappel "
                   "inner join dbo.clientes_rappel on dbo.clientes_rappel.id = dbo.VW_condiciones_rappel.id where dbo.VW_condiciones_rappel.estado = 'A'")
        rappels_data = cr.fetchall()
        cont = 0
        num_rows = len(rappels_data)
        rappel_type = self.search("rappel.type", [])[0]
        for row in rappels_data:
            partner_ids = self.search("res.partner", [('ref', '=', str(int(row.customer_id_map))),('customer', '=', True),'|',('active', '=', True),('active', '=', False)])
            if partner_ids:
                if row.start_date:
                    start_date = row.start_date.strftime("%Y-%m-%d")
                else:
                    start_date = "2015-01-01"
                if row.end_date:
                    end_date = row.end_date.strftime("%Y-%m-%d")
                else:
                    end_date = "2999-12-31"

                subgroups = []
                group_supplier_id = False
                if row.rappel_subgroup_id_map:
                    subgroup_id = self._getRappelSubgroup_byInternalCode(str(int(row.rappel_subgroup_id_map)))
                    subgroup_data = self.read("product.rappel.subgroup", subgroup_id, ["code", "group_id"])
                    group_data = self.read("product.rappel.group", subgroup_data["group_id"][0], ["supplier_id"])
                    group_supplier_id = group_data["supplier_id"][0]
                    subgroups = [subgroup_data["code"]]
                else:
                    group_id = self._getRappelGroup_byInternalCode(str(int(row.rappel_group_id_map)))
                    group_data = self.read("product.rappel.group", group_id, ["subgroup_ids", "supplier_id"])
                    group_supplier_id = group_data["supplier_id"][0]
                    for subgroup  in group_data["subgroup_ids"]:
                        subgroup_data = self.read("product.rappel.subgroup", subgroup, ["code"])
                        subgroups.append(subgroup_data["code"])

                #promotion
                if row.promotion:
                    vals = {
                        "name": ustr(row.name),
                        "from_date": start_date,
                        "to_date": end_date,
                        "login": "and",
                        "expected_logic_result": "True",
                        "sequence": 1,
                        'customer_ids': [(6,0,partner_ids)]
                    }
                    promoton_id = self.create("promos.rules", vals)

                    for subgroup in subgroups:
                        action_vals = {
                            "action_type": "prod_disc_perc_sub",
                            "product_code": "'" + subgroup + "'",
                            "arguments": str(float(row.promotion)),
                            "promotion": promoton_id,
                            "sequence": 1
                        }
                        action = self.create("promos.rules.actions", action_vals)

                        rule_vals = {
                            'stop_further': True,
                            'attribute': "subgroup",
                            'comparator': 'in',
                            'value': "'" + subgroup + "'",
                            'promotion': promoton_id,
                            "sequence": 1
                        }
                        self.create("promos.rules.conditions.exps", rule_vals)

                    if row.discount_assumed and group_supplier_id:
                        comp_promo_vals = {'start_date': start_date,
                                           'end_date': end_date,
                                           'supplier_id': group_supplier_id,
                                           'type': 'discount',
                                           'promotion_id': promoton_id,
                                           'discount_assumed': float(row.discount_assumed)}
                        self.create("sale.joint.promotion", comp_promo_vals)

                # Rappel
                if row.rappel_id:
                    cr.execute("select hasta as rappel_until, porcentaje as percentage from dbo.clientes_rappel_escalado"
                               " where id_rappel = ? order by linea asc", (int(row.rappel_id),))
                    sections_data = cr.fetchall()
                    rappel_from = 0
                    sections = []
                    for section in sections_data:
                        if section.percentage:
                            vals = {'rappel_until': float(section.rappel_until),
                                    'percent': float(section.percentage),
                                    'rappel_from': rappel_from}
                            rappel_from = float(section.rappel_until)
                            sections.append((0,0,vals))
                    if sections:
                        rappel_vals = {'type_id': rappel_type,
                                       'name': ustr(row.name),
                                       'date_start': start_date,
                                       'date_stop': end_date,
                                       'periodicity': 'annual',
                                       'global_application': False,
                                       'rappel_subgroup_id': row.rappel_subgroup_id_map and subgroup_id or False,
                                       'rappel_group_id': not row.rappel_subgroup_id_map and group_id or False,
                                       'grouped': row.grouped == 'S' and True or False,
                                       'invoice_grouped': row.grouped == 'S' and True or False,
                                       'calc_amount': 'percent',
                                       'customer_ids': [(6,0,partner_ids)]}
                        if len(sections) == 1:
                            rappel_vals['calc_mode'] = 'fixed'
                            rappel_vals['fix_qty'] = sections[0][2]['percent']
                        else:
                            rappel_vals['calc_mode'] = 'variable'
                            rappel_vals['calc_type'] = 'monetary'
                            rappel_vals['sections'] = sections
                        rappel_id = self.create("rappel", rappel_vals)

                        if row.discount_assumed and group_supplier_id:
                            comp_promo_vals = {'start_date': start_date,
                                               'end_date': end_date,
                                               'supplier_id': group_supplier_id,
                                               'type': 'rappel',
                                               'rappel_id': rappel_id,
                                               'discount_assumed': float(row.discount_assumed)}
                            self.create("sale.joint.promotion", comp_promo_vals)


            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_product_rappel_groups(self, cr):
        cr.execute("select pr1_codi as product_id_map, subgrupo_rappel as subgroup_map_id, codigo_ean_unidad as ean_consum from dbo.adsd_art where subgrupo_rappel is not null")
        prod_data = cr.fetchall()
        cont = 0
        num_rows = len(prod_data)
        for row in prod_data:
            product_ids = self.search('product.product', [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', True),('active', '=', False)])
            if product_ids:
                subgroup_ids = self.search("product.rappel.subgroup", [("internal_code", '=', str(row.subgroup_map_id))])
                if subgroup_ids:
                    subgroup_data = self.read("product.rappel.subgroup", subgroup_ids[0], ['group_id'])
                    self.write("product.product", product_ids, {'rappel_subgroup_id': subgroup_ids[0],
                                                                'ean_consum': row.ean_consum != 0 and str(int(row.ean_consum)) or False,
                                                                'rappel_group_id':  subgroup_data['group_id'] and subgroup_data['group_id'][0] or False})
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def process_data(self):
        """
        Importa la bbdd
        """
        print "Intentamos establecer conexion"
        try:
            #
            # Nos conectamos a la bbdd de sql server
            #
            conn = pyodbc.connect("DRIVER={FreeTDS};SERVER=" + self.sql_server_host + ";UID=midban;PWD=midban2015;DATABASE=gest2015;Port=1433;TDS_Version=10.0")
            cr = conn.cursor()

            #self.import_product_category(cr)
            #self.import_products(cr)
            #self.import_customers(cr)
            #self.import_suppliers(cr)
            #self.import_indirect_customer(cr)
            #self.import_rel_product_supplier(cr)
            #self.fix_products(cr)
            #self.import_bank_accounts(cr)
            #self.import_master_frigo_data(cr)
            #self.import_product_frigo_data(cr)
            #self.update_product_sale_price(cr)
            #self.import_other_prices(cr)
            #self.import_customers_other_data(cr)
            #self.import_preferential_agree_data(cr)
            #self.import_tourism_data(cr)
            #self.import_giras(cr)
            #self.fix_customer_names(cr)
            #self.fix_product_weight(cr)
            #self.import_partner_contacts(cr)
            #self.import_customer_unilever_families(cr)
            #self.import_items_data(cr)
            #self.import_cadena(cr)
            #self.import_product_customer_rules(cr)
            #self.import_rappels(cr)
            self.import_product_rappel_groups(cr)


        except Exception, ex:
            print u"Error al conectarse a las bbdd: ", repr(ex)
            sys.exit()

        self.file.write(u"Iniciamos la Importacion\n\n")


        #cerramos el fichero
        self.file.close()

        return True

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print u"Uso: %s <dbname> <user> <password> <sql_server_host>" % sys.argv[0]
    else:
        ENGINE = DatabaseImport(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

        ENGINE.process_data()
