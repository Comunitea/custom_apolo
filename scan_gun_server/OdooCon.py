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

    def search(self, model, query, order = 'id desc', context={}):
        """
        Wrapper del método search.
        """
        try:
            #context = { 'order' :  'name asc'}
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, 0, False, order, context)#, order = "name asc")
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

        name = self.connection.read('res.users', user_id, ['name'])[0]['name']

        return user_id[0], name

    def set_to_process(self, user_id, task_id):
        domain = [('task_id', '=', task_id)]
        pool = self.connection.search('stock.pack.operation', domain)
        vals = {'to_process' : False}
        _write = self.connection.write('stock.pack.operation', pool, vals )
        return _write

    def get_locations_ids(self):
        loc_ids = []
        domain = []
        loc_ids = self.connection.search('stock.location', domain, order ='id desc')
        return loc_ids


    def get_cameras_menu(self):
        res = {}
        domain = [('camera', '=', True)]
        camera_ids = self.connection.search('stock.location', domain, order ='name asc')
        if not camera_ids:
            raise Exception("No hay ubicaciones marcadas como cámaras")
        res_read = self.connection.read('stock.location', camera_ids, ['name'])
        indx = 1
        for x in res_read:
            res[indx] = (x['id'], x['name'])
            indx += 1
        return res

    def get_machines_menu(self, type):

        res = {}
        domain =[]
        if type =="ubication":
            domain = [('type', 'not in', ['prep_order', 'transpalet'])]
        if type =="reposition":
            domain = [('type', 'not in', ['prep_order', 'transpalet'])]
        if type =="picking":
            domain = [('type', 'not in', ['retractil'])]

        machine_ids = self.connection.search('stock.machine', domain, order ='code asc')
        if not machine_ids:
            raise Exception("No hay maquinas")
        res_read = self.connection.read('stock.machine', machine_ids, ['code'])
        indx = 1
        for x in res_read:
            domain_free = [('state', '=', 'assigned'), ('machine_id', '=', x['id'])]
            machine_free = self.connection.search('stock.task', domain_free)
            if not machine_free:
                res[indx] = (x['id'], x['code'])
                indx += 1
        return res

    def get_task_assigned(self, user_id):
        my_args = {'user_id': user_id}
        task_id, tasks = self.connection.execute('stock.task', 'get_task_assigned', [], my_args)
        return task_id, tasks

    def get_ops (self, id, type='ubication'):
        if type == 'ubication':
            return self.get_ops_from_tasks(id)
        if type == 'picking':
            return self.get_ops_from_wave(id)
        if type == 'reposition':
            return self.get_ops_from_tasks(id)

    def get_ops_from_tasks(self, task_id):
        my_args = {'task_id': task_id}
        ops_data = self.connection.execute('stock.pack.operation', 'get_ops_from_task', [], my_args)
        return ops_data

    def get_wave_reports_from_task (self, task_id, type):
        my_args = {'task_id': task_id, 'type' : type}
        ops_data = self.connection.execute('stock.picking.wave', 'get_wave_reports_from_task', [], my_args)
        return ops_data

    def get_ops_from_wave (self, wave_id):
        my_args = {'wave_id': wave_id}
        ops_data = self.connection.execute('stock.pack.operation', 'get_ops_from_wave', [], my_args)
        return ops_data

    def set_task_pause_state(self, user_id, task_id, pause_state):
        my_args = {'user_id': user_id, 'task_id': task_id, 'pause_state': pause_state}
        res = self.connection.execute('stock.task', 'set_task_pause_state', [], my_args)
        return res

    def get_task_of_type(self, user_id, camera_id, task_type, machine_id, date_planned):
        my_args = {'user_id': user_id, 'camera_id': camera_id,
                   'task_type': task_type, 'machine_id': machine_id,'date_planned': date_planned}
        task_id = self.connection.execute('stock.task', 'get_task_of_type', [], my_args)
        return task_id

    def get_reposition_task(self, user_id, camera_id):
        my_args = {'user_id': user_id, 'camera_id': camera_id}
        task_id = self.connection.execute('stock.task', 'get_reposition_gun_operations', [], my_args)
        return task_id

    def set_processed_val(self, op_id, new_state):
        my_args = {'op_id' : op_id, 'state' : new_state}
        done = self.connection.execute('stock.pack.operation', 'set_processed_val', [], my_args)
        return done

    def set_wave_ops_values(self, wave_id, user_id, field, value):
        my_args= {'wave_id' : wave_id, 'user_id' :user_id, 'field': field, 'value' :value}
        done = self.connection.execute('stock.pack.operation', 'set_wave_ops_values', [], my_args)
        return done

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

    def check_op_visited(self, user_id, op_id, forzar = False):
        my_args = {'user_id': user_id, 'forzar': forzar, 'op_id': op_id}
        done = self.connection.execute('stock.pack.operation', 'check_op_visited', [], my_args)
        return done

    def check_op_to_proccess(self, op_id):
        my_args = {'op_id': op_id}
        done = self.connection.execute('stock.pack.operation', 'check_op_to_process', [], my_args)
        return done

    def set_op_to_process(self, user_id, task_id, op_id, to_process):
        my_args = {'user_id': user_id, 'task_id': task_id, 'op_id': op_id, 'to_process': to_process}
        done = self.connection.execute('stock.pack.operation', 'set_op_to_process', [], my_args)
        return done

    def check_task_ops_finished(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        ops_finish = self.connection.execute('stock.task', 'check_task_ops_finished', [], my_args)
        return ops_finish

    def gun_begin_task(self, user_id, task_id, run = False):
        my_args = {'user_id': user_id, 'task_id': task_id, 'run': run}
        res = self.connection.execute('stock.task', 'gun_begin_task', [], my_args)
        return res

    def finish_task(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        op_data = self.connection.execute('stock.task', 'gun_finish_task', [], my_args)
        return op_data

    def check_packet_op(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        res = self.connection.execute('stock.pack.operation', 'check_packet_op', [], my_args)
        return res

    def set_wave_op_values(self, user_id, wave_id, field, value):
        my_args = {'user_id': user_id, 'wave_id': wave_id, 'field': field, 'value': value}
        res = self.connection.execute('wave.report', 'set_wave_op_values', [], my_args)
        return res

    def set_wave_reports_values(self, user_id, wave_id, field, value):
        my_args = {'user_id': user_id, 'wave_id': wave_id, 'field': field, 'value': value}
        res = self.connection.execute('wave.reports', 'set_wave_reports_values', [], my_args)
        return res



    def change_op_value(self, user_id, op_id, field, value):
        my_args = {'user_id': user_id, 'op_id': op_id, 'field': field, 'value': value}
        res = self.connection.execute('stock.pack.operation', 'change_op_value', [], my_args)
        return res

    def get_pack_gun_info(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant.package', 'get_pack_gun_info', [], my_args)
        return op_data

    def get_quant_pack_gun_info(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant', 'get_quant_pack_gun_info', [], my_args)
        return op_data

    def get_quant_pack_gun_info_resumen(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant', 'get_quant_pack_gun_info_resumen', [], my_args)
        return op_data

    def get_product_gun_info(self, user_id, product_ean):
        my_args = {'user_id': user_id, 'product_ean': product_ean}
        op_data = self.connection.execute('product.product', 'get_product_gun_info', [], my_args)
        return op_data

    def get_location_gun_info(self, user_id, location_id, type =''):
        my_args = {'user_id': user_id, 'location_id': location_id, 'type': type}
        op_data = self.connection.execute('stock.location', 'get_location_gun_info', [], my_args)
        return op_data

    def get_lot_gun_info(self, user_id, lot_id):
        my_args = {'user_id': user_id, 'lot_id': lot_id}
        op_data = self.connection.execute('stock.production.lot', 'get_lot_gun_info', [], my_args)
        return op_data

    def do_manual_trasfer_from_gun(self, vals):
        self.connection.execute('manual.transfer.wzd', 'do_manual_trasfer_from_gun', [], vals)
        return True

    def conv_units_from_gun(self, product_id, uom_origen, uom_destino, supplier_id =0):
        my_args = {'product_id': product_id, 'uom_origen': uom_origen, 'uom_destino': uom_destino,'supplier_id': 0}
        op_data = self.connection.execute('product.product', 'conv_units_from_gun', [], my_args)
        return op_data

    def get_product_gun_complete_info(self, user_id, product_id = False, ean = False):
        my_args = {'user_id': user_id, 'ean': ean, 'product_id': product_id}
        product_data = self.connection.execute('product.product', 'get_product_gun_complete_info',[], my_args)
        return product_data

    def get_packets_for_ean(self, user_id, product_id = False, ean = False):
        my_args = {'user_id': user_id, 'ean' : ean, 'product_id':product_id}
        packets = self.connection.execute('product.product', 'get_packets_for_ean',[], my_args)
        return packets

    def get_user_packet_busy(self, user_id, packet_id):
        my_args = {'user_id': user_id, 'packet_id': packet_id}
        res = self.connection.execute('stock.pack.operation', 'get_user_packet_busy', [], my_args)
        return res

    def new_wave_to_revised(self, user_id, new_uom_qty, new_uos_qty, id):
        my_args = {'user_id': user_id, 'new_uom_qty' : new_uom_qty, 'new_uos_qty' : new_uos_qty, 'id' : id}
        res = self.connection.execute('wave.report.revised', 'new_wave_to_revised', [], my_args)
        return res

    def set_waves_op_processed(self, user_id, id):
        my_args = {'user_id': user_id, 'id' : id}
        res = self.connection.execute('wave.report', 'set_waves_op_processed', [], my_args)
        return res