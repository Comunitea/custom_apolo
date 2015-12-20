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
import psycopg2

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
        print u"HANDLER: ", (exception)
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

    def get_locations_ids(self, user_id=1):
        loc_ids = []
        domain = []
        loc_ids = self.connection.search('stock.location', domain, order ='id desc')
        return loc_ids

    def sql_execute(self, model, where, values, sql = False):
        try:
            if not sql:
                coma = ''
                str_vals = ''
                for key in values.keys():
                    str_vals += u', %s = %s'%(key, values[key])
                sql = "update %s set %s where %s"%(model, str_vals[1:], where)
            connection=psycopg2.connect("dbname=%s user=%s password=%s"%(self.connection.dbname, 'odoo', 'odoo'))
            cursor=connection.cursor()
            cursor.execute(sql)
            connection.commit()
            return True
        except:
            return False


    def get_cameras_menu(self, user_id=1):
        res = {}
        domain = [('camera', '=', True)]
        camera_ids = self.connection.search('stock.location', domain, order ='name asc')
        if not camera_ids:
            raise Exception("No hay ubicaciones marcadas como cámaras")
        res_read = self.connection.read('stock.location', camera_ids, ['bcd_name', 'temp_type_id'] )
        indx = 1
        for x in res_read:
            res[indx] = (x['id'], x['bcd_name'], x['temp_type_id'][0])
            indx += 1
        return res

    def get_routes_menu2(self, type = False):
        res = {}
        domain =[]
        domain = [('picking_type_id', '=',5), ('validated_state', '=', 'loaded'), ('state', 'not in', ('draft','done','cancel'))]
        route_ids = self.connection.search('stock.picking', domain, order ='min_date, name asc')
        if not route_ids:
            res = False
        res_read = self.connection.read('stock.picking', route_ids, ['route_detail_id'])
        res_read = list(set(res_read))
        indx = 1
        for x in res_read:
            domain = [('id', '=', x['route_detail_id'])]
            route = self.connection.search('route.detail', domain)
            if not route:
                res[indx] = (x['id'], x['detail_name_str'], x['date'])
                indx += 1
        return res

    def get_routes_menu(self, user_id, type=False):
        my_args = {'user_id': user_id}
        ops_data = self.connection.execute('stock.picking', 'get_routes_menu', [], my_args)
        return ops_data

    def get_packs_in_same_picking(self, user_id = 1, package_id = False):
        my_args = {'user_id': user_id, 'package_id': package_id}
        ops_data = self.connection.execute('stock.picking', 'get_packs_in_same_picking', [], my_args)
        return ops_data

    def create_multipack_from_pick(self, user_id = 1, pick_id = False, ops = []):
        my_args = {'user_id': user_id, 'pick' : pick_id, 'ops': ops}
        ops_data = self.connection.execute('stock.picking', 'create_multipack_from_pick', [], my_args)
        return ops_data

    def get_stock_from_output_stock(self, package_id, write = False, quant_id = False):
        my_args = {'package_id': package_id, 'write': write, 'quant_id': quant_id}
        res = self.connection.execute('stock.quant', 'get_stock_from_output_stock', [], my_args)
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

    def get_ops (self, user_id, id, type='ubication'):
        if type == 'ubication':
            return self.get_ops_from_task(user_id, id)
        if type == 'picking':
            return self.get_ops_from_wave(user_id, id)
        if type == 'reposition':
            return self.get_ops_from_task(user_id, id)

    def get_ops_from_task(self, user_id, task_id = False, op_id = False):
        my_args = {'user_id': user_id, 'task_id': task_id, 'op_id' : op_id}
        ops_data = self.connection.execute('stock.pack.operation', 'get_ops_from_task', [], my_args)
        return ops_data

    def get_wave_reports_from_task (self, user_id, task_id, type):
        my_args = {'user_id': user_id, 'task_id': task_id, 'type' : type}
        ops_data = self.connection.execute('stock.picking.wave', 'get_wave_reports_from_task', [], my_args)
        return ops_data

    def get_ops_from_wave (self, user_id, wave_id):
        my_args = {'user_id': user_id, 'wave_id': wave_id}
        ops_data = self.connection.execute('stock.pack.operation', 'get_ops_from_wave', [], my_args)
        return ops_data

    def create_task_from_gun(self, user_id):
        my_args = {'user_id': user_id}
        res = self.connection.execute('stock.task', 'create_task_from_gun', [], my_args)
        return res

    def set_task_pause_state(self, user_id, task_id, pause_state):
        my_args = {'user_id': user_id, 'task_id': task_id, 'pause_state': pause_state}
        res = self.connection.execute('stock.task', 'set_task_pause_state', [], my_args)
        return res

    def get_task_of_type(self, user_id, camera_id, task_type, machine_id, route_id, date_planned):
        my_args = {'user_id': user_id, 'camera_id': camera_id,
                   'task_type': task_type, 'machine_id': machine_id,'date_planned': date_planned, 'route_id': route_id}
        task_id = self.connection.execute('stock.task', 'get_task_of_type', [], my_args)
        return task_id

    def get_reposition_task(self, user_id, camera_id):
        my_args = {'user_id': user_id, 'camera_id': camera_id}
        task_id = self.connection.execute('stock.task', 'get_reposition_gun_operations', [], my_args)
        return task_id

    def set_processed_val(self, user_id, op_id, new_state):
        my_args = {'user_id': user_id, 'op_id' : op_id, 'state' : new_state}
        done = self.connection.execute('stock.pack.operation', 'set_processed_val', [], my_args)
        return done

    def set_wave_ops_values(self, user_id, wave_id, op_id, fields):
        my_args= {'user_id' :user_id, 'wave_id' : wave_id, 'op_id' : op_id, 'fields': fields}
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

    def check_op_to_proccess(self, user_id, op_id):
        my_args = {'user_id': user_id, 'op_id': op_id}
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

    def finish_task(self, user_id, task_id, picking_task = False):
        my_args = {'user_id': user_id, 'task_id': task_id, 'picking_task': picking_task}
        op_data = self.connection.execute('stock.task', 'gun_finish_task', [], my_args)
        return op_data

    def gun_cancel_task(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        op_data = self.connection.execute('stock.task', 'gun_cancel_task', [], my_args)
        return op_data

    def add_loc_operation_from_gun(self, user_id, task_id, pack_id):
        my_args = {'user_id': user_id, 'task_id': task_id, 'pack_id':pack_id}
        op_data = self.connection.execute('stock.task', 'add_loc_operation_from_gun', [], my_args)
        return op_data

    def check_packet_op(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        res = self.connection.execute('stock.pack.operation', 'check_packet_op', [], my_args)
        return res

    def set_wave_op_values(self, user_id, wave_id, field, value):
        my_args = {'user_id': user_id, 'wave_id': wave_id, 'field': field, 'value': value}
        res = self.connection.execute('wave.report', 'set_wave_op_values', [], my_args)
        return res

    def create_operations_on_the_fly(self, user_id, wave_report_id, needed_qty, pack_id):
        my_args = {'user_id': user_id, 'wave_report_id': wave_report_id, 'needed_qty': needed_qty, 'pack_id': pack_id}

        res = self.connection.execute('wave.report', 'create_operations_on_the_fly_from_gun', [], my_args)
        return res

    def set_wave_reports_values(self, user_id, wave_id, field, value):
        my_args = {'user_id': user_id, 'wave_id': wave_id, 'field': field, 'value': value}
        res = self.connection.execute('wave.reports', 'set_wave_reports_values', [], my_args)
        return res

    def change_op_value(self, user_id, op_id, field, value):
        my_args = {'user_id': user_id, 'op_id': op_id, 'field': field, 'value': value}
        res = self.connection.execute('stock.pack.operation', 'change_op_value', [], my_args)
        return res
    def change_op_values(self, user_id, op_id, field_values):
        my_args = {'user_id': user_id, 'op_id': op_id, 'field_values': field_values}
        res = self.connection.execute('stock.pack.operation', 'change_op_values', [], my_args)
        return res

    def check_package_for_picking_change(self, user_id, product_id, package_id, qty_to_move):
        my_args = {'user_id': user_id, 'package_id': package_id, 'product_id': product_id, 'qty_to_move': qty_to_move}
        op_data = self.connection.execute('stock.quant.package', 'check_package_for_picking_change', [], my_args)
        return op_data

    def get_pack_gun_info(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant.package', 'get_pack_gun_info', [], my_args)
        return op_data

    def get_package_gun_info(self, user_id, name):
        my_args = {'user_id': user_id, 'name': name}
        op_data = self.connection.execute('stock.quant.package', 'get_package_gun_info', [], my_args)
        return op_data

    def get_parent_package(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant.package', 'get_parent_package', [], my_args)
        return op_data

    def create_package_from_gun(self, user_id, values = {}):
        my_args = {'user_id': user_id, 'values': values}
        package_data = self.connection.execute('stock.quant.package', 'create_package_from_gun', [], my_args)
        return package_data

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

    def get_uom_from_conversions_from_gun(self, units, product_id, uos_id = False):
        my_args = {'units': units, 'product_id': product_id, 'uos_id': uos_id}
        op_data = self.connection.execute('product.product', 'get_uom_from_conversions_from_gun', [], my_args)
        return op_data

    def get_pack_candidates(self, product_id, min_qty = False):
        my_args = {'min_qty': min_qty, 'product_id': product_id}
        op_data = self.connection.execute('product.product', 'get_pack_candidates_from_gun', [], my_args)
        return op_data

    def get_parent_location_id(self, user_id, location_id):
        my_args = {'user_id': user_id, 'location_id': location_id}
        op_data = self.connection.execute('stock.location', 'get_parent_location_id', [], my_args)
        return op_data

    def get_location_id_childs(self, user_id, location_id):
        my_args = {'user_id': user_id, 'location_id': location_id}
        op_data = self.connection.execute('stock.location', 'get_location_id_childs', [], my_args)
        return op_data

    def get_list_location(self, user_id, location_id):
        my_args = {'user_id': user_id, 'location_id': location_id}
        op_data = self.connection.execute('stock.location', 'get_list_location', [], my_args)
        return op_data

    def is_location_free(self, user_id, location_id):
        my_args = {'user_id': user_id, 'location_id': location_id}
        op_data = self.connection.execute('stock.location', 'is_location_free', [], my_args)
        return op_data

    def get_subpicking_zones(self, user_id, location_id= False, bcd_code = False):
        my_args = {'user_id': user_id, 'location_id': location_id, 'bcd_code' : bcd_code}
        op_data = self.connection.execute('stock.location', 'get_subpicking_zones', [], my_args)
        return op_data

    def get_location_gun_info(self, user_id, location_id=False, lot_id = False, bcd_code=False, type=False):
        my_args = {'user_id': user_id, 'location_id': location_id, 'lot_id': lot_id, 'bcd_code' : bcd_code, 'type' : type}
        op_data = self.connection.execute('stock.location', 'get_location_gun_info', [], my_args)
        return op_data

    def get_product_by_picking_location(self, user_id, location_id=False):
        my_args = {'user_id': user_id, 'location_id': location_id}
        op_data = self.connection.execute('stock.location', 'get_product_by_picking_location', [], my_args)
        return op_data


    def get_package_of_lot_from_gun(self, user_id, location_id=False, lot_id = False):
        my_args = {'user_id': user_id, 'location_id': location_id, 'lot_id':lot_id}
        op_data = self.connection.execute('stock.location', 'get_package_of_lot_from_gun', [], my_args)
        return op_data

    def get_lot_gun_info(self, user_id, lot_id):
        my_args = {'user_id': user_id, 'lot_id': lot_id}
        op_data = self.connection.execute('stock.production.lot', 'get_lot_gun_info', [], my_args)
        return op_data

    def do_manual_transfer_from_gun(self, user_id, vals):
        my_args= {'user_id': user_id, 'vals': vals}
        res = self.connection.execute('manual.transfer.wzd', 'do_manual_transfer_from_gun', [], my_args)
        return res

    def conv_units_from_gun(self, user_id,  product_id, uom_origen, uom_destino, supplier_id =0):
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

    def new_wave_to_revised(self, user_id, task_id, wave_id, new_uom_qty = 0, new_uos_qty = 0, uom_qty = 0, uos_qty = 0):
        my_args = {'user_id': user_id, 'new_uom_qty' : new_uom_qty, 'wave_id': wave_id,
                   'new_uos_qty' : new_uos_qty, 'task_id': task_id,
                   'uom_qty': uom_qty, 'uos_qty': uos_qty }
        res = self.connection.execute('wave.report.revised', 'new_wave_to_revised', [], my_args)
        return res

    def set_waves_op_processed(self, user_id, id):
        my_args = {'user_id': user_id, 'id' : id}
        res = self.connection.execute('wave.report', 'set_waves_op_processed', [], my_args)
        return res

    def change_wave_op_values_packed_change(self, user_id, id, values):
        my_args = {'user_id': user_id, 'id' : id, 'values' : values }
        res = self.connection.execute('wave.report', 'change_wave_op_values_packed_change', [], my_args)
        return res

    def change_wave_op_values(self, user_id, id, values):
        my_args = {'user_id': user_id, 'id' : id, 'values' : values }
        res = self.connection.execute('wave.report', 'change_wave_op_values', [], my_args)
        return res

    def create_reposition_from_gun(self, user_id, selected_loc_ids, limit, capacity):
        my_args = {'user_id': user_id, 'selected_loc_ids' : selected_loc_ids, 'limit' : limit, 'capacity':capacity}
        res, error = self.connection.execute('reposition.wizard', 'create_reposition_from_gun', [], my_args)
        # my_args = {'user_id': user_id, 'picks': res}
        # res = self.connection.execute('stock.pack.operation', 'add_task_to_created_rep', [], my_args)
        return res, error

    def check_picking_zone(self, user_id, product_id, picking_location_id, write = True):
        my_args = {'user_id': user_id, 'picking_location_id' : picking_location_id, 'product_id' : product_id, 'write': write}
        res = self.connection.execute('product.product', 'check_picking_zone', [], my_args)
        return res

    def create_picking_sublocation_from_gun(self, user_id, pick_zone_id, sub_cols):
        my_args = {'user_id': user_id, 'pick_zone_id' : pick_zone_id, 'sub_cols' : sub_cols}
        res = self.connection.execute('stock.location', 'create_picking_sublocation_from_gun', [], my_args)
        return res

    def create_multipack_from_gun(self, user_id, package_id):
        my_args = {'user_id': user_id, 'package_id': package_id}
        op_data = self.connection.execute('stock.quant.package', 'create_multipack_from_gun', [], my_args)
        return op_data

    def print_from_gun(self, user_id, package_ids):
        my_args = {'user_id': user_id, 'package_ids': package_ids}
        op_data = self.connection.execute('create.tag.wizard', 'print_from_gun', [], my_args)
        return op_data

    def print_task(self, user_id, task_id):
        my_args = {'user_id': user_id, 'task_id': task_id}
        op_data = self.connection.execute('create.tag.wizard', 'print_task_from_gun', [], my_args)
        return op_data