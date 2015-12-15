#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback
import unicsv
from datetime import datetime
import csv

class integrate_accounting(object):
    def __init__(self, dbname, user, passwd, import_file):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.import_file = import_file

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.import_accounting_file()
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


    def import_accounting_file(self):
        row_count = sum(1 for row in csv.reader(open(self.import_file))) - 1
        cont = 0
        account_map = {'400900014': 1613,
                       '400900015': 1736,
                       }
        search_account_id = 402
        with open(self.import_file) as csvfile:
            reader = unicsv.UnicodeCSVDictReader(csvfile, delimiter=';', encoding="iso-8859-1")
            for row in reader:
                try:
                    last_date = datetime.strftime(datetime.strptime(row['Fecha'], "%d-%m-%Y"),"%Y-%m-%d")
                    move_ids = self.search('account.move', [('name', '=', str(int(row['Referencia']))),('date', '=', last_date)])
                    if move_ids:
                        self.execute('account.move', 'button_cancel' ,[move_ids[0]])
                        search_domain = [('account_id', '=', search_account_id),('move_id', '=', move_ids[0])]
                        debit = 0.0
                        credit = 0.0
                        if row.get('Debe', False):
                            debit_t = float(row['Debe'].replace(",", "."))
                            if debit_t < 0:
                                credit = abs(debit_t)
                            else:
                                debit = debit_t
                        if row.get('Haber', False):
                            credit_t = float(row['Haber'].replace(",", "."))
                            if credit_t < 0:
                                debit = abs(credit_t)
                            else:
                                credit = credit_t
                        if debit:
                            search_domain.append(('debit', '=', debit))
                        else:
                            search_domain.append(('credit', '=', credit))
                        lines_ids = self.search('account.move.line', search_domain)
                        if lines_ids:
                            self.write('account.move.line', [lines_ids[0]], {'account_id': account_map[row['Cuenta']]})
                        self.execute('account.move', 'post' ,[move_ids[0]])
                    cont+= 1
                    print "%s de %s" % (cont, row_count)
                except Exception, e:
                    print "EXCEPTION: REC: ", row, e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <file_to_import.xls>" % sys.argv[0]
    else:
        integrate_accounting(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
