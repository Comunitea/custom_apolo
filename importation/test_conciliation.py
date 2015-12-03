#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket
import traceback

class conciliation(object):
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

            res = self.run_concilie()
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

    def try_concilie(self, customer, move_list):
        def sum_list(move_list):
            debit = 0
            credit =0
            for move in move_list:
                debit += move['debit']
                credit += move['credit']
            return [debit, credit]

        def busca_move(move_list, amnt):
            num=0
            res =[]
            suma = 0
            diff = amnt
            testing =[]
            print u"Buscando con importe %s "%(amnt)
            if len(move_list) > 1:
                for move in move_list:
                    print u"Numero de movimiento %s"%(num)
                    if self.isclose(move['debit'], amnt, 0.0001, 0.0001):
                        res.append(num)
                        return res
                    if self.isclose(move['credit'], -amnt, 0.0001, 0.0001):
                        res.append(num)
                        return res
                        # HAsta aqui si un movimiento coincide al 100% con la
                        # diferencia, se dejaría fuera de la conciliación
                        # si no, intentamos buscar más de uno

                    suma += move['debit']
                    suma -= move['credit']
                    #Acumula debe y haber
                    testing.append(num)
                    diff = suma - amnt
                    if self.isclose(diff, 0, 0.0001, 0.0001):
                        print "Cuadrado"
                        print testing
                        res = testing
                        return testing
                    num += 1
                    print u"Buscando diferencia %s "%(diff)
            return False

        print u"Conciliar una lista de %s"%(len(move_list))
        res =sum_list(move_list)

        while not self.isclose(res[0], res[1]) and len(move_list):
            print "Comienza pruebas"
            diff = res[0] - res[1]
            moves = busca_move(move_list, diff)
            if moves:
                for move in moves.reverse():
                    move_list.pop(move)
                res = sum_list(move_list)
                break

        if self.isclose(res[0],res[1]) and not self.isclose(res[0], 0) and len(move_list):
            move_ids = [move['id'] for move in move_list]
            print u"Ejecuta conciliacción %s movimientos"%(len(move_ids))
            self.execute('account.move.line', 'reconcile', move_ids, 'manual', False,
                                    False, False)
            print u"Conciliación realizada para : %s con  %s movimientos"%(customer['name'], len(move_ids))
        else:
            self.no_conciliados.append(customer['name'])
            print u"ATENCIÓN!!!! No se pudo conciliar : %s !!!!!!"%(customer['name'])

    def run_concilie(self):
        try:
            customer_ids = self.search('res.partner', [('is_company', '=', True),('customer', '=', True)], order = 'id ASC')
            total = len(customer_ids)
            print u"Iniciando conciliación para : %s clientes"%(total)
            customers = self.read('res.partner', customer_ids, ['id', 'name', 'property_account_receivable'])
            num = 1
            for customer in customers:
                print u"Buscando conciliación para : %s , (%s/%s) "%(customer['name'], num, total)
                move_ids = self.search('account.move.line', [('account_id', '=', customer['property_account_receivable'][0]),
                                                             ('partner_id', '=', customer['id']),
                                                              ('reconcile_ref', '=', False)], order = 'date DESC, id DESC')
                if len(move_ids) > 1:
                    move_fields = self.read('account.move.line', move_ids, ['id', 'credit', 'debit'])
                    self.try_concilie(customer, move_fields)
                else:
                    print "Nada que realizar. Siguiente...."
                num +=1
            print "FINALIZado!!. No conciliados procesados TOTAL:"
            for n in self.no_conciliados:
                print n
        except Exception, e:
            print u"EXCEPTION: REC %s"%(e)
            print "No conciliados procesados hasta el momento:"
            for n in self.no_conciliados:
                print n

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password>" % sys.argv[0]
    else:
        conciliation(sys.argv[1], sys.argv[2], sys.argv[3])
