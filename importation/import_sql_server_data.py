# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import traceback

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
                "description": (row.description and ustr(row.description) or "") + (row.base_use_sale != "F" and "\nBLOQUEADO" or ""),
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

            self.import_product_category(cr)
            self.import_products(cr)

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
