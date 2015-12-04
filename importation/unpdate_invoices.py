#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback

class invoice_move(object):
    def __init__(self, dbname, user, passwd):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = 9069
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd
            self.no_conciliados =[]

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.invoice_move_link()
            #con exito
            if res:
                print ("!!!!!All concilied!!!!!!!")
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

    def getSupplierByRef(self, partner_ref):
        partner_ids = self.search("res.partner", [('supplier','=',True),('ref','=',partner_ref)])
        return partner_ids and partner_ids[0] or False

    def getTaxes(self, tax_name):
        tax_ids = self.search("account.tax", [('name', '=', tax_name)])
        return tax_ids

    def getUomByName(self, uom_name):
        uom_ids = self.search("product.uom", [('name', '=', uom_name)])
        return uom_ids and uom_ids[0] or False

    def getCategoryByName(self, categ_name):
        categ_ids = self.search("product.category", [('name', '=', categ_name)])
        if not categ_ids:
            categ_id = self.create("product.category", {"name": categ_name})
            categ_ids = [categ_id]
        return categ_ids and categ_ids[-1] or False

    def isclose(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


    def invoice_move_link(self):
        try:
            invoice_ids = self.search('account.invoice', [('fiscal_position', '=', False)],
                                      order="date_invoice DESC")
            total = len(invoice_ids)
            num=0
            realizadas = 0
            print u"Iniciando asociación  movimientos para un total de: %s facturas"%(total)
            for invoice_id in invoice_ids:
                invoice = self.read('account.invoice', invoice_id, ['id', 'number','amount_total', 'partner_id',
                                                                    'date_invoice', 'date_due',
                                                                    'invoice_line'])
                print u"Comprobando %s"%(invoice['number'])
                partner_id = invoice['partner_id'][0]
                #partner_ids = self.search('res.partner',[('id','=',partner_id)])
                partner = self.read('res.partner', partner_id, ['property_account_position'])
                #moves = self.read('account.move.line', move_ids, ['move_id'])
                fpos_ob = partner['property_account_position']
                if fpos_ob:
                    fpos= fpos_ob[0]
                else:
                    fpos =0
                if fpos:
                    vals = {'fiscal_position':fpos}
                    res = self.write('account.invoice', invoice_id, vals)

                if fpos != 0 and fpos != 1: # DOMICILIO RECALCULA
                    print u"Ha domicilio %s"%(invoice['number'])
                    ils = self.read('account.invoice.line',  invoice['invoice_line'], ['id', 'product_id',
                                                                                      'invoice_line_tax_id'])
                    for line in ils:
                        taxes = self.execute('account.fiscal.position','map_tax_id', fpos,
                                     line['invoice_line_tax_id'])
                        vals = {
                            'invoice_line_tax_id': [(6,0,taxes)]
                        }
                        res= self.write('account.invoice.line', line['id'], vals)
                    self.execute('account.invoice','button_reset_taxes', invoice_id)
                    print u"HECHO para %s"%(invoice['number'])
                    realizadas += 1
                num +=1
                print u"Procesado %s : %s/%s/%s"%(invoice['number'],realizadas, num, total)
            print "FINALIZado!!. No conciliados procesados TOTAL:"

        except Exception, e:
            print u"EXCEPTION: REC %s"%(e)
            print "No conciliados procesados hasta el momento:"

        return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password>" % sys.argv[0]
    else:
        invoice_move(sys.argv[1], sys.argv[2], sys.argv[3])
