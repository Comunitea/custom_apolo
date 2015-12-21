#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback

class fix_stock_location(object):
    def __init__(self, dbname, user, passwd, loc_name):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = 'odoo_PRO_ultima'
            self.user_name = 'admin'
            self.user_passwd = 'AdminApolo15'
            self.loc_name = 5

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.fix_stock_location()
            #con exito
            if res:
                print ("All created")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

        #Métodos Xml-rpc

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del metodo create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                            model, 'create', data, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))


    def search(self, model, query, offset=0, limit=False, order=False, context={}, count=False, obj=1):
        """
        Wrapper del metodo search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'search', query, offset, limit, order, context, count)
            return ids
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))


    def read(self, model, ids, fields, context={}):
        """
        Wrapper del metodo read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                            model, 'read', ids, fields, context)
            return data
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))


    def write(self, model, ids, field_values,context={}):
        """
        Wrapper del metodo write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))


    def unlink(self, model, ids, context={}):
        """
        Wrapper del metodo unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                    raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del metodo default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                        model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
                raise Exception('Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, *args, **kw):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                                model, method, *args, **kw)
            return res
        except socket.error, err:
                raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))

    def fix_stock_location(self):

        inventory_id = 5
        #lista de paquetes en inventario
        packages_en_inventario = self.search('stock.quant.package', [('location_id', '=', inventory_id)], order = 'id ASC')
        #import ipdb; ipdb.set_trace()
        for old_package in packages_en_inventario:

            #buscamos los quants en cada paquete
            quants_in_package = self.search('stock.quant', [('package_id', '=', old_package)])

            if quants_in_package:
                name = self.read('stock.quant.package', old_package, ['name'])
                print "Trato el paquete nº %s"%name
                vals = {'location_id': inventory_id}
                new_package = self.create('stock.quant.package', vals)
                new_name = self.read('stock.quant.package', new_package, ['name'])
                new_location_old_package = False
                for quant in quants_in_package:
                    #cogemos la location_id de cada quant
                    loc = self.read('stock.quant', quant, ['location_id'])
                    quant_location = loc['location_id'][0]
                    #si está en inventario, lo movemos al paquete nuevo

                    if quant_location == inventory_id:
                        print "Quant en Inventario, lo muevo a paquete %s"%new_package
                        val = {'package_id': new_package}
                        write = self.write('stock.quant', quant, val)
                    else:
                        new_location = self.read('stock.location', quant_location, ['bcd_name'])
                        print "Quant en ubicación, %s"%new_location
                        new_location_old_package = quant_location

                if new_location_old_package:
                    val_loc = {'location_id': new_location_old_package}
                    write =  self.write('stock.quant.package', old_package, val_loc)


                #
                # op_pool = self.search('stock.move', [('location_id', '=', min_id)])
                # val ={'location_id': max_id}
                #
                # conn_string = "dbname='TEST_odoo_apolo' user='admin' password='AdminApolo15'"
                # conn = psycopg2.connect(conn_string)
                # cursor = conn.cursor()
                # sql = "update from %s set %s=%s where %s = %s"%('stock_move', 'location_id', max_id, 'location_id', min_id )
                # cursor.execute(sql)
                # conn.cursor
                #
                # for op in op_pool:
                #     self.write('stock.move', op, val)
                #
                # op_pool = self.search('stock.move', [('location_dest_id', '=', min_id)])
                # val ={'location_dest_id': max_id}
                # for op in op_pool:
                #     self.write('stock.move', op, val)

                # op_pool = self.search('stock.location', [('location_id', '=', min_id)])
                # val ={'location_id': max_id}
                # for op in op_pool:
                #     self.write('stock.location', op, val)
                #
                # op_pool = self.search('product.product', [('picking_location_id', '=', min_id)])
                # val ={'picking_location_id': max_id}
                # for op in op_pool:
                #     self.write('product.product', op, val)
                #
                # op_pool = self.search('stock.location', [('id', '=', min_id)])
                # val ={'active': False}
                # for op in op_pool:
                #      self.write('stock.location', op, val)

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <location to fix>" % sys.argv[0]
    else:
        fix_stock_location(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
