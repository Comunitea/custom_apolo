# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import traceback
import time

PRODUCT_FIX = {
    '200102': 12, '140606': 3, '140612': 2, '140614': 6, '140613': 3, '130113': 8, '130109': 12,
    '247201': 6, '101301': 6, '101303': 6, '101304': 6, '101305': 6, '4127': 6, '101401': 6,
    '235112': 12, '130101': 16, '130116': 16, '130114': 8, '247231': 100, '205101': 6,
    '4426': 5, '4791': 10, '4790': 10, '130115': 8, '302102': 12, '11130': 4, '247207': 6,
    '247206': 6, '247208': 6, '247209': 6, '100701': 6, '423': 6, '4634': 6, '4132': 12,
    '125': 4, '4131': 12, '140701': 4, '4112': 12, '4108': 12, '4111': 12, '247210': 6,
    '304': 5, '247212': 6, '100602': 12, '100601': 12, '230105': 12, '4159': 4, '4145': 6,
    '4146': 6, '4140': 6, '4106': 5, '4115': 5, '101402': 6, '9257': 6, '44405': 6,
    '247214': 6, '539502': 4, '225203': 12, '225204': 6, '4177': 10, '4113': 6, '4107': 6,
    '4114': 6, '4123': 12, '4101': 10, '247230': 6, '230114': 12, '100301': 6, '225103': 12,
    '225104': 12, '225105': 4, '4122': 10, '4119': 6, '225403': 12, '225404': 6, '4205': 12,
    '4610': 6, '4607': 6, '4608': 6, '4600': 6, '247216': 6, '247217': 6, '661101': 10,
    '225502': 4, '4821': 12, '247218': 6, '247229': 6, '247219': 6, '247220': 6, '247222': 6,
    '247223': 6, '101201': 6, '101202': 6, '101203': 6, '101204': 24, '686': 3, '247224': 6,
    '428': 6, '427': 6, '113': 10, '4470': 3, '247101': 6, '89': 5, '302201': 6, '4801': 12,
    '230120': 12, '4121': 25, '100802': 6, '100804': 3, '247227': 6, '4820': 12, '245101': 12,
    '100201': 6, '3003': 24, '3004': 12, '3021': 10, '3008': 40, '3012': 40, '3033': 6, '3024': 10,
    '3025': 1, '10173': 23
}

PRODUCT_VAR = {'821': 1, '120': 5, '117': 1.5, '541117': 3.5, '820': 1, '124': 1.5, '531108': 3.5,
               '685': 3.5, '531103': 4, '531110': 2.5, '632': 1.2, '680': 1.5, '531109': 2.5,
               '510403': 0.7, '819': 1, '614': 0.7, '551205': 5.5, '531217': 0.8, '541206': 3.5,
               '541207': 4.5, '531107': 2.5, '92': 3.5, '617': 0.35, '620': 1, '531111': 2.5,
               '531211': 1.4, '4420': 1.5, '658': 2.6, '93': 0.9}

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
        self.port = 9069
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

    def execute(self, model, method, args = [], context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, method, *args, **context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def import_lots(self, cr):
        cr.execute("select REF_PROD as product_id_map, NUM_LOTE as name, MAX(FECHA_CAD) as life_date from dbo.TB_ESTOCA where NUM_LOTE != '' group by REF_PROD,NUM_LOTE")
        data = cr.fetchall()
        num_rows = len(data)
        print "Numero de lotes: ", (num_rows)
        cont = 0
        for row in data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', False),('active', '=', True)])
            if product_ids:
                lot_ids = self.search("stock.production.lot", [('product_id', '=', product_ids[0]),('name','=',row.name)])
                if not lot_ids:
                    lot_vals = {'product_id': product_ids[0],
                                'name': row.name,
                                'life_date': row.life_date and row.life_date.strftime("%Y-%m-%d %H:%M:%S") or False,
                                'removal_date': row.life_date and row.life_date.strftime("%Y-%m-%d %H:%M:%S") or False}
                    lot_id = self.create("stock.production.lot", lot_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_packages(self, cr):
        cr.execute("select distinct REF_PROD as product_id_map,NUM_PALET as name from dbo.TB_ESTOCA")
        data = cr.fetchall()
        num_rows = len(data)
        print "Numero de paquetes: ", (num_rows)
        cont = 0
        for row in data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', False),('active', '=', True)])
            if product_ids:
                product_data = self.read("product.product", product_ids[0], ["uom_id"])
                package_vals = {'name': row.name,
                                'uos_id': product_data["uom_id"][0]}
                self.create("stock.quant.package", package_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))

    def import_stock(self, cr):
        inv_id = self.create("stock.inventory", {"name": "Inventario inicial"})
        cr.execute("select case CAM when '' then null else CAM + EST + RIGHT('0'+convert(varchar,FIL),2) + RIGHT('0'+convert(varchar,PIS),2)end as location_id_map, "
                   "REF_PROD as product_id_map, NUM_LOTE as lot_id_map, NUM_PALET as package_id_map, UNIDADES as box_qty, COMPOS as unit_qty from dbo.TB_ESTOCA")
        data = cr.fetchall()
        num_rows = len(data)
        print "Numero de stocks: ", (num_rows)
        cont = 0
        for row in data:
            product_ids = self.search("product.product", [('default_code', '=', str(int(row.product_id_map))),'|',('active', '=', False),('active', '=', True)])
            if product_ids:
                product_data = self.read("product.product", product_ids[0], ["uom_id", "log_unit_id", "log_base_id", "log_box_id"])
                loc_qty = row.box_qty
                if str(int(row.product_id_map)) in PRODUCT_FIX:
                    loc_qty = loc_qty / PRODUCT_FIX[str(int(row.product_id_map))]
                elif str(int(row.product_id_map)) in PRODUCT_VAR:
                    loc_qty = loc_qty * PRODUCT_VAR[str(int(row.product_id_map))]

                if row.unit_qty:
                    if product_data["log_base_id"]:
                        unit = product_data["log_base_id"][0]
                    elif product_data["log_unit_id"]:
                        unit = product_data["log_unit_id"][0]
                    else:
                        unit = product_data["log_box_id"][0]
                    if unit:
                        print "initial loc_qty: ", loc_qty
                        loc_qty += self.execute("product.product", "uos_qty_to_uom_qty", [product_ids[0], row.unit_qty, unit])
                        print "end loc_qty: ", loc_qty

                if row.lot_id_map and row.lot_id_map.strip() != "":
                    lots_ids = self.search("stock.production.lot", [('product_id', '=', product_ids[0]),('name', 'ilike', row.lot_id_map)])
                    if not lots_ids:
                        raise Exception("No se ha podido encontrar el lote n: %s" % row.lot_id_map)
                else:
                    self.write("product.product", [product_ids[0]], {'track_all': False, 'track_incoming': False, 'track_outgoing': False})
                    lots_ids = []
                if row.package_id_map:
                    package_ids = self.search("stock.quant.package", [('name', '=', row.package_id_map)])
                    if not package_ids:
                        raise Exception("No se ha podido encontrar el lote n: %s" % row.package_id_map)
                    elif len(package_ids) > 1:
                        raise Exception("Hay más de un paquete con número %s" % row.package_id_map)
                else:
                    package_ids = []
                if row.location_id_map:
                    location_ids = self.search("stock.location", [('bcd_code', '=', row.location_id_map)])
                    if not location_ids:
                        raise Exception("No se ha podido encontrar la ubicacion: %s" % row.location_id_map)
                else:
                    location_ids = self.search("stock.location", [('special_location', '=', True)])
                    if not location_ids:
                        raise Exception("No se ha podido encontrar una ubicación especial")

                if loc_qty > 0:
                    inv_line_vals = {'inventory_id': inv_id,
                                     'product_id': product_ids[0],
                                     'product_qty': loc_qty,
                                     'product_uom_id': product_data["uom_id"][0],
                                     'location_id': location_ids[0],
                                     'prod_lot_id': lots_ids and lots_ids[0] or False,
                                     'package_id': package_ids and package_ids[0] or False}
                    self.create("stock.inventory.line", inv_line_vals)
            cont += 1
            print "%s de %s" % (str(cont), str(num_rows))
        self.execute("stock.inventory", "prepare_inventory", [[inv_id]])
        self.execute("stock.inventory", "action_done", [[inv_id]])

    def process_data(self):
        """
        Importa la bbdd
        """
        print "Intentamos establecer conexion"
        try:
            #
            # Nos conectamos a la bbdd de sql server
            #
            conn = pyodbc.connect("DRIVER={FreeTDS};SERVER=" + self.sql_server_host + ";UID=midban;PWD=midban2015;DATABASE=GestMag_APOLO;Port=1433;TDS_Version=10.0")
            cr = conn.cursor()

            self.import_lots(cr)
            self.import_packages(cr)
            self.import_stock(cr)

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
