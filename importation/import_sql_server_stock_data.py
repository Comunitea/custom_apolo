# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import pyodbc
import traceback
import time

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
                                'life_date': row.life_date and row.life_date.strftime("%Y-%m-%d %H:%M:%S") or False}
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
