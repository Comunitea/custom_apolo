# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import time

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

def ustr(text):
    """convierte las cadenas de sql server en iso-8859-1 a utf-8 que es la cofificaciï¿œn de postgresql"""
    return unicode(text.strip(), 'iso-8859-15').encode('utf-8')

class DatabaseImport:
    """
    Importa a OpenERP datos de una base de datos SqlServer para Calor Color.
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

    def search(self, model, query, context={}):
        """
        Wrapper del método search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, context)
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

    def _getTaxes(self, tax_name):
        tax_ids = self.search("account.tax", [('description', '=', tax_name)])
        return tax_ids

    def _getTempType_byName(self, temp_name):
        temp_ids = self.search("temp.type", [("name", "=", temp_name)])
        return temp_ids and temp_ids[0] or False

    def _get_bank_by_bic(self, bank_bic):
        bank_ids = self.search("res.bank", [("bic", '=', bank_bic)])
        return bank_ids and bank_ids[0] or False

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
                            "supp_ca_ma": row.supp_ca_ma or 0,
                            "supp_ma_pa": row.supp_ma_pa or 0,
                            "var_coeff_un": row.var_coeff_un == "V" and True or False}

                    if row.uom_id_map.strip() == "C":
                        vals["log_box_id"] = uom_id
                        vals["box_use_purchase"] = True
                        if row.uomb_map.strip() not in ["L", "K"]:
                            vals["supp_un_ca"] = row.supp_kg_un
                            vals["supp_kg_un"] = 1
                        else:
                            vals["supp_kg_un"] = row.supp_kg_un
                            vals["supp_un_ca"] = 1
                    elif row.uom_id_map.strip() == "U":
                        vals["log_unit_id"] = uom_id
                        vals["unit_use_purchase"] = True
                        vals["supp_kg_un"] = row.supp_kg_un
                    else:
                        vals["log_base_id"] = uom_id
                        vals["base_use_purchase"] = True
                        vals["supp_kg_un"] = 1
                    if uom_id != uob_id:
                        if row.uomb_map.strip() == "U":
                            vals["log_unit_id"] = uob_id
                        else:
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
                    'code': row.code != '00' and row.code or str(int(row.internal_code))}
            self.create("product.rappel.group", vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

        print "Subgrupo rappel"
        cr.execute("select codigo as internal_code, descripcion as name, grupo_rappel as group_id_map, informe_frigo as code from dbo.subgrupo_rappel")
        rappel_subgroup_data = cr.fetchall()
        num_rows = len(rappel_subgroup_data)
        cont = 0
        for row in rappel_subgroup_data:
            rappel_group_ids = self.search("product.rappel.group", [('internal_code', '=', str(int(row.internal_code)))])
            vals = {'internal_code': str(int(row.internal_code)),
                    'name': ustr(row.name),
                    'group_id': rappel_group_ids and rappel_group_ids[0] or False,
                    'code': row.code != '00' and row.code or str(int(row.internal_code))}
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
                    subgroup_ids = self.search("product.rappel.subgroup", [("code", '=', row.rappel_subgroup_id_map)])
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
            self.import_other_prices(cr)

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
