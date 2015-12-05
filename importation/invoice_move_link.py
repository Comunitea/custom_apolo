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
            logfile_diff = open('log_invoices_amount_diff.csv', 'w') # Indicamos el valor 'w'.
            logfile_no_found = open('log_invoices_no_found.csv', 'w')

            invoice_ids = self.search('account.invoice', [('state','=','history'),
                                                          ('type','=','out_invoice'),
                                                          ('amount_total', '>', 0),
                                                          ('move_id', '=', False),
                                                          ('date_invoice', '<>', False)],
                                      order="date_invoice DESC")
            total = len(invoice_ids)
            num=0
            realizadas = 0
            print u"Iniciando asociación  movimientos para un total de: %s facturas"%(total)
            for invoice_id in invoice_ids:
                invoice = self.read('account.invoice', invoice_id, ['number', 'id',
                                                                    'amount_total', 'partner_id',
                                                                    'date_invoice', 'date_due'])
                separ = invoice['number'].split('/')
                move_ref_pre = separ[0] + "/"
                move_ref_post = "0000" + separ[1]
                move_ref_post = move_ref_post[-7:]
                move_ref = move_ref_pre + move_ref_post
                domain = [('account_id.type', '=', 'receivable'),
                        ('ref', 'like', move_ref)]
                print "Buscando %s : %s - %s  "%(move_ref,invoice['date_invoice'], invoice['amount_total'])
                move_ids = self.search('account.move.line',domain)

                if move_ids:
                    if len(move_ids) == 1:
                        print u"ENCONTRADA REFERENCIA para %s"%(invoice['number'])
                        moves = self.read('account.move.line', move_ids, ['move_id', 'debit'])
                        if self.isclose(moves[0]['debit'], invoice['amount_total'],0.2,0.2):
                            if invoice['date_due']:
                                date_due = invoice['date_due']
                            else:
                                date_due = invoice['date_invoice']
                            vals = {
                                'move_id': moves[0]['move_id'][0],
                                'date_due': date_due
                            }
                            self.write('account.invoice', invoice['id'], vals)
                            vals = {
                                'date_maturity': date_due
                            }
                            self.write('account.move.line', move_ids[0], vals)
                            print u"HECHO   para %s %s"%(invoice['number'],invoice['amount_total'])
                            realizadas += 1
                        else:
                            print u"IMPORTES DIFERENTES para %s: %s(asiento) -  %s(factura)"%(invoice['number'],
                                                                                              moves[0]['debit'], invoice['amount_total'])
                            logfile_diff.write("%s,%s,%s\n"%(invoice['number'],moves[0]['debit'], invoice['amount_total']))
                    else:
                        print u"Más de un Asiento no encontrado  para %s"%(invoice['number'])
                else:
                    print u"Asiento no encontrado  para %s"%(invoice['number'])
                    logfile_no_found.write("%s\n"%(invoice['number']))
                num +=1
                print u"Procesado %s : %s/%s/%s"%(invoice['number'],realizadas, num, total)
            print "FINALIZado!!. No conciliados procesados TOTAL:"
            logfile_diff.close()
            logfile_no_found.close()
        except Exception, e:
            print u"EXCEPTION: REC %s"%(e)
            print "No conciliados procesados hasta el momento:"
            logfile_diff.close()
            logfile_no_found.close()
        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password>" % sys.argv[0]
    else:
        invoice_move(sys.argv[1], sys.argv[2], sys.argv[3])
