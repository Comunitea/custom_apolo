#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback
import xlrd

class import_customers(object):
    def __init__(self, dbname, user, passwd, customers_file):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 8069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.customers_file = customers_file

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.import_customer()
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


    def import_customer(self):
        partner_hierarchy = {}
        unregister_reason = "Baja en importación"
        unregister_id = self.search("unregister.partner.reason", [("name", '=', unregister_reason)])
        if not unregister_id:
            print u"Por favor cree el motivo de baja '%s'" % unregister_reason
        cwb = xlrd.open_workbook(self.customers_file, encoding_override="utf-8")
        sh = cwb.sheet_by_index(0)

        cont = 1
        all_lines = sh.nrows - 1
        print "partners no: ", all_lines

        for rownum in range(1, all_lines):
            record = sh.row_values(rownum)
            try:
                partner_vals = {
                    "customer": True,
                    "ref": str(int(record[0])),
                    "comercial": record[1],
                    "name": record[2],
                    "street": record[3],
                    "zip": record[4],
                    "phone": record[6],
                    "city":  record[9],
                    "comment": False
                }
                if record[11]: #Baja
                    partner_vals['state2'] = "unregistered"
                    partner_vals['unregister_reason_id'] = unregister_id[0]
                    partner_vals['comment'] = "Fecha de baja: " + str(record[11])

                if int(recod[0]) != int(record[10]):
                    partner_vals['comment'] = partner_vals['comment'] and partner_vals['comment']  + u"\nCODIGO_AGRUPA: " + str(int(record[10])) or u"CODIGO_AGRUPA: " + str(int(record[10]))

                if record[5] and int(record[5]):
                    if int(record[5]) > int(record[0]):
                        if partner_hierarchy.get(int(record[5])):
                            partner_hierarchy[int(record[5])].append(int(record[0]))
                        else:
                            partner_hierarchy[int(record[5])] = [int(record[0])]
                    elif int(record[5]) < int(record[0]):
                        parent_id = self.search("res.partner", [('customer', '=', True),("ref", '=', str(int(record[5]))),'|',('active', '=', False),('active', '=', True)])
                        if parent_id:
                            partner_vals["parent_id"] = parent_id[0]
                else:
                    partner_vals["is_company"] = True

                partner_id = self.create("res.partner", partner_vals)

                if not record[5] or not int(record[5]):
                    if partner_hierarchy.get(int(record[0])):
                        for partner in partner_hierarchy[int(record[0])]:
                            child_id = self.search("res.partner", [('customer', '=', True),("ref", '=', str(partner)),'|',('active', '=', False),('active', '=', True)])
                            if child_id:
                                self.write("res.partner", [child_id[0]], {'parent_id': partner_id})
                        del partner_hierarchy[int(record[0])]

                if record[7] and len(record[7]) in [9,10]:
                    vat = u"ES" + record[7].upper().replace(" ", "").replace("-","")
                    try:
                        self.write("res.partner", [partner_id], {'vat': vat})
                    except:
                        print u"CIF no váĺido en España", record[7]

                print "%s de %s" % (cont, all_lines)
                cont += 1
            except Exception, e:
                print "EXCEPTION: REC: %" % (record), e

        print u"Pendientes de jerarquía: ", partner_hierarchy
        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <customers.xls>" % sys.argv[0]
    else:
        import_customers(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
