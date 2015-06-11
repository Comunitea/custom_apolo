#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import xmlrpclib
import socket
import traceback
import re
import base64
import time
import csv


class OdooConnector:

    def __init__(self, server, port, dbname, user, passwd):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = server
        self.port = port
        self.dbname = dbname
        self.user_name = user
        self.user_passwd = passwd
        self.user_id = 0

        #
        # Conectamos con OpenERP
        #
        login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
        self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
        self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
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

    def execute(self, model, method, ids, arguments, context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                             model, method, ids, arguments, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))


class OdooDao:

    def __init__(self, server, port, db, user, password):
        self.connection = OdooConnector(server, port, db, user, password)

    def get_user_by_code(self, telnet_code):
        user_id = self.connection.search('res.users',
                                         [('x_telnet_code', '=', telnet_code)])
        print "USEWRE id    ---   > ", user_id

        if len(user_id) != 1:
            raise ValueError('Code error')
        return user_id[0]

    def get_cameras_menu(self):
        res = {}
        domain = [('camera', '=', True)]
        camera_ids = self.connection.search('stock.location', domain)
        if not camera_ids:
            raise Exception("No hay ubicaciones marcadas como cámaras")
        res_read = self.connection.read('stock.location', camera_ids, ['name'])
        indx = 1
        for x in res_read:
            res[indx] = (x['id'], x['name'])
            indx += 1
        return res

    def get_task_of_type(self, user_id, camera_id, task_type):
        my_args = {'user_id': user_id, 'camera_id': camera_id, 'task_type': task_type}
        task_id = self.connection.execute('stock.task', 'get_task_of_type', [], my_args)
        return task_id

    def get_reposition_task(self, user_id, camera_id):
        my_args = {'user_id': user_id, 'camera_id': camera_id}
        task_id = self.connection.execute('stock.task', 'get_reposition_gun_operations', [], my_args)
        return task_id

    def get_op_data(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        op_data = self.connection.execute('stock.task', 'get_op_data', [], my_args)
        return op_data

    def check_scan(self, user_id, task_id, op_id, line, mode):
        my_args = {'user_id': user_id, 'task_id': task_id, 'scan': line, 'op_id': op_id, 'mode': mode}
        done = self.connection.execute('stock.task', 'check_scan', [], my_args)
        return done

    def set_op_visited(self, user_id, task_id, op_id, to_process):
        my_args = {'user_id': user_id, 'task_id': task_id, 'op_id': op_id, 'to_process': to_process}
        done = self.connection.execute('stock.pack.operation', 'set_op_visited', [], my_args)
        return done

    def finish_task(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        op_data = self.connection.execute('stock.task', 'gun_finish_task', [], my_args)
        return op_data
