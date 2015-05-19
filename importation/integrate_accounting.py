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
            self.port = 8069
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
        row_count = sum(1 for row in csv.reader(open(self.import_file))) - 2
        cont = 0
        with open(self.import_file) as csvfile:
            reader = unicsv.UnicodeCSVDictReader(csvfile, delimiter=';', encoding="iso-8859-1")
            last_move = False
            last_date = False
            last_period_id = False
            last_move_id = False
            posted = False
            journal_id = self.search("account.journal", [('name', '=', u"Diario Importación")])
            if not journal_id:
                print "EXCEPTION: Por favor, cree un diario con el nombre 'Diario Importacion'"
                sys.exit(1)
            for row in reader:
                try:
                    if not row.get('Referencia', False) or not row.get('Cuenta', False):
                        continue
                    cont += 1
                    print "%s de %s" % (cont, row_count)
                    if row['Fecha'] != last_date:
                        last_date = datetime.strftime(datetime.strptime(row['Fecha'], "%d-%m-%Y"),"%Y-%m-%d")
                        if row['Concepto'] in ('APERTURA', 'CIERRE', 'PYG', 'EXPLOTACIO'):
                            context = {'account_period_prefer_normal': False}
                        else:
                            context = {}
                        last_period_id = self.execute('account.period', 'find', last_date, context)[0]

                    if int(row['Referencia']) != last_move:
                        if last_move_id and not posted:
                            self.execute('account.move', 'post' ,[last_move_id])
                        last_move = int(row['Referencia'])
                        move_ids = self.search("account.move", [('name', '=', str(last_move)),('date', '=', last_date),('journal_id', '=', journal_id[0])])
                        if move_ids:
                            move_state = self.read("account.move", move_ids[0], ["state"])["state"]
                            if move_state == "posted":
                                last_move_id = move_ids[0]
                                posted = True
                                continue
                            else:
                                posted = False
                                self.unlink("account.move", move_ids[0])
                        move_vals = {
                            'ref': row['Concepto'],
                            'journal_id': journal_id[0],
                            'period_id': last_period_id,
                            'date': last_date,
                            'name': str(last_move)
                        }
                        last_move_id = self.create('account.move', move_vals)
                    elif posted:
                        continue

                    ref = row.get('Documento', "")
                    if not ref:
                        ref = row.get('Ampliacion', "")
                    elif row.get('Ampliacion'):
                        ref += u" // " + row['Ampliacion']
                    account_ids = self.search('account.account', [('code', '=', row['Cuenta'])])
                    if (row['Cuenta'].startswith('430') or row['Cuenta'].startswith('410') or row['Cuenta'].startswith('400') or row['Cuenta'].startswith('440')) and not account_ids:
                        partner_ref = row['Cuenta'][3:]
                        partner_ref = int(partner_ref) and str(int(partner_ref)) or False
                    else:
                        partner_ref = False

                    if partner_ref:
                        partner_ids = self.search("res.partner", [("ref", '=', partner_ref),'|',('active','=',True),('active','=',False)])
                        if not partner_ids:
                            partner_vals = {
                                "customer": row['Cuenta'].startswith('43') and True or False,
                                "ref": partner_ref,
                                "name": row['Titulo'] + u" (IMPORTADO)",
                                "supplier": row['Cuenta'].startswith('43') and False or True,
                                "is_company": True
                            }
                            partner = self.create('res.partner', partner_vals)
                            partner_ids = [partner]
                    else:
                        partner_ids = []
                    if partner_ids:
                        account_code = row['Cuenta'][:3].ljust(9, '0')
                    else:
                        account_code = row['Cuenta']
                    account_ids = self.search('account.account', [('code', '=', account_code)])
                    if not account_ids:
                        print "EXCEPTION: No hay ninguna cuenta contable creada con el codigo %s" % account_code
                        parent_ids = False
                        parent_account_code = account_code[:-1]
                        while len(parent_account_code) > 0:
                            parent_ids = self.search('account.account', [('code', '=', parent_account_code)])
                            if parent_ids:
                                parent_account_code = ""
                            parent_account_code = parent_account_code[:-1]
                        if parent_ids:
                            parent_data = self.read('account.account', parent_ids[0], ["user_type"])
                            account_id = self.create('account.account', {'code': account_code,
                                                                         'name': row['Titulo'],
                                                                         'type': "other",
                                                                         'user_type': parent_data["user_type"][0],
                                                                         'parent_id': parent_ids[0]})
                            account_ids = [account_id]
                        else:
                            print "EXCEPTION: No se pudo crear la cuenta %s" % account_code
                            sys.exit(1)

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

                    move_line_vals = {
                        'journal_id': journal_id[0],
                        'period_id': last_period_id,
                        'date': row['Fecha'],
                        'name': row['Concepto'],
                        'ref': ref,
                        'date': last_date,
                        'debit': debit,
                        'credit': credit,
                        'partner_id': partner_ids and partner_ids[0] or False,
                        'account_id': account_ids[0],
                        'move_id': last_move_id
                    }
                    if row.get('Notas'):
                        analytic_code = row['Notas'].replace("-", "")
                        analytic_acc_id = self.search("account.analytic.account", [('code', '=', analytic_code)])
                        if analytic_acc_id:
                           move_line_vals['analytic_account_id'] =  analytic_acc_id[0]
                        else:
                            print "EXCEPTION: No hay ninguna cuenta analítica creada con el codigo %s" % analytic_code

                    self.create('account.move.line', move_line_vals)

                except Exception, e:
                    print "EXCEPTION: REC: ", row, e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <file_to_import.xls>" % sys.argv[0]
    else:
        integrate_accounting(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
