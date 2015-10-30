#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback
import psycopg2

class fix_stock_location(object):
    def __init__(self, dbname, user, passwd, loc_name):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 8069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.loc_name = loc_name

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
        def get_ids(code):
            max_id = False
            min_id = False
            pool = self.search('stock.location', [('bcd_code', 'ilike', code)], order = 'id desc')
            if len(pool) == 2:
                max_id = pool[0]
                min_id = pool[1]
            return max_id, min_id



        product_pool = self.search('product.product', [('short_name', 'like','')])

        for product in product_pool:
            #import ipdb; ipdb.set_trace()
            loc = self.read('stock.location', loc_, ['bcd_code'])
            print loc['bcd_code']
            max_id, min_id = get_ids(loc['bcd_code'])
            if min_id:
                print "Operacion: %s Se cambia de %s a %s"%(loc, min_id, max_id)
                #cambiamos en stock_pack_operation


                op_pool = self.search('stock.pack.operation', [('location_dest_id', '=', min_id)])
                val ={'location_dest_id': max_id}
                for op in op_pool:
                    self.write('stock.pack.operation', op, val)

                op_pool = self.search('stock.pack.operation', [('location_id', '=', min_id)])
                val ={'location_id': max_id}
                for op in op_pool:
                    self.write('stock.pack.operation', op, val)

                op_pool = self.search('stock.quant', [('location_id', '=', min_id)])
                val ={'location_id': max_id}
                for op in op_pool:
                    self.write('stock.quant', op, val)
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

                op_pool = self.search('stock.location', [('location_id', '=', min_id)])
                val ={'location_id': max_id}
                for op in op_pool:
                    self.write('stock.location', op, val)

                op_pool = self.search('product.product', [('picking_location_id', '=', min_id)])
                val ={'picking_location_id': max_id}
                for op in op_pool:
                    self.write('product.product', op, val)

                op_pool = self.search('stock.location', [('id', '=', min_id)])
                val ={'active': False}
                for op in op_pool:
                     self.write('stock.location', op, val)

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <location to fix>" % sys.argv[0]
    else:
        fix_stock_location(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
