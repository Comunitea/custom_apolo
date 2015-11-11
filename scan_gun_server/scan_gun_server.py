#!/usr/bin/python
# -*- coding: utf-8 -*-
from twisted.internet.protocol import Factory
#from twisted.protocols.basic import LineReceiver
from basic import LineReceiver
from twisted.internet import reactor
from OdooCon import OdooDao
import sys
import datetime
import string

params = {}  # se guardará la configuración del archivo aquí

KEY_F1 = '8f50' #'\x8fP'
KEY_F2 = '8f51' #'\x8fQ'
KEY_F3 = '8f52' #'\x8fR'
KEY_F4 = '8f53' #'\x8fS'
KEY_F5 = '9b31367e' #'\x9bf5~'
KEY_F6 = '9b31377e' #'\x9b17~'
KEY_F7 = '9b31387e' #'\x9b18~'
KEY_F8 = '9b31397e' #'\x9b19~'
KEY_F9 = '9b32307e' #'\x9b20~'
KEY_F10 = '9b32317e' #'\x9b21~'
KEY_F11 = '9b32337e' #'\x9b23~'
KEY_F12 = '9b32347e' #'\x9b24~'
KEY_UP = '9b41' #'\x8bA'
KEY_DOWN = '9b42' #'\x8bB'

KEY_NEXT = "KD"
KEY_PREV = "KU"


KEY_CONFIRM = "F1"
KEY_YES ="F1"

KEY_PAUSE = "F6"
KEY_MANUAL ="F3"

KEY_PRINT = "F7"
KEY_RUN = "F10" #"F5"
KEY_FINISH = "F10" #"F5"

KEY_ORIGEN = "F6"
KEY_WAVE_OPS = "F6"

KEY_PAQUETE = "F7"
KEY_QTY = "F8"##

KEY_DESTINO = "F9"
KEY_CALCULADORA = "F8"
KEY_DO_PACK = "F7"
KEY_DEBUG="F9"
KEY_NO_REALIZADA = "F9"

KEY_NO ="F4" # "F11"
KEY_CANCEL ="F4" # "F11"

KEY_VOLVER = "F2"#"F12"
KEY_SHOW_PROCESSED = "F3"
VALS = {'paquete': False, 'destino' : False, 'origen' : False, 'cantidad' : 0, 'lote' : False, 'packets' : {}}
VALS_MANUAL = {'exist': False, 'package_id': False, 'product_id' : False, 'quantity': 0,
               'lot_id': False, 'src_location_id': False, 'dest_location_id': False, 'do_pack': 'do_pack',
               'package': False, 'product': False, 'lot': False, 'src': False, 'dest': False}
VALS_UBI = {'paquete': False, 'destino' : False}
COLORS_0 = chr(27)+"[0m"
COLORS_INV = chr(27) + "[7m"
COLORS_NECESARIO = chr(27) + "[31m"

OPS_BLOCKED = True
PRE_PACK = 'PK'
PRE_LOC = 'LC'
PRE_PROD = 'PR'
PRE_LOT = 'LT'
MAX_NUM = 4
MAX_NUM_ONE = 6
ERROR_TAREA_EN_PAUSA = u'\n[x] Tarea en pausa'
# Para leer el archivo de configuración y guardarlo en params

def read_file():
    if len(sys.argv)>1:
        telnet_cfg = sys.argv[1]
    else:
        telnet_cfg = 'telnet.cfg'
    with open(telnet_cfg, 'r') as configfile:
        for line in configfile:
            key = line[:line.index('=')]
            value = line[line.index('=') + 1:].replace('\n', '')
            if value.isdigit():
                value = int(value)
            if key == 'allowed_ips':
                value = value.split(',')
            params[key] = value
read_file()


# Devuelve datos de conexión del archivo de configuración guardado en para,s
def get_connection_params(return_params=[]):
    return [params[k] for k in return_params if k in params]


# Protocolo para manejar las conexiones, una instancia por conexión
class ScanGunProtocol(LineReceiver):

    def __init__(self, factory):

        self.factory = factory

        self.user_id = False
        self.user_name = False
        self.code = False
        self.show_id = False
        self.show_keys = True
        self.views = 0 # ver pendientes, 1# ver no vistas, 2 ver todoas
        self.confirm_last_step = False

        self.last = False
        self.reset_self_task()
        self.reset_self_op()
        self.show_op_processed = False
        self.print_tag_option = True
    def reset_self_task(self):

        self.camera_id = [] # Lista de Camaras activa, por la que se busca
        self.camera_ids = [] #lista de camaras activas
        self.machine_id = False
        self.task_id = False # False si no tiene tarea, lista de tareas si tiene varias activas
        self.wave_id = False
        #self.task_data = False #datos de la tarea activa, cuyo numero esta en active_task
        self.active_task = False # numero de la tarea activa, dentro de la matriz de tareas
        self.tasks = False # datos de las tareas
        self.vals = VALS #valores necesarios para finalizar tarea, se reinician al entrar en una tarea
        self.type ='ubication'
        self.state = "register"
        self.last_read={}
        self.loc_id = False  #se usa para confirmar una segunda lectura
        self.step = 0
        self.new_qty =0.00
        self.uom_var = False
        self.uos_var = False
        self.qty_calc = []
        self.last_state = self.state
        self.new_package_id= False
        self.pack_type = 'do_pack'
        self.do_pack = True


    def reset_self_op(self):
        self.op_id = False
        self.op_data = False # datos de la operacion activa, cuyo numero esta en active_pack
        self.active_op = False # numero de la operacion activa, dentro de la matriz de operaciones
        self.ops = False
        self.num_order_list_ops = 1
        #Tengo que crear esto para las operaciones de las waves
        self.wave_op_id = False
        self.wave_op_data = False # datos de la operacion activa, cuyo numero esta en active_pack
        self.wave_active_op = False # numero de la operacion activa, dentro de la matriz de operaciones
        self.wave_ops = False
        self.wave_num_order_list_ops = 1
        self.fc = 1
        self.new_uom_qty =0.00
        self.uom_var = False
        self.uos_var = False
        self.qty_calc = []
        self.new_uos_qty = 0.00
        self.new_qty = 0.00
        self.route=False
        self.route_id = False


    def connectionMade(self):
        """
        Método del framework. Mensaje al establecer la conexión
        """
        self.factory.debug= False
        self._snd(u"Codigo de operador:")

    def connectionLost(self, reason = u"Se perdio la conexión"):
        """
        Método del framework. Mensaje al perder la conexión
        """
        if self.code in self.factory.users_codes:
            self.factory.users_codes.remove(self.code)
        self._snd(reason)

    def get_odoo_connexion(self, code):
        """
        LLamado en estado register, si se establece la conexión, se guarda el
        usuario y el código telnet usado para comprobar si alguíen introdue
        el mismo
        """
        self.reset_self_task()
        self.reset_self_op()
        res = True
        try:
            user_id, user_name = self.factory.odoo_con.get_user_by_code(code)
            self.user_name = user_name
            self.user_id = user_id
            self.code = code
            self.factory.users_codes.append(code)
        except Exception, e:
            res = False
        return res

    def lineReceived(self, line, confirm= False):

        if self.factory.debug:
            self.lineReceived2(line = line, confirm = confirm)
            return
        else:
            try:
                self.lineReceived2(line = line, confirm = confirm)
            except Exception, e:
                print Exception, e.message
                self._snd(self.last_send)
                return

    def lineReceived2(self, line, confirm= False):
        """
        Método del framework. LLamado cada vez que se recibe una linea
        """
        #try:
        line_received = line
        if line == '' or not line:
            return
        key = False
        line = line.upper()
        print u"[%s] Estado: %s Anterior: %s "%(self.step, self.state, self.last_state)
        izq = line.encode('hex')[0:2]

        key = False
        if izq == "8f" or izq == "9b" or izq=="1b":
            #son teclas de fucnion

            line = self.function_keys(line.encode('hex'))
            if line:
                key = True
        print "Codificación Tecla: %s > %s"%(line, line.encode('hex'))
        print u"Entrada: " + str(line)
        line= str(line)
        if not key:
            if len(line)==9:
                line_, child = self.check_ubi(line)
                if line_:
                    line = line_
                    if child:
                        self.last_read = line
                        self.subzones = False
                        self.selected_subzone = False
                        self.last_state = self.state

                        self._snd(self.get_str_select_picking_subzone(line))
                        self.state = 'select_subzone'#self.handle_select_picking_subzone(line)
                        return
                    else:
                        line = PRE_LOC + str(line)
                else:

                    self._snd(u"%s no encontrada\n %s Volver" %(line, KEY_VOLVER))
                    return

            elif len (line) == 6 and line[0:2]!="PK":
                line = self.check_package(line)
                if not line:
                    message = "\nPaquete No Encontrado"
                    self.sendLine(self.last_send + message)
                    return


        # if line == "F3":
        #     self.show_op_processed = not self.show_op_processed
        #     #self.lineReceived(line=KEY_VOLVER)
        #     return


        if line == "quit":
            sys.exit(0)
        elif self.state=="message":
            self.handle_message(line)
        elif self.state=="error":
            self.handle_error(line)
        elif self.state =="yes_no":
            self.handle_yes_no(line)
        elif self.state == "register":
            self.handle_register(line)
        elif self.state == "menu1":
            self.handle_menu1(line)
        elif self.state == "tasks":
            self.handle_tasks(line, confirm = confirm)
        elif self.state =="routes":
            self.handle_route_selected(line)
        elif self.state =="machines":
            self.handle_machine_selected(line)
        elif self.state =="manual_transfer_product":
            self.handle_manual_transfer_product(line)
        elif self.state =="manual_transfer_packet":
            self.handle_manual_transfer_packet(line)

        elif self.state =="products_by_zone":
            self.handle_products_by_zone(line)

        elif self.state =="manual_picking_reposition":
            self.handle_manual_picking_reposition(line)
        elif self.state == "form_repo_ops":
            self.handle_form_repo_ops(line, confirm=confirm)
        elif self.state == "list_ops":
            self.handle_list_ubi_ops(line, confirm=confirm)
        elif self.state == "list_waves":
            self.handle_list_waves(line, confirm=confirm)
        elif self.state == "form_wave":
            self.handle_form_wave(line, confirm=confirm)
        elif self.state == "list_wave_ops":
            self.handle_list_wave_ops(line, confirm=confirm)
        elif self.state == "list_repo_ops":
            self.handle_list_repo_ops(line, confirm=confirm)
        elif self.state == "form_ops":
            self.handle_form_ubi_ops(line, confirm=confirm)
            #self.handle_ops(line, confirm=confirm)
        elif self.state in ["ubication", "reposition", "picking"]:
            self.handle_camera_selected(line)
        elif self.state =="form_product":
            self.handle_form_product(line)
        elif self.state =="list_product":
            self.handle_list_product(line)
        elif self.state == "scan_op":
            self.handle_scan_op(line)
        elif self.state == "scan_location":
            self.handle_scan_location(line)
        elif self.state == 'scan_op_rep':
            self.handle_scan_op_rep(line)
        elif self.state == 'scan_location_rep':
            self.handle_scan_location_rep(line)
        elif self.state == 'scan_quantity':
            self.handle_quantity(line)
        elif self.state == 'tools':
            self.handle_menu_tool(line)
        elif self.state == 'parametros':
            self.handle_menu_parametros(line)
        elif self.state == 'set_picking_zone':
            self.handle_set_picking_zone(line)
        elif self.state == 'create_picking_zone':
            self.handle_create_picking_zone(line)
        elif self.state == 'select_subzone':
            self.handle_select_picking_subzone(line)
        elif self.state == 'create_multipack':
            self.handle_create_multipack(line)
        elif self.state == 'multipack':
            self.handle_create_multipack_from_pick(line)
        elif self.state == 'print_tags':
            self.handle_print_tags(line)


        else:
            message = u"Introduciste %s\n, pero no te entiendo:" %line_received
            self._snd(self.last_send, message)
            return
        # except Exception, e:
        #     print Exception, e.message
        #     self._snd(self.last_send)
        #     return

    def handle_error(self, line):

        if line == KEY_CONFIRM:
            self.state=self.last_state
            self._snd (self.next_str)

    def _snd_error(self, str, message, custom_format=True):
        self.next_str = str
        message = message.encode("UTF-8", 'ignore')
        message += '\n<' + KEY_CONFIRM + '> Continuar'
        self.last_state=self.state
        self.state = "error"
        clean = u'\n' * 25
        clean = clean.encode("UTF-8", "ignore")
        if custom_format:
            cutstr = self.cut_in_lines(message)
            self.sendLine(clean + cutstr)
        else:
            self.sendLine(clean+ message)

    def _snd(self, line='\n', message='', custom_format=True):

        clean = u'Menu:      ' + str(self.last) + \
                u'\nState:   ' + str(self.state) + \
                u'\nStep:    ' + str(self.step) + \
                u'\nTask id: ' + str(self.task_id) + \
                u'\nOp id:   ' + str(self.op_id)+\
                u'\nDeb.(%s): %s'%(KEY_DEBUG, str(self.factory.debug))+\
                u'\nFiltrar : %s'%self.show_op_processed+\
                u'\n' * 25


        self.last = '-'
        if not self.factory.debug:
            clean = u'\n' * 25

        if self.user_id:
            cabecera = self.user_name
        else:
            cabecera=''

        delimiter = u"\n" + u'*'*25 + u'\n'

        if message !='':
            message = '\n' + message
        if not line:
            line = "\n"
        line = line.encode("UTF-8")
        message = message.encode("UTF-8")
        cabecera = cabecera.encode("UTF-8")
        clean = clean.encode("UTF-8")
        delimiter = delimiter.encode("UTF-8")
        snd_str =clean + cabecera + delimiter + line + message
        self.last_send = snd_str
        self.sendLine(snd_str)
        return

    def cut_in_lines(self,line):
        """
        Corta la cadena de caracteres quitándole los símbolos \n, que son los
        que indican el ambio de línea.
        """
        limit_screen = 30 #caracteres que tiene de ancho la pantalla
        length = 0 #para comparar líneas
        res = ''

        for linea in line.split('\n'):
            if length + len(linea) <= limit_screen:
                new_linea = linea
                length += len(new_linea)
            else:
                if len(linea) > limit_screen:
                    linea = self.cut_in_words(linea)
                new_linea = '\n' + linea
                length = len(new_linea) - 2 #-2 para no tener en cuenta el \n
            res += new_linea
        return res

    def cut_in_words(self,linea):
        """
        Corta la línea de caracteres separándola por palabras y, si no cabe hace
        un salto de carro.
        """
        length = 0
        res = ''
        limit_screen = 30
        for word in linea.split(' '):
            if length + len(word) <= limit_screen:
                new_word = word + ' '
                length += len(new_word)
            else:
                new_word = '\n' + word + ' '
                length = len(new_word) - 2 #-2 para no tener en cuenta el \n
            res += new_word
        return res

    def handle_register(self, code):
        """
        Manejador del estado de register. Si hace read del código de usuario
        nos damos por logeados. Solo se usa la conexión central en el factory.
        """

        if code in self.factory.users_codes and not self.factory.debug:
            self._snd(u"Codigo Ya Registrado\nIntroduzca codigo")
            return

        if self.get_odoo_connexion(code):
            self.state = "tasks"
            self.menu1_tasks()
            return
        else:
            self._snd(u"No se pudo establecer\n la conexion.\nIntroduzca codigo")

    def get_str_menu1(self, paused = False):
        """
        Método que devuelve el menú principal
        """
        self.last = "get_str_menu1"
        self.check_task()
        #Siempre que pase por aquí, actualizo tareas
        print "Menu principal"
        delimiter = "\n********************\n"
        user_delimiter = "User: " + self.user_name
        keys =''
        menu_str =''
        if self.tasks:
            if len(self.tasks)>0:
                menu_str += u"0 -> Tareas Asignadas\n"
        if self.tasks_paused():
            menu_str += u"1 -> Tarea de ubicacion\n2 -> Tarea de reposicion\n3 -> Tarea de picking\n"
        menu_str+= u"4 -> Transferencia manual\n"
        menu_str+= u"9 -> Herramientas\n"
        if self.show_keys:
            keys = u"%s Atrás"%KEY_VOLVER
        menu_str += delimiter + keys

        return menu_str

    def check_package(self, line):

        line = str(line)

        res = self.factory.odoo_con.get_package_gun_info(self.user_id, line)
        check=False
        if res:
            check = PRE_PACK + str(res)
        return check

    def check_ubi(self, line):
        res = self.factory.odoo_con.get_location_gun_info(self.user_id, bcd_code = line)
        check = False
        childs = False
        if res['exist']:
            check = res['location_id']
            childs = res['childs']
        return check, childs

    def handle_menu1(self, line):
        """
        Manejador del estado menu1. Para tareas muestra un mení con las
        cámaras a seleccionar, y cambia al siguiente estado si la ubicación es
        correcta.
        """
        self.step = 0
        self.active_op=False
        self.active_task= False
        self.tasks= {}
        self.task_id = False
        self.vals= VALS
        self.num_order_list_ops = 1
        print "handle_menu" + str(line)
        if line not in ["0", "1", "2", "3", "4", "5", "9"] and line != KEY_VOLVER:
            str_error = u"La opcion %s no es valida.\nReintentar:\n"%line
            self.state='menu1'
            self._snd(str_error + self.get_str_menu1(True))
        elif line =="0_":
            self.state = "register"
            self.factory.users_codes.remove(self.code)
            self.user_id = False
            self.code = False
            self.handle_register('0')
        elif line == "1":
            self.state = "ubication"
            self.type = 'ubication'
            self.camera_ids=[]
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        elif line == "2":
            self.state = "reposition"
            self.type = "reposition"
            self.camera_ids=[]
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        elif line == "3":
            self.state = 'routes'
            self.type = 'picking'
            self.camera_ids=[]
            menu_str = self.get_routes_menu(self.type)
            self._snd(menu_str)
        elif line == "4":
            self.state = 'manual_transfer_packet'
            self.vals = VALS_MANUAL
            menu_str = self.get_manual_transfer_packet()
            self._snd(menu_str)

        elif line == "8":
            self.state = 'config'
            self.vals = VALS_MANUAL
            menu_str = self.menu_config()
            self._snd(menu_str)

        elif line == "9":
            self.state = 'tools'
            self.vals = VALS_MANUAL
            menu_str = self.get_menu_tools()
            self._snd(menu_str)
        elif line == "0":
            self.state = 'tasks'
            menu_str = self.get_str_menu_task()
            self._snd(menu_str)
        elif line == KEY_VOLVER:
            self.state = 'register'
            self.user_id = False
            self.user_name =""
            self.connectionLost(u"Sesion Cerrada\nIntroduzca su codigo\n")
            return False
        else:
            self._snd(u"No implementado aún")

    def menu1_tasks(self):

        print "Menu1 tasks"
        res = self.check_task()
        self.last_state = self.state

        if res==1:
            print "Tengo tarea activa: " + str(self.task_id)
            self.state = "tasks"
            str_menu = self.get_str_menu_task()
        elif res ==0:
            print "No tengo tareas"
            self.state = "menu1"
            str_menu = self.get_str_menu1()
        elif res ==-1:
            print "Tengo tareas pausadas"
            self.state = "menu1"
            str_menu = self.get_str_menu1(paused = True)

        self._snd(str_menu)

    def get_active_task(self):
        res ='1'
        for task in self.tasks:
            if self.tasks[task]['id']==self.task_id:
                res = task
        return res
    def check_task(self):
        #buscamos tareas asignadas al self.user_id
        self.task_id, self.tasks = self.factory.odoo_con.get_task_assigned(self.user_id)

        self.step=0
        if self.tasks:
            if self.task_id != False:
                self.type = self.tasks['0']['type']
                if self.vals != True:
                    self.reset_vals()

                return 1
            else:
                if self.vals != True:
                    self.reset_vals()
                return -1

        else:
            return 0

    def get_str_menu_task(self):

        print "get menu tasks:"
        self.last = "get_str_menu_task"
        header = "Tareas Asignadas:"
        strg = header
        self.task_id = False
        self.active_task = False
        self.op_id = False
        self.active_op = False
        if not self.tasks:
            self.check_task()

        strg_data = ''
        for task_ in self.tasks:
            task = self.tasks[task_]
            data =  u"\n%s -> %s (%s op)"%(task_, task['ref'], str(task['ops']))

            if task['paused']:
                strg_data += data
            else:
                strg_data += self.inverse(data)
                self.type = task['type']
                self.task_id = task['id']
                self.active_task = task_

        strg += strg_data

        if not self.tasks:
            strg += U"\nSin Tareas Asignadas"

        keys = u"\n%s Atras"%KEY_VOLVER
        if self.show_keys:
            strg += keys
        return strg

    def handle_new_task(self):
        self.vals = {}
        self.ops = {}
        self.waves = {}
        ok_task = self.check_task()
        self.ops = False
        self.step=0
        if self.task_id:
            self.ops = self.factory.odoo_con.get_ops(self.user_id,self.task_id, self.type)
            self.step=0
            self.state ='tasks'
            self._snd(self.get_str_menu_task())
        else:
            self.state ='menu1'
            self._snd(self.get_str_menu1())
        return

    def handle_tasks(self, line='0', confirm = False):

        print "handle_tasks"

        line_in_keys = False

        if line == "" or not line:
            self.handle_tasks(line='0')
            return

        #Ponemso una tara en pausa, la ponemos en RUN
        # if line == KEY_RUN and False:
        #
        #     if len(self.tasks)==1:
        #         self.ops = False
        #         try:
        #             aux = self.task_id
        #             res = self.factory.odoo_con.set_task_pause_state(self.user_id,
        #                                                              self.tasks['0']['id'], False)
        #             self.check_task()
        #             self.task_id = aux
        #             message = u"Ok"
        #         except Exception, e:
        #             message = u"Error de tarea"
        #     else:
        #         message =u'Tienes más de una. Cual?'
        #     self._snd(self.get_str_menu_task(), message)
        #     return



        #Ponemso una tarea en run , la ponemos en PAUSE. No hace falta preguntar cual
        #es la que tiene self.task_id
        pausar = False
        # if line == KEY_PAUSE  and pausar == True:
        #     self.ops = False
        #     if self.task_id:
        #         try:
        #             res = self.factory.odoo_con.set_task_pause_state(self.user_id,
        #                                                              self.tasks[self.active_task]['id'], True)
        #             self.check_task()
        #             message = "Ok"
        #         except Exception, e:
        #             message = "Error de tarea(%s)"%e
        #             self.state = "tasks"
        #         self._snd(self.get_str_menu_task(), message)
        #         return

        #volvemos a menu principal
        if line == KEY_VOLVER:
            self.ops = False
            self.last_state = self.state
            self.state = "menu1"
            self._snd(self.get_str_menu1())
            return

        # if line == KEY_CANCEL and pausar == True:
        #     res = self.factory.odoo_con.gun_cancel_task(self.user_id, self.task_id)
        #     self.check_task()
        #
        #     if res==True:
        #         message = u'Tarea cancelada\n'
        #     else:
        #         message = u'Error al cancelar (ERP)\n'
        #     self._snd(self.get_str_menu_task(), message)
        #     return
        #     if self.tasks[self.active_task]['ops']==0:
        #         res = self.factory.odoo_con.gun_cancel_task(self.user_id, self.task_id)
        #         self.check_task()
        #         message = u'Tarea cancelada\n'
        #     else:
        #         message = u'No puedes. Tiene Ops\n'
        #     self._snd(self.get_str_menu_task(), message)
        #     return

        if line == KEY_CONFIRM and self.task_id and self.ops and confirm==False:
            task_ops_finish = True
            for op in self.ops:
                if not self.ops[op]['PROCESADO']:
                    task_ops_finish = False

            if task_ops_finish:
                message = u"Todas las operaciones OK\nFinalizar Tarea:\n"\
                          + u"%s"%self.tasks[self.active_task]['ref']\
                          + u"\n%s Si %s No"%(KEY_YES, KEY_NO)
            else :
                message = u"Falta operaciones\nFinalizar Tarea:\n%s Seguro?:\n"\
                          %self.tasks[self.active_task]['ref']\
                         + u"\n%s Si %s No"%(KEY_YES,KEY_NO)

            #llamamos a confirmar tarea
            self.last_state= "tasks" #queremos que vuelva a tareas
            self.state=10
            self.state = "yes_no"
            self._snd(message)
            return

        if line == KEY_CONFIRM and confirm == True:

            res = self.factory.odoo_con.finish_task(self.user_id, self.task_id)

            if not res:
                message = u'\nError:\nRevisa Ubicaciones y/o Cantidades\n%s para volver'%KEY_VOLVER
                self._snd(message)
            else:
                self.print_task(self.task_id)
                self.handle_new_task()
            return

        if line == KEY_YES and self.step==10:
            self.handle_tasks(line=KEY_CONFIRM, confirm= True)
            return
        if line == KEY_NO and self.step==10:
            self.handle_tasks(line=KEY_CANCEL)
            self.step=0
            return

        if line in self.tasks.keys():
            self.last_state = self.state
            self.check_task()
            self.active_op = 1
            self.active_wave = line
            self.active_task = line
            self.task_id = self.tasks[line]['id']
            self.type = self.tasks[self.active_task]['type']
            self.ops = False
            if self.type=='ubication':
                res = self.handle_tasks_ubication(line=line, confirm=confirm)
                return
            if self.type =='picking':
                res = self.handle_tasks_picking(line=line, confirm=confirm)
                return
            if self.type=='reposition':
                res = self.handle_tasks_reposition(line=line, confirm=confirm)
                return
        else:
            message = "Error de tarea(" + line + ')'
            self.state = "tasks"
            self._snd(self.get_str_menu_task(), message)
            return

    def handle_tasks_picking(self, line='0', confirm=False):

        self.active_wave = line
        try:
            self.state = "list_waves"
            self.step=0
            self._snd(self.get_str_list_waves())
            return
        except Exception, e:
            message =e.message+ '\n' + "Error de tarea(Pick:%s)"%self.tasks[self.active_task]['id']
            self.state = "tasks"
            self._snd_error(self.get_str_menu_task(), message)
            return

    def handle_tasks_ubication(self, line='0', confirm = False):

        try:
            self.state = "list_ops"
            self.num_order_list_ops = 1
            self._snd(self.get_str_list_ops())
            return
        except Exception, e:
            message =e.message+ '\n' + "Error de tarea(Ubic:%s)"%self.tasks[self.active_task]['id']
            self.state = "tasks"
            self._snd_error(self.get_str_menu_task(), message)
            return

    def handle_tasks_reposition(self, line='0', confirm = False):

        try:
            self.state = "list_repo_ops"
            self.num_order_list_ops = 1
            self._snd(self.get_str_list_repo_ops())
            return
        except Exception, e:
            message =e.message + '\n' + "Error de tarea(Repo:%s)"%self.tasks[self.active_task]['id']
            self.state = "tasks"
            self._snd_error(self.get_str_menu_task(), message)
            return

    def get_str_list_repo_ops(self):
        self.last = "get_str_list_repo_ops"
        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
        header = "Ops en %s"%str(self.tasks[self.active_task]['ref'])
        res = "x" if self.show_op_processed else " "
        header +=" [%s] Todas\n"%res
        return self.get_str(self.ops, header)

    def handle_list_repo_ops(self, line, confirm=False):
        # Manejador de lista de operaciones de ubicacion
        if line == '0' or line =='':
            self.handle_list_repo_ops(line='1')
            return

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if not order_line:
            if line == KEY_PAUSE:
                aux = self.task_id
                pause = not self.tasks[self.active_task]['paused']
                res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                                self.tasks[self.active_task]['id'],
                                                                pause)
                self.check_task()
                self.task_id = aux
                self.active_task = self.get_active_task()
                self._snd(self.get_str_list_ops())
                return


            if line == KEY_CANCEL:
                #CANCELAR LA TAREA QUE ESTÁ CON Sself.task_id
                # aux = self.task_id
                # res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                #                                                 self.tasks['0']['id'],
                #                                                 not self.tasks['0']['id']['paused'])
                # self.check_task()
                # self.task_id = aux
                # self._snd(self.get_str_list_ops())
                return



            if line == KEY_CONFIRM:
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM, confirm = not self.confirm_last_step)
                return
            if line == KEY_VOLVER:

                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM<=len(self.ops):
                    self.num_order_list_ops += MAX_NUM
                self._snd(self.get_str_list_repo_ops())
                return
            if line == KEY_PREV:
                self.num_order_list_ops -= MAX_NUM
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self._snd(self.get_str_list_repo_ops())
                return
            if line=='0' or line =='':
                line='1'
            if self.ops:
                if line in self.ops.keys():
                    self.step=0
                    self.active_op = self.int_(line)
                    self.op_id = self.ops[line]['ID']
                    self.state = 'form_repo_ops'
                    self.handle_form_repo_ops(line)
                    return

            message ="\nNo te entiendo"
            self._snd(self.get_str_list_repo_ops(), message)
            return

        if order_line == PRE_PACK:
            #Es un paquete
            for op_ in self.ops:
                op = self.ops[op_]
                if op['package'] == line or op['pack_id'] == self.int_(line):
                    self.last_state = "list_repo_ops"
                    self.active_op = self.int_(op_)
                    self.op_id = op['ID']
                    self.step=2
                    self.state = 'form_repo_ops'
                    self.handle_form_repo_ops(PRE_PACK + line)
                    return
            message = u'\nPaquete no Válido'
            self._snd(self.get_str_list_repo_ops(), message)
            return

    def get_str_form_repo_ops_con_uos(self):

        self.last = "get_str_form_repo_ops"
        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
        num_ops = len(self.ops)
        op_=self.ops[str(self.active_op)]
        self.op_id = op_['ID']

        if op_['VISITED'] == False:
            op_['VISITED'] =True
            res = self.factory.odoo_con.change_op_value(self.user_id, self.op_id, 'visited', True)

        not_vis = 0
        not_proc = 0
        for op in self.ops:
            op__=self.ops[op]
            if op__['VISITED']:
                not_vis += 1
            if op__['PROCESADO']:
                not_proc += 1
        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")
        header = u"%s: Faltan %s de %s\n"%(self.tasks[self.active_task]['ref'], (num_ops-not_proc), num_ops )
        if self.tasks[self.active_task]['paused'] == True:
            header = self.inverse(header)

        # header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
        #          + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "***************************\n"
        strg = header
        keys=''
        orden =''

        strg = header
        strg += u"%s\n"%op_['product']
        if self.step ==0:
            #no leimos paquete los datos son solo de op
            if not op_['PROCESADO']:
                strg +=self.inverse(u"%s:%s "%(self.show_id*str(op_['pack_id']), str(op_['paquete']))) + u'(%s)\n'%op_['lot']
            else:
                strg +=u"%s:%s "%(self.show_id*str(op_['pack_id']), str(op_['paquete'])) + u'(%s)\n'%op_['lot']

            #entiendo que las tareas de reposición siempre se tratan en la unidad de stock
            strg += u"\n%s %s"%(op_['packed_qty'],op_['uom'])
            strg += u"\nDe %s: %s"%(op_['origen_id']*self.show_id, op_['origen_bcd'])
            strg += u"\nA %s: %s"%(op_['destino_id']*self.show_id, op_['destino_bcd'])
            if not op_['PROCESADO']:
                orden = self.inverse (u'\nScan Paquete')

        if self.step in [2,3,5,7,9]:
            #Paquete + Lote
            strg +=u"%s:%s "%(self.show_id*str(op_['pack_id']), str(op_['paquete'])) + u'(%s)\n'%op_['lot']

            #Unidades, si es la misma solo muestra una linea

            strg += u"\n%s %s"%(op_['packed_qty'],op_['uom'])
            strg += u"\nDe %s: %s"%(op_['origen_id']*self.show_id, op_['origen_bcd'])
            strg += u"\nA %s: %s"%(op_['destino_id']*self.show_id, op_['destino_bcd'])


            if self.step == 2:
                orden = self.inverse (u'\nCantidad (en %s)\nScan Destino para fin')%self.pack['uom']

            if self.step in [3,7]:
                strg += self.inverse(u'\n%s %s')%(self.new_uom_qty, self.pack['uom']) + ' ' + u'(%s %s)'%(self.new_uos_qty, self.pack['uos'])
                orden = self.inverse (u'\nIntro cantidad (%s)')%self.pack['uom']
                if self.step == 7:
                    orden += u'%s Cambiar a %s'%(KEY_QTY,  self.pack['uos'])
            if self.step ==5:
                strg += self.inverse(u"\n%s %s (%s %s) "%(self.new_uos_qty, self.pack['uos'], self.new_uom_qty, self.pack['uom']))
                orden = self.inverse (u'\nIntro cantidad (%s)\n%s Cambiar a %s')%(self.pack['uos'], KEY_QTY,  self.pack['uom'])

            if self.step == 9:
                strg += self.inverse(u"\n%s %s"%(self.new_uom_qty, self.pack['uom']))
                orden = self.inverse (u'\nIntro cantidad (%s)'%self.pack['uom'])

            if self.step == 7 or self.step == 9:
                orden += self.inverse (u' (%s)'%KEY_CONFIRM)

        if self.step in [4,6,8]:
            strg +=u"%s:%s "%(self.show_id*str(op_['pack_id']), str(op_['paquete'])) + u'(%s)\n'%op_['lot']
            strg += u"\n%s %s %s %s"%(op_['packed_qty'],op_['uom'], op_['uos_qty'], op_['uos'])
            #strg += u"\n%s: %s"%(self.pack['qty'], self.pack['uom'])
            strg += u"\nDe %s: %s"%(op_['origen_id']*self.show_id, op_['origen_bcd'])
            strg += u"\nA %s: %s"%(op_['destino_id']*self.show_id, op_['destino_bcd'])

            if self.step in [4,8]:
                strg += u'\n%s %s'%(self.new_uom_qty, self.pack['uom']) + ' ' + self.inverse(u'(%s %s)'%(self.new_uos_qty, self.pack['uos']))

                orden = self.inverse (u'\nIntro cantidad (%s)')%self.pack['uos']
                if self.step == 8:
                    orden += u'%s Cambiar a %s'%(KEY_QTY,  self.pack['uom'])
            if self.step == 6:
                strg += self.inverse(u"\n%s %s (%s %s) "%(self.new_uos_qty, self.pack['uos'], self.new_uom_qty, self.pack['uom']))
                orden = self.inverse (u'\nIntro cantidad (%s)\n%s Cambiar a %s')%(self.pack['uos'],KEY_QTY, self.pack['uom'])

        if self.step == 10:
            strg += u"\n%s: %s"%(self.pack['package'], self.pack['lot'])
            #strg += u"\n%s: %s"%(self.pack['qty'], self.pack['uom'])
            strg += u"\n%s %s (%s %s)"%(op_['packed_qty'],op_['uom'], op_['uos_qty'], op_['uos'])
            strg += u"\nDe %s: %s"%(op_['origen_id']*self.show_id, op_['origen_bcd'])
            strg += self.inverse(u"\nA %s: %s"%(op_['destino_id']*self.show_id, op_['destino_bcd']))

            #strg += u"\n%s %s %s %s"%(op_['packed_qty'],op_['uom'], op_['uos_qty'], op_['uos'])
            if self.pack['uos']!= self.pack['uom']:
                strg += u"\n%s %s (%s %s) "%(self.new_uom_qty, self.pack['uom'], self.new_uos_qty, self.pack['uos'])
            else:
                strg += u"\n%s %s"%(self.new_uom_qty, self.pack['uom'])

            orden = self.inverse (u'\nScan Destino')
            if self.pack['packed_qty']<self.new_uom_qty or self.pack['uos_qty']<self.new_uos_qty:
                orden += self.inverse (u'\nNo hay qty suficiente')

        strg += orden

        if op_['PROCESADO']:
            strg += self.inverse(u"[x] %s Cancel Op\n"%KEY_CANCEL)

        keys += u"\n%s Volver "%KEY_VOLVER
        if self.show_keys:
            strg += keys

        return strg

    def get_str_form_repo_ops(self):

        self.last = "get_str_form_repo_ops"

        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
        num_ops = len(self.ops)
        op_=self.ops[str(self.active_op)]
        self.op_id = op_['ID']

        if op_['VISITED'] == False:
            op_['VISITED'] =True
            res = self.factory.odoo_con.change_op_value(self.user_id, self.op_id, 'visited', True)
        if self.do_pack:
            do_pack ='x'
        else:
            do_pack =' '

        not_vis = 0
        not_proc = 0
        for op in self.ops:
            op__=self.ops[op]
            if op__['VISITED']:
                not_vis += 1
            if op__['PROCESADO']:
                not_proc += 1
        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")
        header = u"%s: Faltan %s de %s\n"%(self.tasks[self.active_task]['ref'], (num_ops-not_proc), num_ops )
        if self.tasks[self.active_task]['paused'] == True:
            header = self.inverse(header)

        # header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
        #          + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "***************************\n"
        strg = header
        keys=''
        orden =''

        strg = header
        strg_product = u"%s"%op_['product']
        if self.step==0:
            strg_package = u"\n%s - %s"%(str(op_['paquete']), op_['lot'])
            strg_de = u"\nDe %s"%op_['origen_bcd']
        else:
            strg_package = u"\n%s - %s"%(str(self.pack['package']), self.pack['lot'])
            strg_de = u"\nDe %s"%self.pack['src_location_bcd']

        strg_qty_op = u"\nMover: %s %s"%(op_['packed_qty'],op_['uom'])
        if self.step>0:
            strg_qty_package = u"\nStock %s %s"%(self.pack['packed_qty'],self.pack['uom'])
        strg_qty_actual = u"\nActual %s %s"%(self.new_uom_qty,op_['uom'])
        strg_a = u"\nA  %s"%op_['destino_bcd']

        if self.step ==0:
            #no leimos paquete los datos son solo de op
            if not op_['PROCESADO']:
                strg_package = self.inverse(strg_package)
                orden = self.inverse (u'\nScan Paquete')

        if self.step in [2,3,5,7,9]:
            if self.step == 2:
                strg_a = self.inverse(strg_a)
                orden = u'\nCantidad (en %s)\nScan Destino para fin'%op_['uom']

            if self.step == 3:
                strg_qty_actual = self.inverse(strg_qty_actual)
                orden = u'\nCantidad (en %s)\nScan Destino para fin'%op_['uom']

        if self.step == 10:
            if self.pack['packed_qty']<self.new_uom_qty:
                orden += self.inverse (u'\nNo hay qty suficiente\n%s Volver'%KEY_VOLVER)
            else:
                orden += self.inverse (u'\n%s Confirmar'%KEY_CONFIRM)

        strg += strg_product
        strg += strg_package
        if self.step == 0:
            strg += strg_qty_op
        if self.step == 2:
            #strg += strg_qty_package
            strg += strg_qty_op
            #strg += strg_qty_actual

        if self.step == 3 or self.step == 10:
            strg += strg_qty_package
            strg += strg_qty_op
            strg += strg_qty_actual

        strg += strg_de
        strg += strg_a
        strg += u'\n[%s] Fusionar Paquete (%s)\n'%(do_pack, KEY_DO_PACK)
        strg += orden

        if op_['PROCESADO']:
            strg += self.inverse(u"\n[x] %s Cancel Op\n"%KEY_CANCEL)

        qty_sum = 0
        list=''
        if self.step>0 and len(self.qty_calc)>1:
            for qty in self.qty_calc:
                    qty_sum += qty
                    list += u'[%s]'%qty
            qty_count = len(self.qty_calc)
            message_qtys = u'\n%s: %s'%(qty_count, list)
            self.new_uom_qty = qty_sum
            strg += message_qtys

        keys += u"\n%s Volver"%KEY_VOLVER
        if self.show_keys:
            strg += keys

        return strg

    def handle_form_repo_ops(self, line, confirm=False):

        def reset_qties():
            self.calc=[]
            self.new_uom_qty = 0
            self.new_uos_qty = 0
            self.qty_calc=[]

        default_line = line
        # if self.step == 0 and (line == '0' or line ==''):
        #     self._snd(self.get_str_form_repo_ops())
        #     return
        #     self.handle_form_repo_ops(line ='1')
        #     return
        order_line = line[0:2]
        if line[0:1] == "F" or line[0:1]=="K":
            function_key = True
        else:
            function_key = False
        message_qtys =''
        message =''
        op_ = self.ops[str(self.active_op)]

        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
            line_int=self.int_(line)
            line_float = self.float_(line)
        else:
            line_int=self.int_(line)
            line_float = self.float_(line)
            order_line = False
            self.last_read = False


        if line == KEY_VOLVER:
            if self.step==0:
                self.state = 'list_repo_ops'
                reset_qties()

                self._snd(self.get_str_list_repo_ops())
                return
            if self.step == 10:
                reset_qties()
                self.step = 2
            elif self.step >10:
                self.step = 10
            elif self.step ==4:
                self.step=3
            elif self.step ==6:
                self.step = 5
            elif self.step ==8:
                self.step = 7
            elif self.step in [3,5,7,9]:
                reset_qties()
                self.step =2
            else:
                self.step =0
                self.pack = {}
                self.product = {}
                reset_qties()
            self._snd(self.get_str_form_repo_ops())
            return

        if line == KEY_DO_PACK:
            self.do_pack= not self.do_pack
            if self.do_pack:
                self.pack_type = 'do_pack'
            else:
                self.pack_type = 'no_pack'
            self._snd(self.get_str_form_repo_ops())
            return

        #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
        if line == KEY_NEXT:
            num_ops = len(self.ops)
            self.active_op +=1
            if self.active_op > num_ops:
                self.active_op = 1
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        if line == KEY_PREV:
            self.active_op -=1
            if self.active_op <= 0:
                self.active_op = len(self.ops)
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        #Si la tarea esta pausada, no pasa de aquí
        if self.tasks[self.active_task]['paused'] == True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_repo_ops(), ERROR_TAREA_EN_PAUSA)
            return

        #Si la operación está procesada, solo permito Cancelar el Proceso
        if line == KEY_CANCEL:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
            self.pack = {}
            self.product ={}

            self.reset_vals()
            self.step =0
            self.state = 'list_repo_ops'
            message =u"\nTarea Cancelada"
            self._snd(self.get_str_list_repo_ops() + message)
            return

        #Si está procesada, no pasa de este if
        if op_['PROCESADO']== True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_repo_ops())
            return

        if self.step == 0 and order_line == PRE_PACK: #step 0 solo paquete
            if line_int == op_['pack_id'] or (line_int == self.new_package_id and confirm == True):
                self.new_package_id= False
                reset_qties()
                self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                self.product = self.factory.odoo_con.get_product_gun_complete_info(self.user_id,
                                                                                   self.pack['product_id'])
                self.fc = self.factory.odoo_con.conv_units_from_gun(self.user_id,
                                                                    self.product['product_id'],
                                                                    self.pack['uom_id'],
                                                                    self.pack['uos_id'])
                self.vals['paquete'] = self.pack['package_id']

                self.step = 2
                message =""#u"\n%s Ok Cantidades"%KEY_CONFIRM
                self._snd(self.get_str_form_repo_ops() + message)
                return

            else:
                message = u"\nNo es el paquete pedido\no no lo encuentro"
                self.new_package_id = False
                self._snd(self.get_str_form_repo_ops() + message)
                return
                self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                if line_int==self.new_package_id and confirm == False:
                      self.handle_form_repo_ops('%s%s'%(PRE_PACK,line_int), confirm=True)
                      return


                elif self.pack['exist'] and self.pack['product_id'] == op_['product_id']:
                    message = u"\nNo es el paquete pedido\nREscan para confirmar"
                    self.new_package_id = self.pack['package_id']
                    self._snd(self.get_str_form_repo_ops() + message)
                    return
                else:
                    message =u"\nError en paquete\nScan Paquete"
                    self.new_package_id = False
                    self._snd(self.get_str_form_repo_ops() + message)
                    return

        self.new_package_id = False
        if self.step>0  and order_line == PRE_PACK:
            #REINICIO OPERACION
            self.pack = {}
            self.product ={}
            self.reset_vals()
            self.step =0
            self.handle_form_repo_ops(PRE_PACK + line)
            return

        if self.step >=2 and not order_line and line_float and not function_key and line_float!=0:
            #si introduciomos una cantidad
            self.step = 3
            list = ''
            qty_sum = 0

            if line_float>0:
                self.qty_calc.append(line_float)
            else:
                try:
                    self.qty_calc.remove(line_float * -1)
                except:
                    res = False

            for qty in self.qty_calc:
                qty_sum += qty
                list += u'[%s]'%qty
            qty_count = len(self.qty_calc)
            message_qtys = u'\n%s: %s'%(qty_count, list)

            self.new_uom_qty = qty_sum

            message = ''#message_qtys
            self._snd(self.get_str_form_repo_ops() + message)
            return


        if line == KEY_CONFIRM:
            # if self.step == 3:
            #     self.step = 10
            #     self._snd(self.get_str_form_repo_ops() + message)
            #     return

            if self.step == 15:
                if self.new_uom_qty <= self.pack['packed_qty']:
                    res = self.finish_repo_op()
                    return
                else:
                    self.step = 10
                    self._snd(self.get_str_form_repo_ops() + message)
                    return
            message = u'\nNo válido'
            self._snd(self.get_str_form_repo_ops() + message)
            return

        if self.step in [2,3, 10] and order_line == PRE_LOC \
                and line_int == op_['destino_id']:
            if self.step == 2:
                self.new_uom_qty = self.pack['packed_qty']
                self.step = 15
                self.handle_form_repo_ops(line = KEY_CONFIRM)
                return
            if self.step == 10 or self.step ==3:
                if self.new_uom_qty <= self.pack['packed_qty']:
                    self.step = 15
                    self.handle_form_repo_ops(line = KEY_CONFIRM)
                    return
                else:
                    self._snd(self.get_str_form_repo_ops())
                    return
            message = u'No te entiendo'
            self._snd(self.get_str_form_repo_ops() + message)
            return

        if not default_line in self.ops.keys():
            message =u"\nNo Válido"

        self._snd(self.get_str_form_repo_ops() + message)
        return

    def handle_form_repo_ops_con_ops(self, line, confirm=False):

        def reset_qties():
            self.calc=[]
            self.new_uom_qty = 0
            self.new_uos_qty = 0
            self.qty_calc=[]

        default_line = line
        # if self.step == 0 and (line == '0' or line ==''):
        #     self._snd(self.get_str_form_repo_ops())
        #     return
        #     self.handle_form_repo_ops(line ='1')
        #     return
        order_line = line[0:2]
        if line[0:1] == "F" or line[0:1]=="K":
            function_key = True
        else:
            function_key = False
        message_qtys =''
        message =''
        op_ = self.ops[str(self.active_op)]

        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
            line_int=self.int_(line)
            line_float = self.float_(line)
        else:
            line_int=self.int_(line)
            line_float = self.float_(line)
            order_line = False
            self.last_read = False


        if line == KEY_VOLVER:
            if self.step==0:
                self.state = 'list_repo_ops'
                reset_qties()

                self._snd(self.get_str_list_repo_ops())
                return
            if self.step == 10:
                self.step = 2
            elif self.step >10:
                self.step = 10
            elif self.step ==4:
                self.step=3
            elif self.step ==6:
                self.step = 5
            elif self.step ==8:
                self.step = 7
            elif self.step in [3,5,7,9]:
                reset_qties()
                self.step =2
            else:
                self.step =0
                self.pack = {}
                self.product = {}
                reset_qties()
            self._snd(self.get_str_form_repo_ops())
            return





        #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
        if line == KEY_NEXT:
            num_ops = len(self.ops)
            self.active_op +=1
            if self.active_op > num_ops:
                self.active_op = 1
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        if line == KEY_PREV:
            self.active_op -=1
            if self.active_op <= 0:
                self.active_op = len(self.ops)
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        #Si la tarea esta pausada, no pasa de aquí
        if self.tasks[self.active_task]['paused'] == True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_repo_ops(), ERROR_TAREA_EN_PAUSA)
            return

        #Si la operación está procesada, solo permito Cancelar el Proceso
        if line == KEY_CANCEL:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
            self.pack = {}
            self.product ={}

            self.reset_vals()
            self.step =0
            self._snd(self.get_str_form_repo_ops())
            return

        # if self.step==0 and not order_line:
        #     if line_int== self.ops[str(self.active_op)]['pack_id']:
        #         self.vals ['paquete'] = self.ops[str(self.active_op)]['pack_id']
        #         self.step = 1
        #         message =u"\nEscanea Paquete"
        #         self._snd(self.get_str_form_repo_ops() + message)
        #         return

        #Si está procesada, no pasa de este if
        if op_['PROCESADO']== True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_repo_ops())
            return

        if self.step == 0 and order_line == PRE_PACK: #step 0 solo paquete

            if line_int == op_['pack_id'] or (line_int == self.new_package_id and confirm == True):

                self.new_package_id= False
                reset_qties()
                self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                self.product = self.factory.odoo_con.get_product_gun_complete_info(self.user_id,
                                                                                   self.pack['product_id'])
                self.fc = self.factory.odoo_con.conv_units_from_gun(self.user_id,
                                                                    self.product['product_id'],
                                                                    self.pack['uom_id'],
                                                                    self.pack['uos_id'])
                self.vals['paquete'] = self.pack['package_id']

                self.step = 2
                message =u"\n%s Ok Cantidades"%KEY_CONFIRM
                self._snd(self.get_str_form_repo_ops() + message)
                return

            else:
                self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                if line_int==self.new_package_id and confirm == False:
                      self.handle_form_repo_ops('%s%s'%(PRE_PACK,line_int), confirm=True)
                      return


                elif self.pack['exist'] and self.pack['product_id'] == op_['product_id']:
                    message = u"\nNo es el paquete pedido\nREscan para confirmar"
                    self.new_package_id = self.pack['package_id']
                    self._snd(self.get_str_form_repo_ops() + message)
                    return
                else:
                    message =u"\nError en paquete\nScan Paquete"
                    self.new_package_id = False
                    self._snd(self.get_str_form_repo_ops() + message)
                    return

        self.new_package_id = False
        if self.step>0  and order_line == PRE_PACK:
            #REINICIO OPERACION
            self.step =0
            self.handle_form_repo_ops(PRE_PACK + line)
            return

        if self.step !=0 and not order_line and line_float and not function_key and line_float!=0:
            #si introduciomos una cantidad

            if self.step == 2 :
                #solo nos vale una cantidad
                #es una cantidad
                if op_['uom_id']==op_['uos_id']:
                    #mmisma unidad
                    self.step=9
                elif self.product['is_var_coeff']:
                    #es variable
                    self.step = 3
                else:
                    self.step= 7

                self.handle_form_repo_ops(line)
                return

            elif self.step in [3, 5, 7, 8, 9]:
                list = ''
                qty_sum = 0

                if line_float>0:
                    self.qty_calc.append(line_float)

                else:
                    try:
                        self.qty_calc.remove(line_float * -1)
                    except:
                        res = False

                for qty in self.qty_calc:
                    qty_sum += qty
                    list += u'%s '%qty
                qty_count = len(self.qty_calc)
                message_qtys = u'\n[%s] %s'%(qty_count, list)

                if self.step == 3:
                    self.new_uom_qty = qty_sum
                    self.new_uos_qty = qty_count
                elif self.step == 5:
                    self.new_uos_qty = qty_sum
                    self.new_uom_qty = qty_count
                elif self.step == 7:
                    self.new_uom_qty = qty_sum
                    self.new_uos_qty = qty_sum * self.fc
                elif self.step == 8:
                    self.new_uos_qty = qty_sum
                    self.new_uom_qty = qty_sum / self.fc
                elif self.step == 9:
                    self.new_uom_qty = qty_sum
                    self.new_uos_qty = qty_sum

            elif self.step ==4 :
                self.new_uos_qty = line_float

            elif self.step ==6 :
                self.new_uom_qty = line_float

            message = message_qtys
            self._snd(self.get_str_form_repo_ops() + message)
            return

        change_qtys_possible = False

        if line == KEY_QTY and change_qtys_possible:
            reset_qties()
            if self.step ==2:
                if op_['uom_id']==op_['uos_id']:
                    self.step=9
                elif self.product['is_var_coeff']:
                    #es variable
                    self.step = 3
                else:
                    self.step= 7
            # elif self.step ==3:
            #     self.step =5
            # elif self.step ==5:
            #     self.step =3
            elif self.step ==7:
                self.step =8
            elif self.step ==8:
                self.step =7

            self._snd(self.get_str_form_repo_ops() + message)
            return

        if line == KEY_CONFIRM:

            if self.step == 2 :
                self.new_uom_qty = op_['packed_qty']
                self.new_uos_qty = op_['uos_qty']
                self.step = 10

            elif self.step ==3:
                self.step=4

            elif self.step ==5:
                self.step =6

            elif self.step in [4,6,7,8,9]:
                self.step = 10

            self._snd(self.get_str_form_repo_ops() + message)
            return

        if self.step == 2 and order_line == PRE_LOC \
                and line == str(self.product['picking_location_id']):
                    self.new_uom_qty = op_['packed_qty']
                    self.new_uos_qty = op_['uos_qty']
                    self.step =10
                    self.handle_form_repo_ops(default_line)
                    return

        if (self.step ==7 or self.step == 9) and \
                        order_line == PRE_LOC and \
                        line == str(self.product['picking_location_id']):
            #podemos confirmar desde step 9 : solo una cantidad
            #o podemos confirmar la cantidad si no es variable
            #ya que las sabemos desde el principio
            self.step =10
            self.handle_form_repo_ops(default_line)
            return

        if self.step ==10 and order_line == PRE_LOC:
            location_id = line_int
            location = self.factory.odoo_con.get_location_gun_info(self.user_id, location_id=line_int)

            #Concide con la ubicación de picking del producto
            #Entonces ok
            if line == str(self.product['picking_location_id']):
                self.ops[str(self.active_op)]['destino_id'] = line
                res = self.finish_repo_op()
                return

            #coincide con la ubicación padre del producto
            elif location['parent_id'] == line_int:
                #hemos escaneado una ubicación padre, muestra el menu hijas
                #para seleccionar
                self.step=11
                self.last_read = line_int
                self.subzones = False
                self.last_state= self.state
                self.state ='select_subzone'
                self.selected_subzone = False
                self.menu_anterior = 'get_str_form_repo_ops'
                self._snd(self.get_str_select_picking_subzone(line_int))
                return
            #producto sin zona de picking asignada y escaneamos una cantidad

            elif self.factory.odoo_con.check_picking_zone(self.user_id,
                                                            self.product['product_id'],
                                                            line_int, write = False):
                self.ops[str(self.active_op)]['destino_id'] = line_int
                self.step == 13
                message += u'\n%s Asignar Pick Zone\n%s No asignar'%(KEY_RUN, KEY_NO)
                self._snd(self.get_str_form_repo_ops() + message)
                return

            elif location:
                self.step = 15
                self.ops[str(self.active_op)]['destino_id'] = line_int
                message = u"\n%s Confirmar"%KEY_CONFIRM
                self._snd(self.get_str_form_repo_ops() + message)
                return


        if self.step == 13:
            if line == KEY_YES:
                #se actualiza
                res = self.factory.odoo_con.check_picking_zone(self.user_id,
                                                        self.product['product_id'],
                                                        self.last_read, write = True)
                self.step = 15
                self.product['picking_location_id'] = self.last_read
                self.ops[str(self.active_op)]['destino_id'] = self.line_int
                message = u"\nAsignadaa Zona de Picking\%s Para Mover"%KEY_CONFIRM
                self._snd(self.get_str_form_repo_ops() + message)
                return


            if line == KEY_NO:

                self.ops[str(self.active_op)]['destino_id'] = self.last_read
                self.last_read = False
                self.step = 15
                #res = self.finish_repo_op()
                message += u'\n%s Mover'%KEY_CONFIRM
                self._snd(self.get_str_form_ops() + message)
                return

        if self.step == 15:
            res = self.finish_repo_op()
            return

        if self.step ==11:
            if line_int:
                if line_int >0 and line_int < len(self.subzones):
                    self.step =10
                    self.handle_form_repo_ops(PRE_LOC + self.subzones[line_int]['id'])
                    return
            #
            #
            #
            #
            # if line == KEY_RUN:
            #         if self.factory.odoo_con.check_picking_zone(self.user_id,
            #                                                 self.product['product_id'],
            #                                                 self.last_read, write = True):
            #             self.product['picking_location_id'] = self.last_read
            #             message += u'\nAsignada'%KEY_RUN
            #             self._snd(self.get_str_form_ops() + message)
            #             return
            #
            # location_id = self.subzones[line_int]['id']
            # self.last_read = location_id
            # location = self.factory.odoo_con.get_location_gun_info(self, location_id=location_id)
            #
            # if location_id == self.product['picking_location_id']:
            #     #1º caso, conincide con el que nos pide
            #     if self.confirm_last_step==False or confirm == True:
            #         res = self.finish_repo_op()
            #         return
            #
            # else:
            #     #si está libre, pregunta si se asigna
            #     if not self.factory.odoo_con.is_location_free(location_id):
            #         message += u'\n%s Asignar Pick Zone\n'%KEY_CONFIRM
            #         self._snd(self.get_str_form_ops(), message)
            #         return
            #
            #     message =u"Ubicacion no valida"
            #     self._snd(self.get_str_form_repo_ops() + message)
            #     return
            #

        if not default_line in self.ops.keys():
            message =u"\nNo Válido"
        self._snd(self.get_str_form_repo_ops() + message)
        return

    def finish_repo_op(self, message = ''):
        #creamosop_
        #  el values

        op_ = self.ops[str(self.active_op)]
        values = {}
        self.op_id=op_['id']
        res = False

        #es producto y no cambiamos cantidad o es paquete y no cambiamos cantidad
        #(confirmamos la operación)
        if self.new_uom_qty == op_['packed_qty']:
             values ={
                'to_process': True,
                'visited': True,
           }
        # es producto y cambiamos cantidad
        elif op_['op_product_id'] and self.new_uom_qty > 0:
             values ={
                'product_qty': self.new_uom_qty,
                'to_process': True,
                'visited': True,
             }
        #no es producto y cambiamos cantidad
        elif not op_['op_product_id'] and  self.new_uom_qty > 0:#self.new_uom_qty != self.pack['packed_qty']:
            #Cambiamos la cantidad del paquete
            values ={
                'to_process': True,
                'visited': True,
                'product_id' : self.pack['product_id'],
                'product_uom_id' : self.pack['uom_id'],
                'product_qty': self.new_uom_qty,
                'packed_qty':  self.new_uom_qty,
                'do_pack': self.pack_type,
                'result_package_id': False
            }

        if values:
            res = self.factory.odoo_con.change_op_values(self.user_id, self.op_id, values)

        pack_destino = self.factory.odoo_con.get_package_of_lot_from_gun(self.user_id,
                                                                                op_['destino_id'],
                                                                                op_['lot_id'])
        #IMPRIMIMOS
        tag=[]
        message, print_tag = self.get_tags_message(self.pack_type, pack_destino, values.get('product_id', False))

        if res:
            #self.print_op_tags(self.op_id)
            #recargamos operaciones para actualizar cambios
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
            # y buscamos la primera no procesada
            active_op = False
            for op in self.ops:
                if self.ops[op]['to_process']:
                    continue
                else:
                    self.op_id=self.ops[op]['id']
                    self.active_op = self.int_(op)
                    active_op = True
                    break

            self.pack={}
            self.product={}
            self.new_uom_qty=0
            self.new_uos_qty=0
            self.qty_cal=[]
            self.step=0
            if active_op:
                self.step=0
            else:
                self.step=0
        else:
            message =u"Error. Revisa cantidades"
            self.state = 'list_repo_ops'
            self._snd(self.get_str_list_repo_ops() + message)
            return
        self.state = 'list_repo_ops'
        self._snd(self.get_str_list_repo_ops() + message)
        return

    def get_str_list_ops(self):
        self.last = "get_str_list_ops"
        header =''
        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
        if self.ops:
            header = u"Ops en %s\n"%self.tasks[self.active_task]['ref']
        return self.get_str(self.ops, header)

    def get_str_list_waves(self):
        self.last = "get_str_list_waves"

        # En vez de operaciones, sacamos wave_reports
        self.active_wave = 1
        self.waves = self.factory.odoo_con.get_wave_reports_from_task(self.user_id, self.task_id, self.type)

        header = u"Picks %s %s\n" %(self.task_id, self.route)
        if self.waves:
            header = u"%s\n"%self.waves['1']['name']
        return self.get_str(self.waves , header)

    def get_str_list_wave_ops(self):
        self.last = "get_str_list_wave_ops"
        data_ = self.factory.odoo_con.get_ops(self.user_id, self.wave_id, self.type)
        if not self.wave_id:
            self.wave_id =  self.tasks[self.active_task]['wave_id']
        header =u"Operaciones en %s\n"%str(self.tasks[self.active_task]['wave_id'])
        return self.get_str(data_, header)

    def get_str(self, data_, header =''):
        #Saca una lista de operaciones o picks
        #si no hay ninguna ubicación

        keys =u''
        total = len(data_)

        if (self.type =="ubication" or self.type == "reposition" ) and not self.ops:
            strg =u'Tarea creada.\nScan Paquete para añadir ops\n'
        else:
            header1=''
            if self.type!='picking':
                not_vis = 0
                not_proc = 0
                total = len(data_)
                for op in data_:
                    op__=data_[op]
                    if op__['VISITED']:
                        not_vis += 1
                    if not op__['PROCESADO']:
                        not_proc += 1
                header1 += u"Faltan %s de %s\n"%(not_proc, len(data_))

            delimiter = "*" * 25 + u"\n"
            strg = header + header1 #+ delimiter
            #lo que mostramos como a continuación de paquete
            #depende de si es ubicaion o picking
            if self.type == 'ubication':
                after_PAQUETE = 'destino_bcd'
            else:
                after_PAQUETE = 'origen_bcd'
            inc=0

            for k in range(self.num_order_list_ops, total + 1):
                k_ = str(k)
                if k_ in data_:
                    op_processed = data_[k_]['PROCESADO']
                    if k <= len(data_):
                        k_ = str(k)
                        op = k_ + '>'

                        if not op_processed:
                            op = self.inverse(op)
                        op +=u'%s \n >%s\n'%(data_[k_]['package'], data_[k_][after_PAQUETE])
                    if self.show_op_processed or not op_processed:
                        strg += op
                        inc+=1
                    if inc>MAX_NUM:
                        break

            if self.tasks[self.active_task]['type']=="reposition":
                keys += u"%s Fin Tarea "%KEY_CONFIRM
            elif self.tasks[self.active_task]['type']=="ubication":
                keys += u"%s Fin Tarea "%KEY_CONFIRM
            elif self.tasks[self.active_task]['type']=="picking":
                keys += u"%s Fin Picking "%KEY_FINISH

        strg += keys
        keys = ''
        keys += u"%s Atrás"%KEY_VOLVER
        if self.tasks[self.active_task]['paused']:
            opc = u'Run'
        else:
            opc = u'Pause'
        keys += u"\n%s %s %s Cancelar Tarea"%(KEY_PAUSE, opc, KEY_CANCEL)
        if self.show_keys:
            strg += keys
        return strg

    def handle_list_waves(self, line, confirm=False):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        if not order_line:
            if line == KEY_PAUSE:
                aux = self.task_id
                pause = not self.tasks[self.active_task]['paused']
                res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                                self.tasks[self.active_task]['id'],
                                                                pause)
                self.check_task()
                self.task_id = aux
                self.active_task = self.get_active_task()
                self._snd(self.get_str_list_ops())
                return

            if line == KEY_VOLVER and self.step!=5:
                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM <=len(self.waves):
                    self.num_order_list_ops += MAX_NUM
                self._snd(self.get_str_list_waves())
                return
            if line == KEY_PREV:
                self.num_order_list_ops -= MAX_NUM
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self._snd(self.get_str_list_waves())
                return



            if line == KEY_FINISH:
                all_processed = True
                for wave in self.waves:
                    if not self.waves[wave]['PROCESADO'] and not self.waves[wave]['to_revised']:
                        all_processed = False
                if all_processed:
                    self.step = 5
                    self.handle_list_waves(KEY_YES)
                    return
                else:
                    self.step = 5
                    message =u"Ops no ok\nContinuar? %s o no %s"%(KEY_YES, KEY_CANCEL)
                    self._snd(self.get_str_list_waves(), message)
                    return



            if self.step==5 and (line == KEY_CANCEL or line==KEY_VOLVER) :
                self.step = 0
                message =u"Cancelado"
                self._snd(self.get_str_list_waves(), message)

            if line == KEY_YES and self.step==5:
                #marcamos la tarea como finalizada
                #llamamos a finish_partial_task de stock_task
                ok = self.factory.odoo_con.finish_task(self.user_id, self.task_id)
                if ok:
                    self.print_task(self.task_id)
                self.step=0
                self.last_state = "list_waves"
                self.state ='menu1'
                self.waves=False
                self.ops = False
                self.task_id=False
                self.reset_vals()
                self.handle_new_task()
                return


            if line in self.waves.keys():
                #seleccionamos un elemento del menu
                #aqui tengo que abrir list_ops
                self.last_state = "list_waves"
                self.active_op = self.int_(line)
                self.active_wave = self.int_(line)
                self.step = 0
                self.wave_id = self.waves[line]['ID']
                self.state = 'form_wave'
                self._snd(self.get_str_form_wave(), '')
                return

            message ="\nNo te entiendo"
            self._snd(self.get_str_list_waves(), message)
            return

        if order_line == PRE_PACK:

            one_package = 0
            order = False
            active_wave ='1'
            for op_ in self.waves:
                op = self.waves[op_]
                if op['pack_id'] == self.int_(line):
                    one_package+=1
                    active_wave=op_
                    order = order_line + line
            if one_package==1:
            #es un paquete de la lista de paquetes de esta tarea
                self.last_state = "list_waves"
                self.num_order_list_ops=1
                self.step=0
                self.active_wave = active_wave
                self.state = 'form_wave'
                self.handle_form_wave(order)
                return
            elif one_package>1:
                message = u'Usa teclado (%s)'%self.waves[op_]['package']
                self._snd(self.get_str_list_waves(), message)
                return


        # if order_line == PRE_LOC:
        #     for op_ in self.waves:
        #         op = self.waves[op_]
        #         if op['origen'] == line or op['origen_id'] == self.int_(line) and self.step == 0:
        #             #es un paquete de la lista de paquetes de esta tarea
        #             self.last_state = "list_waves"
        #             self.step=1
        #             self.num_order_list_ops=1
        #             self.handle_form_wave(order_line + line)
        #             return

        message = u'\nPaquete no Válido'
        self._snd(self.get_str_list_waves(), message)
        return

    def handle_list_wave_ops(self, line, confirm):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if not order_line:
            if line == KEY_VOLVER:
                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES

            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM <len(self.ops):
                    self.num_order_list_ops += MAX_NUM
                self._snd(self.get_str_list_wave_ops())
                return
            if line == KEY_PREV:
                self.num_order_list_ops -= MAX_NUM
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self._snd(self.get_str_list_wave_ops())
                return

            if line in self.waves.keys():
                #seleccionamos un elemento del menu
                #aqui tengo que abrir list_ops
                self.last_state = "list_wave_ops"
                self.active_op = int(line)
                self.active_wave = int(line)
                self.step =0
                self.wave_id = self.waves[line]['ID']
                self.state = 'list_form_wave'
                self._snd(self.get_str_wave_form(), '')
                return

            message ="\nNo te entiendo"
            self._snd(self.get_str_list_wave_ops(), message)
            return

        if order_line == PRE_LOC:
            for op_ in self.waves:
                op = self.waves[op_]
                if op['origen'] == line or op['origen_id'] == self.int_(line) and self.step == 0:
                    #es un paquete de la lista de paquetes de esta tarea
                    self.last_state = "list_wave_ops"
                    self.active_op = op_
                    self.wave_id = op['ID']
                    self.state = 'list_form_wave'
                    self.step =1
                    self._snd(self.get_str_wave_form(), '')
                    return

        message = u'\nPaquete/Origen no Válido'
        self._snd(self.get_str_list_wave_ops(), message)
        return

    def check_max_packet_qty(self, packet_id):
        packet_values = self.factory.odoo_con.get_quant_pack_gun_info_resumen(self.user_id, packet_id)
        qty = packet_values['qty']
        if self.new_uom_qty > qty:
            message = u'%s %s: (max %s)\nInsuficiente. %s Forzar'%\
                      (self.new_uom_qty, packet_values['uom'], qty, KEY_FINISH)
            return message
        return False

    def finish_picking(self, force = False):
        # caso 1: lo que nos piden es lo que pickieamos>
        #         finalizamos oks
        # caso 2: No coincide: 1 una op >
        #         Modificamos cantidades en OP y finalizamos
        # caso 3: No coincide: varias operaciones >
        #         No finalizamos>> Seteamos to_revised
        wave_ = self.waves[str(self.active_wave)]
        op_id = wave_['op']
        self.wave_id = wave_['ID']
        #Tengo que comprobar si
        if not force:
            message = self.check_max_packet_qty(wave_['pack_id'])
            if message != False:
                self._snd(self.get_str_form_wave(), message)
                return


        num_ops = wave_['num_ops']
        if wave_['is_var_coeff']:
            var_coeff = True
        num_ops = wave_['num_ops']

        if self.new_uom_qty == 0:
            values = {
                    'to_process':False,
                    'visited':False,
                    'wrong_qty': True
                }
            if num_ops ==1:
                self.factory.odoo_con.change_op_values(self.user_id, op_id, values)
            else:
                self.factory.odoo_con.set_wave_ops_values(self.user_id , self.wave_id, op_id, values)
            message= u'Falta Producto para OP'


        elif (wave_['uos_qty']== self.new_uos_qty and wave_['qty'] == self.new_uom_qty)\
                or (wave_['uos_qty']== self.new_uos_qty and num_ops==1) or \
                (wave_['qty']== self.new_uom_qty and num_ops==1):

            if wave_['qty'] != self.new_uom_qty:
                self.factory.odoo_con.change_op_value(self.user_id, op_id, 'product_qty', self.new_uom_qty)

            if wave_['uos_qty'] != self.new_uos_qty:
                self.factory.odoo_con.change_op_value(self.user_id, op_id, 'uos_qty', self.new_uos_qty)

            #CASO 1
            task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.user_id , self.wave_id, op_id, {'to_process':True})
            self.step = 0
            self.state = "list_waves"
            message = u'Operación Realizada'

        else:
            if num_ops == 1 :
                #CASO 2
                #DEBEMOS ESCRIBIR EN LA OP
                values = {
                    'uos_qty': self.new_uos_qty,
                    'product_qty':self.new_uom_qty,
                    'to_process':True,
                    'visited':True
                }
                self.factory.odoo_con.change_op_values(self.user_id, op_id, values)
                #self.factory.odoo_con.change_op_value(self.user_id, op_id, 'product_qty', self.new_uom_qty)
                #y finalizamos
                #task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.user_id , self.wave_id, op_id, 'to_process', True)
                self.step = 0
                self.state = "list_waves"
                message = u'Operación Realizada'


            elif num_ops>1:
                #CASO 3
                #Marcamos como to revised.
                #Si las cantidades son distintas y hay ás de una operación ...
                task_wave_not_ok = self.factory.odoo_con.new_wave_to_revised(self.user_id, self.new_uos_qty, self.new_uom_qty, self.wave_id, self.task_id)
                #task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.user_id , self.wave_id, op_id, {'to_process':True})
                self.step = 10
                message =u"Pendiente de Revisión"

        act = self.active_wave
        self.waves = self.factory.odoo_con.get_wave_reports_from_task(self.user_id, self.task_id, self.type)
        self.active_wave = act
        self.state= "list_waves"
        self._snd(self.get_str_list_waves(), message)
        return

    def handle_form_wave(self, line, confirm=False):

        #lo modifico para
        #step = 0: Espera localizacióny pasa a step 1
        #step 1, espera pack , si ok pasa a step9
        #if self.step>=3:
        line_int = self.int_(line)
        line_float = self.float_(line)
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        wave_= self.waves[str(self.active_wave)]



        if wave_['uos']==wave_['uom']:
            one_unit = True
        else:
            one_unit = False
        op_id = wave_['op']
        if order_line == PRE_PACK and self.step in [0,1,2]:

            op={}
            package_id = self.int_(line)
            #Es un paquete
            #miramos si está en la lista de paquetes de las operación
            if self.waves[str(self.active_wave)]['pack_id'] == package_id:
                op_= str(self.active_wave)
                op = self.waves[str(self.active_wave)]
            else:
                for op_ in self.waves:
                    if self.waves[op_]['pack_id'] == package_id:
                        op = self.waves[op_]
                        self.active_wave=op_
                        continue
                        #es un paquete de la lista de paquetes de esta tarea
            if op:
                self.last_state = "list_waves"
                self.state = 'form_wave'
                self.qty_calc = []
                self.new_uos_qty=0.00
                self.new_uom_qty=0.00
                self.new_package_id = False
                self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, package_id )
                self.product = self.factory.odoo_con.get_product_gun_complete_info(self.user_id, op['product_id'])
                self.fc = self.factory.odoo_con.conv_units_from_gun(self.user_id, op['product_id'], op['uom_id'], op['uos_id'])
                self.active_wave = op_
                self.active_op = op_
                self.wave_id = op['ID']
                self.step = 2
                self._snd(self.get_str_form_wave(), '')
            return

            # Se confirma cambio de packete
            if package_id == self.new_package_id and self.new_package_id:
                values = {'op_package_id' : op['pack_id'],
                          'package_id':self.new_package_id,
                          'packed_lot_id' : self.pack['lot_id'],
                          'location_id' : self.pack['src_location_id']
                          }
                res = self.factory.odoo_con.change_wave_op_values_packed_change(self.user_id, op_id, values)
                act = self.active_wave
                self.waves = self.factory.odoo_con.get_wave_reports_from_task(self.user_id, self.task_id, self.type)
                self.active_wave = act
                self.new_package_id = False
                self.qty_calc = []
                self.handle_form_wave(PRE_PACK + line)
                return



            # si no está en la lista de paquetes mitaos si existe y es válido
            self.pack = self.factory.odoo_con.get_pack_gun_info(self.user_id,package_id)
            if self.pack['exist']:
                if wave_['product_id'] == self.pack['product_id'] and self.pack['packed_qty']:
                    message =''
                    message += u"\nCambio Pack: %s\nScan para confirmarlo"%self.pack['package']
                    if self.pack['packed_qty'] < wave_['uom_qty']:
                        message +="Comprueba cantidades"
                    self.new_package_id = package_id
                    self.qty_calc = []
                    self.step = 1
                    self._snd(self.get_str_form_wave(), message)
                    return





            message = u'\nPaquete no Válido'
            self._snd(self.get_str_form_wave(), message)
            return


        if line in [KEY_CONFIRM, KEY_CANCEL, KEY_NEXT, KEY_PREV, KEY_QTY, KEY_VOLVER, KEY_FINISH]:

            if line == KEY_CANCEL:
                if wave_['PROCESADO']==True:
                    task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.user_id , self.wave_id, op_id, {'to_process':False})
                    self.step = 0
                    self.state = "list_waves"
                    self._snd(self.get_str_list_waves(), 'Picking cancelado')
                    return

                if self.step>2:
                    self.handler_form_wave('PKL' +  wave_['pack_id'])
                    return

                if self.step<=2:
                    self.step= 0
                    self._snd(self.get_str_form_wave(), '')
                    return

            # if line == KEY_NEXT:
            #     print (u'%s de %s')%(self.active_wave, len(self.waves))
            #     if self.active_wave < len(self.waves):
            #         self.active_wave += 1
            #
            #     self.step=0
            #     self._snd(self.get_str_form_wave())
            #     return
            #
            # if line == KEY_PREV:
            #     if self.active_wave >1:
            #         self.active_wave-=1
            #     self.step=0
            #     self._snd(self.get_str_form_wave())
            #     return

            if line == KEY_VOLVER:

                if self.step == 0:
                    self.last_state = self.state
                    self.state = "list_waves"
                    self._snd(self.get_str_list_waves())
                    return

                if self.step == 1:
                    self.step= 0
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==2:
                    self.step =0
                    self.qty_calc = []
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step in [3,5,5,6,7,8,9,10]:
                    self.step =2
                    self.new_uos_qty=0
                    self.new_uom_qty=0
                    self.qty_calc = []
                    self._snd(self.get_str_form_wave(), '')
                    return

            if line==KEY_CONFIRM:
                if self.step ==2:
                    self.new_uos_qty=wave_['uos_qty']
                    self.new_uom_qty=wave_['CANTIDAD']
                    self.step = 10
                    if self.confirm_last_step:
                        self._snd(self.get_str_form_wave(), '')
                        return
                    else:
                        self.finish_picking()
                        return
                #self.new_uom_qty = line_
                #self.new_uos_qty = round(line_ * self.fc, 2)
                if self.step ==3:
                    if one_unit or not self.product['is_var_coeff']:
                        self.step = 10
                    else:
                        self.step = 5
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==5:
                    self.step = 10
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step == 4:
                    if one_unit or not self.product['is_var_coeff']:
                        self.step = 10
                    else:
                        self.step = 6
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==6:
                    self.step = 10
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step in[8,9]:
                    self.step = 10
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step==10:
                    self.finish_picking()
                    return
                    #si lo que tenemos es lo que nos piden
                    if self.waves[str(self.active_wave)]['uos_qty']== self.new_uos_qty and \
                                    self.waves[str(self.active_wave)]['CANTIDAD']== self.new_uom_qty:

                        task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.user_id, self.wave_id, op_id, {'to_process':True})
                        # Si no funciona con varios probar esta
                        # task_ops_finish = self.factory.odoo_con.set_waves_op_processed(self.user_id, self.wave_id)
                        self.step = 0
                        self.state = "list_waves"
                        self._snd(self.get_str_list_waves(), 'Wave Finish')
                        return
                    if self.waves[str(self.active_wave)]['uos_qty'] != self.new_uos_qty:
                        #creamos un wave_report_to_revised
                        task_wave_not_ok = self.factory.odoo_con.new_wave_to_revised(
                            self.user_id, self.new_uos_qty, self.new_uom_qty, self.wave_id, self.task_id)

                        self.step = 10
                        message ="\nPara Revisión"
                        self._snd(self.get_str_form_wave(), message)
                        return
                self._snd(self.get_str_form_wave(), '')
                return

            if line == KEY_FINISH and self.step==10:
                self.finish_picking(force=True)
                return

            if line ==KEY_NO_REALIZADA:

                if self.step == 10:
                    self.step = 10
                    self._snd(self.get_str_form_wave(), '')
                    return
                    wave_id = 11
                    vals={
                        'to_revised': True,
                        'uos_qty': self.new_uos_qty,
                        'uom_qty': self.new_uom_qty
                    }
                    wave_id_to_revised =  self.factory.odoo_con.set_wave_reports_values(self.user_id, self.wave_id, self.user_id, vals, True)
                    self.step = 0
                    self.state = "list_waves"
                    self._snd(self.get_str_list_waves(), 'Op Finalizada. Para Revisión')
                    return


            if line == KEY_QTY and self.step in [2,3,4]:
                self.new_uos_qty=0
                self.new_uom_qty=0
                self.qty_calc=[]

                if self.step==3 or self.step ==2 or self.step ==5:
                    if one_unit:
                        message='No procede'
                        self._snd(self.get_str_form_wave(), message)
                        return
                    else:
                        self.step = 4
                        self._snd(self.get_str_form_wave(), '')
                        return

                if self.step==4 or self.step == 6:
                    self.step=3
                    self._snd(self.get_str_form_wave(), '')
                    return



                if self.step ==8:
                     if one_unit:
                        message='No procede'
                        self._snd(self.get_str_form_wave(), message)
                        return
                     else:
                        self.step = 9
                        self._snd(self.get_str_form_wave(), '')
                        return

                if self.step ==9:
                    if one_unit:
                        message='No procede'
                        self._snd(self.get_str_form_wave(), message)
                        return
                    else:
                        self.step = 8
                        self._snd(self.get_str_form_wave(), '')
                        return

        if wave_['PROCESADO']:
            message = u'\nYa está procesada'
            self._snd(self.get_str_form_wave(), message)
            return


        if line_float or line_float== 0:
            line_=line_float
            print u"Step: %s, Coef Var: %s"%(self.step, self.product['is_var_coeff'])

            one_unit =  (wave_['uom_id'] == wave_['uos_id'])

            if self.step==2:
                self.step = 3

            if self.step in [3,4]:

                if line_float>0:
                    self.qty_calc.append(line_float)
                else:
                    try:
                        self.qty_calc.remove(line_float*-1)
                    except:
                        res = False

                cal_qty=0
                for qty in self.qty_calc:
                        cal_qty+=qty
                len_qty= len(self.qty_calc)

                if self.step ==3:
                    if self.product['is_var_coeff']:
                        self.new_uom_qty = len_qty
                    else:
                        self.new_uom_qty = round(cal_qty / self.fc, 2)
                    self.new_uos_qty = cal_qty

                if self.step ==4:
                    if self.product['is_var_coeff']:
                        self.new_uos_qty = len_qty
                    else:
                        self.new_uos_qty = round(cal_qty * self.fc, 2)
                    self.new_uom_qty = cal_qty

                self._snd(self.get_str_form_wave(), '')
                return

            if self.step==5:
                self.new_uom_qty = line_float
                self.step=5
                self._snd(self.get_str_form_wave(), '')
                return

            if self.step==6:
                self.new_uos_qty = line_float
                self.step=6
                self._snd(self.get_str_form_wave(), '')
                return


            if self.step == 8:
                self.new_uom_qty = line_float
                self.new_uos_qty = round(line_float * self.fc, 2)
                self._snd(self.get_str_form_wave(), '')
                return

            if self.step == 9:

                self.new_uos_qty = line_float
                self.new_uom_qty = round(line_float / self.fc, 2)
                self._snd(self.get_str_form_wave(), '')
                return


        #si llega aqui, vuelve-.
        message ="\nNo te entiendo"
        self._snd(self.get_str_form_wave(), message)
        return

    def get_str_form_wave(self):

         #if not wave_:
            #self.waves = self.factory.odoo_con.get_wave_reports_from_task(self.task_id, self.type)
            #No puedo poner visited ya que es al vuelo. no puedo modificarlo en la db
        self.last = "get_str_form_wave"
        wave_=self.waves[str(self.active_wave)]
        #self.product = self.factory.odoo_con.get_product_gun_complete_info(self.user_id, wave_['product_id'])
        #Esta cabecera es común a rdos los estados
        header = u"%s\n"%wave_['name']
        menu_str = ''
        if wave_['customer_id']:
            menu_str = u"[%s] %s\n"%(wave_['ref'], wave_['customer_id'])
        str_ = (u'%s - ')%(wave_['package'])
        if self.step in [0] and not wave_['PROCESADO']:
            menu_str+= self.inverse(str_)
        else:
            menu_str += str_

        menu_str += u"(%s)\n%s\n"%(wave_['lot'], wave_['product'])
        menu_str += u"Stock: %s %s\n"%(wave_['qty_available'], wave_['uom'])
        menu_str += u"Mover: %s %s\n"%(wave_['uos_qty'],wave_['uos'])

        if wave_['is_package']:
            menu_str+=u"       (Paquete Completo)\n"
        #FIN CABECERA

        cantidad=''
        cantidad_uos =''
        message =''

        if wave_['uom'] == wave_['uos']:
            one_unit = True
        else:
            one_unit= False

        if self.step <= 2:
            cantidad_uos += ''#u"Mover %s %s\n"%(wave_['uos_qty'],wave_['uos'])
            cantidad =''#cantidad += u"(%s %s) "%(wave_['uom_qty'],wave_['uom'])

        #SI CONFIRMAMOS TODO TAL COMO VIENE
        if self.step ==2:
            message += u"%s o cantidad en %s\n"%(KEY_CONFIRM, wave_['uos'])
            message = self.inverse(message)

        uom = wave_['uom']
        uos = wave_['uos']
        uom_qty = wave_['uom_qty']
        uos_qty = wave_['uos_qty']

        cantidad_uom_full= u'%s %s\n'%(self.new_uom_qty, wave_['uom'])
        cantidad_2uos_full = u'(%s) %s %s\n'%(str(wave_['uos_qty']),self.new_uos_qty,  wave_['uos'])

        cantidad_2uos = (len(str(wave_['qty'])) * " ") + u'%s %s %s\n'%(str(wave_['uos_qty']),self.new_uos_qty,  wave_['uos'])
        cantidad_uom = (len(str(wave_['uos_qty'])) * " ") + u'%s %s\n'%(self.new_uom_qty, wave_['uom'])

        #AÑADIMOS PARA STEP=3, PESO VARIABLE. INTRO EN UOS

        if self.step == 4 or self.step == 5 or self.step == 9:
            #AQUI INTRODUCIMOS EN UOM
            #cantidad += '(%s) %s %s\n'%(wave_['CANTIDAD'], self.new_uom_qty, wave_['uom'])
            #cantidad_uos += '(len(str(wave_['qty'])) * " ") + %s %s\n'%(str(wave_['uos_qty']),self.new_uos_qty,  wave_['uos'])
            #cantidad += (len(str(wave_['uos_qty'])) * " ") + '%s %s\n'%(wave_['uom_qty'], self.new_uom_qty, wave_['uom'])
            #cantidad_uos += '(%s) %s %s\n'%(str(wave_['uos_qty']),self.new_uos_qty,  wave_['uos'])
            if one_unit:
                cantidad = u'(%s) '%uos_qty
                cantidad_uos = self.inverse(u'%s %s\n'%(self.new_uom_qty, self.inverse(uom)))
            else:
                cantidad = u''#(%s) '%uos_qty
                cantidad_uos = u'Actual: %s %s\n%s%s\n'%(self.new_uos_qty, uos, " "*8 , self.inverse(u'%s %s'%(self.new_uom_qty, self.inverse(uom))))

            message = u"%s o cantidad en %s"%(KEY_CONFIRM, wave_['uom'])

        #PESO VARIABLE INTRO EN UOM
        if self.step == 3 or self.step==6 or self.step ==8:
            #no deberçia usarse
            cantidad += u''
            if one_unit:
                cantidad_uos = u'Actual: %s\n'%self.inverse(u'%s %s'%(self.new_uos_qty, uos))
            else:
                cantidad_uos = u'Actual: %s\n%s%s %s\n'%(self.inverse(u'%s %s'%(self.new_uos_qty, uos)), " "*8 , self.new_uom_qty, uom)#, " "*8 , self.new_uom_qty, uom)
            message = u"%s o intro %s"%(KEY_CONFIRM, wave_['uos'])

        if self.step == 5 and False:
            if one_unit:
                message = u"%s OK uom o intro %s\n"%(KEY_CONFIRM, wave_['uom'])
            else:
                cantidad = u''#(%s) '%uos_qty
                cantidad_uos = u'Actual: %s\n%s%s %s\n'%(self.inverse(u'%s %s'%(self.new_uos_qty, uos)), " " *8, self.new_uom_qty, uom)
            message = u"%s o cantidad en %s"%(KEY_CONFIRM, wave_['uos'])

        if self.step == 6 and False:
            #no deberçia usarse
            cantidad += cantidad_uom
            cantidad_uos += cantidad_2uos_full
            cantidad = self.inverse(cantidad)
            message = "%s Ok Uom, o intro nuevo\n"%(KEY_CONFIRM)


        if self.step == 8 and False:
            #Aqui es peso fijo one unit, introducimos cantidad para uom o one_unit
            cantidad = u''#(%s) '%uos_qty
            cantidad_uos = u'Actual: %s\n'%self.inverse(u'%s %s'%(self.new_uom_qty, uom))
            message = u'Cantidad en %s\n'%wave_['uom']

        if self.step == 9 and False:
            #peso fijo, 2 unidades
            cantidad = u''
            if one_unit:
                cantidad_uos = u'Actual: %s\n'%self.inverse(u'%s %s'%(self.new_uos_qty, uos))
            else:
                cantidad_uos = u'Actual: %s\n%s%s %s\n'%(self.inverse(u'%s %s'%(self.new_uos_qty, uos)), 8*" " , self.new_uom_qty, uom)
            message = u'Cantidad en %s\n'%wave_['uos']

        if self.step == 10:
            cantidad = u''#(%s) '%uos_qty
            if wave_['is_var_coeff']:
                if one_unit:
                    cantidad_uos = u'Actual: %s %s\n'%(self.new_uos_qty, uos)
                else:
                    cantidad_uos = u'Actual: %s %s\n%s%s %s\n'%(self.new_uos_qty, uos, 8*" " , self.new_uom_qty, uom)
            else:
                if one_unit:
                    cantidad_uos = u'Actual: %s %s\n'%(self.new_uos_qty, uos)
                else:
                    cantidad_uos = u'Actual: %s %s\n%s%s %s\n'%(self.new_uos_qty, uos, 8*" " , self.new_uom_qty, uom)


            message =u"%s Confirmar Operación\n"%KEY_CONFIRM
            message = self.inverse(message)

        if wave_['uom'] == wave_['uos']:
            menu_str += cantidad_uos
        else:
            menu_str += cantidad + cantidad_uos

        str_ = u'De %s\n'%(wave_['origen_bcd'])
        # com oe s picking no hay destino str_ = 'A %s\n'%wave_['DESTINO']
        if self.step in [1]:
            menu_str+= self.inverse(str_)
        else:
            menu_str += str_
        str_ = ''



        if wave_['PROCESADO']:
            str_= self.inverse(u"[x] %s Cancel Op\n"%KEY_CANCEL)

        menu_str += str_
        keys =''

        if self.step < 10 and self.step>2 and len(self.qty_calc)>1:
            h = False
            qtys_=''
            for qty in self.qty_calc:
                h=True
                qtys_ += u'[%s]'%qty
            if h:
                 menu_str += qtys_ +u'\n'

        if self.step in [2,3,4,5,6] and not one_unit:
            keys += u'\n%s Cambiar Unidad'%KEY_QTY


        menu_str += message

        #keys += KEY_VOLVER + u' Atrás '  + KEY_WAVE_OPS + u' Ops'
        menu_str = header + menu_str + keys
        return menu_str

    def handle_list_ubi_ops(self, line, confirm=False):
        # Manejador de lista de operaciones de ubicacion
        line = line or '0'
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False


        if line == KEY_CANCEL:
            res = self.factory.odoo_con.gun_cancel_task(self.user_id, self.task_id)
            self.check_task()
            self.active_task = self.get_active_task()
            if res==True:
                self.state ='tasks'
                message = u'Tarea cancelada\n'
                self._snd(self.get_str_menu_task(), message)
                return
            else:
                self.state ='tasks'
                message = u'Error al cancelar (ERP)\n'
                self._snd(self.get_str_menu_task(), message)
                return

        if line == KEY_PAUSE:
            aux = self.task_id
            pause = not self.tasks[self.active_task]['paused']
            res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                            self.tasks[self.active_task]['id'],
                                                            pause)
            self.check_task()
            self.task_id = aux
            self.active_task = self.get_active_task()
            self._snd(self.get_str_list_ops())
            return


        if line == KEY_VOLVER:
            self.last_state = self.state
            self.state = "tasks"
            self.reset_vals()
            self._snd(self.get_str_menu_task())
            return

        if line ==KEY_PRINT:
            print_ids=[]
            inc = 0
            for op_ in self.ops:
                inc+=1
                package_id = self.ops[op_]['pack_id']
                print_ids.append[inc]({
                    'id': package_id,
                    'name':self.ops[op_]['paquete']
                })
            self.last_state = self.state
            self.packs= print_ids
            self.state = 'print_tags'
            self._snd(self.get_str_print_tags())
            return


        if self.ops and not order_line:
            if line == KEY_CONFIRM:
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM, confirm=False)
                return
            #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM <=len(self.ops):
                    self.num_order_list_ops += MAX_NUM
                self._snd(self.get_str_list_ops())
                return
            if line == KEY_PREV:
                self.num_order_list_ops -= MAX_NUM
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self._snd(self.get_str_list_ops())
                return
            #Selección de un formulario de op
            if line in self.ops.keys():
                self.step=0
                self.state = 'form_ops'
                self.handle_form_ubi_ops(u"%s"%line)
                return
            # if line =='0':
            #     self.handle_list_ubi_ops(u"%s%s"%(PRE_PACK,self.ops['1']['pack_id']))
            #     return

            message =u"\nNo te entiendo"
            self._snd(self.get_str_list_ops(), message)
            return

        if order_line == PRE_PACK :
            if self.ops:
                for op_ in self.ops:
                    op = self.ops[op_]
                    if op['paquete'] == line or op['pack_id'] == self.int_(line):
                        self.last_state = "list_ops"
                        self.active_op = self.int_(op_)
                        self.op_id = op['ID']
                        self.state = 'form_ops'
                        self.step=2
                        self.handle_form_ubi_ops(order_line+line)
                        return
            #SI NO ESTA SE AÑADE (si se puede)
            pack_id = self.int_(line)
            op_id, message = self.factory.odoo_con.add_loc_operation_from_gun(self.user_id, self.task_id, pack_id)
            #to_process a False
            if op_id:
                res = self.factory.odoo_con.change_op_value(self.user_id, op_id, 'to_process', False)
                self.check_task()
                self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
                self.active_op = len(self.ops)
                self.op_id = op_id

                message = self.inverse(u'Operación creada\n para el paquete')
            else:
                message = self.inverse(u'Paquete No existe')
            self._snd(self.get_str_list_ops(), message)
            return

    def get_str_form_ops(self):
        self.last = "get_str_form_ops"
        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
        num_ops = len(self.ops)
        op_=self.ops[str(self.active_op)]
        self.op_id = op_['ID']

        if op_['VISITED'] == False:
            op_['VISITED'] =True
            res = self.factory.odoo_con.change_op_value(self.user_id, self.op_id, 'visited', True)

        not_vis = 0
        not_proc = 0
        for op in self.ops:
            op__=self.ops[op]
            if op__['VISITED']:
                not_vis += 1
            if op__['PROCESADO']:
                not_proc += 1


        if op_['PROCESADO']:
            self.vals["paquete"]=op_['package']
            self.vals["destino"]=op_['DESTINO']

        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")

        header = "Tarea: %s OP: %s\nNo vistas %s Ok %s\n"\
                 %(self.tasks[self.active_task]['ref'],
                   str(self.op_id), str(num_ops-not_vis), str(not_proc))
        header = u"%s: Faltan %s de %s\n" \
                 u""%(self.tasks[self.active_task]['ref'], num_ops-not_proc , num_ops)
        if self.tasks[self.active_task]['paused'] == True:
            header = self.inverse(header)

        # header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
        #          + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "*"*25+"\n"
        strg = header
        strg += u"%s\n"%op_['product']

        strg_ = u'%s %s:%s\n'%(op_['package'], self.show_id*str(op_['pack_id']), op_['lot'])
        if (self.step == 0 or self.step ==1) and not op_['PROCESADO']:
            strg +=self.inverse(strg_)
        else:
            strg += strg_



        if not op_['CANTIDAD']==1:
            strg += u"%s %s\n"%(op_['CANTIDAD'], op_['uom'])

        #aqui pongo cantidades informativas
        strg+=u"Mover: %s %s\n"%(op_['packed_qty'], op_['uom'])

        if op_['is_package']:
            strg+=u"       (Paquete Completo)\n"

        if op_['uom_id']!=op_['uos_id']:
            strg+="%s%s %s\n"%(' ' * 7, op_['uos_qty'], op_['uos'])

        if self.type != 'ubication':
            strg_= u'De: %s %s\n'%(op_['origen_bcd'], str(op_['origen_id'])* self.show_id)
            if self.step ==0 and not op_['PROCESADO'] :
                strg += self.inverse(strg_)
            else:
                strg +=  strg_

        if self.type != 'picking':
            strg_= u'A: %s %s\n'%(op_['destino_bcd'], str(op_['destino_id'])* self.show_id)
            if (self.step==2 or self.step ==3) and not op_['PROCESADO']:

                strg += self.inverse(strg_)
                op_ok = False
            else:
                strg +=strg_

        if op_['PROCESADO']:
            strg += self.inverse(u"[x] %s Cancel Op\n"%KEY_CANCEL)

        keys = ""
        keys += u"%s Atrás"%KEY_VOLVER
        if self.show_keys:
            strg += keys
        return strg

    def handle_form_ubi_ops(self, line, confirm=False):
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)
        active_op =str(self.active_op)
        if line == KEY_VOLVER:

            if self.last_state == 'list_ops':
                self.state = 'list_ops'
                self.reset_vals()
                self.step =0
                self._snd(self.get_str_list_ops())
                return
            self.last_state = self.state
            self.state = "tasks"
            self.reset_vals()
            self.step =0
            self._snd(self.get_str_menu_task())
            return

        #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
        if line == KEY_NEXT:

            num_ops = len(self.ops)
            self.active_op +=1
            if self.active_op > num_ops:
                self.active_op = 1
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        if line == KEY_PREV:
            self.active_op -=1
            if self.active_op <= 0:
                self.active_op = len(self.ops)
            self.reset_vals()
            self.step =0
            self.get_views(line)
            return

        #Si la tarea esta pausada, no pasa de aquí
        if self.tasks[self.active_task]['paused'] == True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_ops(), ERROR_TAREA_EN_PAUSA)
            return

        #Si la operación está procesada, solo permito Cancelar el Proceso
        if line == KEY_CANCEL and self.step <3:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
            self.reset_vals()
            self.step =0
            self._snd(self.get_str_form_ops())
            return

        #Si está procesada, no pasa de este if
        if self.ops[active_op]['PROCESADO']== True and not line in self.ops.keys():
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_ops() + u'\nOp Procesada')
            return

        if self.step == 2:
            if order_line == PRE_LOC:
                #Lo que leo es una ubicación
                #Si lo que leo es la ubicación que me da la tarea, perfecto paso a step 10
                #miramos si tiene hijas
                #new_loc = self.factory.odoo_con.get_location_gun_info(self.user_id, line_int)
                child_ids = self.factory.odoo_con.get_location_id_childs(self.user_id,line_int)
                if line_int == self.ops[active_op]['destino_id'] or \
                                line_int == self.factory.odoo_con.get_parent_location_id(self.user_id, self.ops[active_op]['destino_id']):

                    self.vals['destino'] = str(self.ops[active_op]['destino_id'])
                    self.vals['nuevo_destino'] = self.vals['destino']
                    self.step = 10
                    if self.confirm_last_step:
                        message =u"\nConfirma Operación\n%s Si %s N0\n" %(KEY_YES, KEY_CANCEL)
                        self._snd(self.get_str_form_ops() + message)
                    else:
                        self.handle_form_ubi_ops(line=KEY_YES)
                    return

                else:
                    #miramos si es una localización o
                    #caso 1 no es multiubi
                    new_loc = self.factory.odoo_con.get_location_gun_info(self.user_id, line_int)
                    if new_loc['exist'] and \
                        self.factory.odoo_con.is_location_free(self.user_id, line_int):

                        if child_ids == []: #no hay sub
                            self.step = 5
                            self.vals['nuevo_destino']= line_int
                            message =self.inverse(u"\nA : %s"%new_loc['bcd_name']) +\
                                     u"\n%s Si %s No"%(KEY_YES, KEY_CANCEL)
                            self._snd(self.get_str_form_ops() + message)
                            self.subzones = False
                            return

                        else:#tienes sub y hay que seleccionarlas

                            message = u'\n' * 20 + u'Selecciona subicación\n'
                            self.subzones = new_loc['childs']
                            inc=0
                            for x in self.subzones:
                                inc +=1
                                message += u'%s > %s\n'%(inc, x['bcd_name'])
                            self.step = 3
                            message =u"[0 - %s]"%inc
                            self._snd(self.get_str_form_ops() + message)
                            return
            # self.step=1
            # message =u"\nError. Escanea Ubicación"
            # self._snd(self.get_str_form_ops() + message)
            # return

        if self.step==3 and line_int>0 and line_int<=len(self.subzones):
            self.vals['nuevo_destino']= self.subzones[line_int]['id']
            self.step = 5
            message =u"\nNuevo A: %s \n%s Si %s No\n"%(self.subzones[line_int]['bcd_name'], KEY_YES, KEY_VOLVER)
            self._snd(self.get_str_form_ops() + message)
            return

        if self.step == 5:
            if line ==KEY_YES:

                self.ops[active_op]['destino_id'] = self.vals['nuevo_destino']
                vals = {'to_procces' : True, 'location_dest_id': self.vals['nuevo_destino']}
                res = self.factory.odoo_con.change_op_values(self.user_id, self.op_id, vals)
                new_loc = self.factory.odoo_con.get_location_gun_info(self.user_id, self.vals['nuevo_destino'])
                self.ops[active_op]['destino_bcd'] = new_loc['bcd_name']
                if new_loc['zone']=='picking':
                    #preguntamos si quiere asignarlo a la zona de picking
                    message = self.inverse(u"\nAsignar zona a producto") + u"\n%s Si %s No"%(KEY_YES, KEY_CANCEL)
                    self.step = 6
                    self._snd(self.get_str_form_ops() + message)
                    return
                else:
                    self.vals['destino'] = str(self.ops[active_op]['destino_id'])
                    self.vals['nuevo_destino'] = self.vals['destino']

                    self.step = 10
                    if self.confirm_last_step:
                        message =self.ivnerse(u"\nConfirma Operación") + "\n%s Si %s N0\n" %(KEY_YES, KEY_CANCEL)
                        self._snd(self.get_str_form_ops() + message)
                    else:
                        self.handle_form_ubi_ops(line=KEY_YES)
                    return

        if self.step == 6:
            if line==KEY_YES:
                res = self.factory.odoo_con.check_picking_zone(self.user_id,
                                                               self.ops[active_op]['product_id'],
                                                               self.ops[active_op]['destino_id'],
                                                               True)
                if res:
                    self.handle_form_ubi_ops(line=KEY_CANCEL)
                    return
                else:
                    self.step = 9
                    self.subzones= False
                    message = u'\nError al asignar la zona\n'
                    self._snd(self.get_str_form_ops() + message)
                    return

            if line==KEY_CANCEL:
                self.vals['destino'] = str(self.ops[active_op]['destino_id'])
                self.vals['nuevo_destino'] = self.vals['destino']
                self.step = 10
                if self.confirm_last_step:
                    message =u"\nConfirma Operación\n%s Si %s N0\n" %(KEY_YES, KEY_CANCEL)
                    self._snd(self.get_str_form_ops() + message)
                else:
                    self.handle_form_ubi_ops(line=KEY_YES)
                return

        if line in self.ops.keys() and self.step == 0:
            res=False
            for op_ in self.ops:
                op = self.ops[op_]
                if op['paquete'] == self.ops[line]['paquete']:
                    self.last_state = "list_ops"
                    self.active_op = self.int_(op_)
                    self.op_id = op['ID']
                    res= True

            if res:
                self.state = 'form_ops'
                self.step=0
                message =u"\nEscanea Paquete"
                self._snd(self.get_str_form_ops() + message)
                return


        #paso 0 solo permito introducit Paquete
        if self.step == 0 or self.step==2:
            if order_line == PRE_PACK:
                if line == self.ops[active_op]['package'] or\
                    self.int_(line) == self.ops[active_op]['pack_id']:
                    self.vals ['paquete'] = self.ops[active_op]['pack_id']
                    self.step = 2
                    message =u"\nEscanea Ubicación"
                    try:
                        self._snd(self.get_str_form_ops() + message)
                        return
                    except:
                        ee=1
                        return
                else:
                    self.reset_vals()
                    self.step = 0
                    message = u'\nPaquete no Válido'
                    self._snd(self.get_str_form_ops() + message)
                    return
            else:
                self.step = 0
                message = u'\nOpción no Válida'
                self._snd(self.get_str_form_ops() + message)
                return

        if self.step ==10:
            #si llegamos aquí, tenemos que confirmar
            if line == KEY_YES:
                new_state = True
            else:
                self.step = 0
                message =u"\nCancelado."
                self._snd(self.get_str_form_ops(), message)
                return

            print "Enviando " + str(new_state) + " para id :" +str(self.op_id)
            task_ops_finish = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, new_state)
            self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
            #task_ops_finish es que están todas finalizadas.

            if not task_ops_finish:
                #llamamos a confirmar tarea
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM, confirm=False)
                return
            else:
                self.step = 0
                message = u"\nProcesada OK"
                self.state = 'list_ops'
                self.reset_vals()
                self.step =0
                self._snd(self.get_str_list_ops(), message)

                return
        #Si llega aquí, hay un error no localizado.
        self.reset_all_vals(self.vals)
        self.step = 1
        message = u"\nNo te entiendo"
        self._snd(self.get_str_form_ops(), message)
        return

    def handle_ops_ubi(self, line='0', confirm = False):
        # aqui veremos line en la pantalla de tasks
        #
        print "handle_ops_ubi" + str(line)
        self.op_id = self.ops[str(self.active_op)]['ID']
        message =''

        if confirm == True and (line == KEY_YES or line == KEY_NO):

            if line == KEY_YES:
                new_state = True
            if line == KEY_NO:
                new_state = False
            print "Enviando " + str(new_state) + " para id :" +str(self.op_id)
            task_ops_finish = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, new_state)

            if not task_ops_finish:
                #llamamos a confirmar tarea
                self.last_state= "tasks" #queremos que vuielva a tareas
                self.state = "yes_no"
                self._snd(u"Todas las operaciones OK\nFinalizar Tarea: \n"
                          + u"\nRef: %s"%str(self.task_id)
                          + u"\n%s Si %s Cancelar Tarea"%(KEY_YES,KEY_NO)
                          )
                return True
            else:
                #hay mas operaciones, entonces vamos a la siguiente
                self.handle_ops_ubi(KEY_NEXT)
                return
        print "h_ops_ubi: " + line + "task: " +str(self.task_id) + " > Op: " +str(self.op_id)
        if line == "" or not line:
            line=KEY_NEXT

        # if line not in used_keys:
        #     str_error = u"La opcion %s no es valida.\nReintentar:\n" % line
        #     self._snd(str_error + self.get_str_menu_task())

        if line == KEY_VOLVER:

            self.last_state = self.state
            self.state = "tasks"
            self.reset_vals()
            self._snd(self.get_str_menu_task())
            return

        #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
        elif line == KEY_NEXT:
            num_ops = len(self.ops)
            self.active_op +=1
            if self.active_op > num_ops:
                self.active_op = 1
            self.reset_vals()
            self.get_views(line)

        elif line == KEY_PREV:
            self.active_op -=1
            if self.active_op <= 0:
                self.active_op = len(self.ops)
            self.reset_vals()
            self.get_views(line)
        #CANCELAR UNA OPERACION ES PONER A CERO, to_process y val_ubi

        elif line == KEY_CANCEL:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.reset_vals()

            self._snd(self.get_str_form_ops())
        #Confirmar (solo si está en pause)

        elif line == KEY_CONFIRM:

            if self.tasks[self.active_task]['paused'] == False:
                self.last_state= self.state
                self.state = "yes_no"
                self._snd(u"Confirmar el movimiento : \n"
                          + u"\nPaquete: " + self.vals ['paquete']
                          + u"\nDestino: " + self.vals ['destino']
                          + u"\nSi <" + KEY_YES + u"> NO <" + KEY_NO + ">"
                          )
            else:
                self._snd(self.get_str_form_ops(), ERROR_TAREA_EN_PAUSA)

        elif line == KEY_DESTINO:
            self.menu_intro_destino
        elif line == KEY_QTY:
            self.menu_intro_qty
        elif line == KEY_ORIGEN:
            self.menu_intro_orien

        else:
            #si no está en pausa ni procesado podemos introduir paquete y destino
            if self.tasks[self.active_task]['paused'] == False and self.ops[str(self.active_op)]['PROCESADO']!= True:
                if line == str(self.ops[str(self.active_op)]['pack_id']) and (self.vals['paquete']==False):
                    #ACABA DE INTRODUCIR PAQUETE
                    self.vals ['paquete'] = line
                    message =u"Escanea Ubicación"
                elif (line == str(self.ops[str(self.active_op)]['destino_id']) or line == self.loc_id) \
                        and (self.vals['paquete']!=False):
                    #ACABA DE INTRODUCIR DESTINO
                    self.vals ['destino'] = line
                    if self.loc_id:
                        #tenemos que cambiarlo en la operacion
                        res = self.factory.odoo_con.change_packet_op(self.user_id, self.op_id, 'location_dest_id', self.int_(line))
                        self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id, self.type)
                        self.handle_ops_ubi(KEY_YES, True)
                        res = self.check_task()
                    self.loc_id = False
                    #me salto la pantalla de confirmación
                    if self.vals['paquete'] != False:
                        self.handle_ops_ubi(KEY_YES, True)
                elif self.int_(line) in self.factory.odoo_con.get_locations_ids() and (self.vals['paquete']!=False):
                    self.loc_id = line
                    message =u"Confirma Ubicación\a"
                else:
                    message = u"No te entiendo\a"

                self._snd(self.get_str_form_ops(), message)
                return
            else:
                message = u"En Pausa/Procesada"
                self._snd(self.get_str_form_ops(), message)
                return

        #self._snd(self.get_str_form_ops())

    def get_str_products_by_zone(self, location_id):
        """
        Devuelve el menú con las cámaras disponibles
        """
        delimiter = "\n********************\n"
        #str_menu = "0 -> Volver\n"
        str_menu=""
        self.products = self.factory.odoo_con.get_product_by_picking_location(self.user_id, location_id)

        inc=1
        if self.products:
            for key in self.products:
                key_ = int(key)
                if key_>= self.num_order_list_ops and key_<= self.num_order_list_ops + MAX_NUM_ONE:
                    str_menu += str(key) + " -> " + self.products[1] + "\n"
        else:
            str_menu +=u"\nNo hay Productos\n"
        keys = u"%s Volver"%KEY_VOLVER
        str_menu += delimiter + keys
        return str_menu

    def handle_products_by_zone(self, line):
        print "handle_products_by_zone" + str(line)

        if line== KEY_VOLVER:
            self.state = "menu1"
            self.machine_id = False
            self.route = False
            self.route_id = False
            self._snd(self.get_str_menu1())
            return

        if line == KEY_NEXT:
            if len(self.products)>self.num_order_list_ops:
                self.num_order_list_ops +=MAX_NUM_ONE
            self._snd(self.get_str_products_by_zone())
            return

        if line == KEY_PREV:
            self.num_order_list_ops -=MAX_NUM_ONE
            if self.num_order_list_ops <1:
                self.num_order_list_ops ==1
            self._snd(self.get_str_products_by_zone())
            return


        if self.routes:
            str_keys = [str(x) for x in self.products.keys()]
            str_keys.append([0])
            if line not in str_keys:
                str_error = u"La opcion %s no es valida.\nReintentar\n" % line
                self._snd(str_error + self.get_str_products_by_zone())
                return
            else:

                self.camera_ids=[]
                self.route_id = self.routes[(line)][0]
                self.route = self.routes[(line)][1]
                self.state = "picking"
                self._snd(self.get_cameras_menu(type = 'picking'))
                return

        self.route = ""
        self.route_id = False
        self._snd(self.get_str_products_by_zone(), u'No válido\n')
        return


    def get_manual_transfer_packet(self):
        #Menu de opciones de movimiento manual
        #cuando se escanea un EAN
        self.state="manual_transfer_packet"
        print "get manual menu:"
        header = u"Mov. Manual (Paquete):\n"
        delimiter = u"********************\n"
        menu_str = header

        if self.do_pack:
            do_pack ='x'
        else:
            do_pack =' '

        if self.step == 0:
            menu_str =self.inverse(u"Scan Paquete para mover"
                                   u"\nUbicación para reposición")


        if self.step>0:
                menu_str+=u'%s\n%s - %s\n'%(self.vals['product'], self.vals['package'], self.vals['lot'])
                menu_str += u'Cantidad: %s %s\nDe: %s'%(self.vals['packed_qty'], self.vals['uom'], self.vals['src_location_bcd'])

        if self.step ==1:
             menu_str += self.inverse(u'\nOpcion o Scan paquete')




        if self.step == 5:
            #ya tenemos pakete
            menu_str += self.inverse(u'\nScan Destino o Cantidad')

        if self.step>5:
             menu_str += u'\nA : %s'%self.loc['dest_bcd_name']

        if self.step >=5 and self.new_uom_qty>0:
            menu_str += u'\nMover: % s %s'%(self.new_uom_qty, self.vals['uom'])

        # if self.step==8:
        #     #Ya tenemos destino
        #     menu_str+= u'\n[%s] Fusionar Paquete (%s)\n'%(do_pack, KEY_DO_PACK)
        #     menu_str += self.inverse(u'\nOpción [1,2] o %s Mover\n'%KEY_CONFIRM)

        if self.step==10 or self.step == 8:
            #Ya tenemos destino
            menu_str+= u'\n[%s] Fusionar Paquete (%s)\n'%(do_pack, KEY_DO_PACK)
            menu_str += self.inverse(u'\n%s Mover'%KEY_CONFIRM)

        keys = u"\n%s Atrás %s Cancelar"%(KEY_VOLVER, KEY_CANCEL)
        if self.show_keys:
            menu_str +=keys

        return menu_str

    def handle_manual_transfer_packet(self, line, confirm=False):
        #menu eventos en manual
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        message =''
        line_int = self.int_(line)
        if order_line==PRE_LOC and self.step==0:
            self.state="manual_picking_reposition"
            self.step=0
            self.handle_manual_picking_reposition(PRE_LOC + line)
            return

        if line == KEY_DO_PACK:
            self.do_pack= not self.do_pack
            if self.do_pack:
                self.pack_type = 'do_pack'
            else:
                self.pack_type = 'no_pack'
            self._snd(self.get_manual_transfer_packet())
            return

        if line == KEY_VOLVER:
            if self.step==0:
                self.state="menu1"
                self._snd(self.get_str_menu1())
                return
            if self.step==5:
                self.vals = []
                self.step = 0
                self._snd(self.get_manual_transfer_packet())
                return
            if self.step==8:
                self.move={}
                self.loc={}
                self.step = 5
                self._snd(self.get_manual_transfer_packet())
                return
            if self.step==10:
                self.step = 8
                self._snd(self.get_manual_transfer_packet())
                return
        if line == KEY_CANCEL:
            self.vals={}
            if self.step==0:
                self.state="menu1"
                self._snd(self.get_str_menu1())
                return
            else:
                self.vals={}
                self.step = 0
                self._snd(self.get_manual_transfer_packet())
                return
        #Si en ccualquier momento meto un opaquete reinicio la operación
        if order_line == PRE_PACK:

            self.pack_type ='do_pack'
            package_id = line_int
            self.vals={}
            self.vals = self.factory.odoo_con.get_pack_gun_info(self.user_id, package_id)
            busy = self.factory.odoo_con.get_user_packet_busy(self.user_id, package_id)
            self.new_uom_qty = 0
            if self.vals['exist'] == False:
                message = u"\nNo encuentro el paquete"
                self.step=0
                self._snd(self.get_manual_transfer_packet(), message)
                return
            else:
                if not busy == False and not confirm:
                    self.step=0
                    self.loc={}
                    message = self.inverse(u"%s (%s)\nContinuar %s"%(busy['ref'], busy['user'], KEY_YES))
                    self._snd(self.get_manual_transfer_packet(), message)
                    return

                else:
                    self.step =5
                    self.loc={}
                    self._snd(self.get_manual_transfer_packet(), message)
                    return

        if self.step==5 and self.float_(line) and not order_line:
            #introdujo un acantidad
            self.new_uom_qty = self.float_(line)
            self._snd(self.get_manual_transfer_packet(), message)
            return

        if self.step==5  and order_line == PRE_LOC:
            self.loc={}
            self.loc =  self.factory.odoo_con.get_location_gun_info(self.user_id, location_id = line, type = 'dest_')
            #es una localización
            if self.loc['exist']:
                if self.vals['src_location_id']==self.loc['dest_location_id']:
                    message=u'Error: De = A'
                    self._snd(self.get_manual_transfer_packet(), message)
                    return

                if self.loc['childs']:
                    #es un loc padre ... hay que seleccionar
                    #self.step=11
                    self.last_read = line_int
                    self.subzones = False
                    self.last_state= self.state
                    self.state ='select_subzone'
                    self.selected_subzone = False
                    self.menu_anterior = 'get_str_manual_transfer_packet'
                    self._snd(self.get_str_select_picking_subzone(line_int))
                    return

                if self.loc['usage']!='internal':
                    message = u"Seguro (No es interno)"
                self.step=8
                self._snd(self.get_manual_transfer_packet(), message)
                return
            else:
                message = u"No encuentro este destino"
                self._snd(self.get_manual_transfer_packet(), message)
                return

        if self.step ==8:
            if line in ['1','2']:
                if line =='1':
                    self.pack_type = 'do_pack'
                if line=='2':
                    self.pack_type = 'no_pack'
                self._snd(self.get_manual_transfer_packet(), message)
                return

            elif line == KEY_CONFIRM:
                self.step=10
                self.handle_manual_transfer_packet(line=KEY_CONFIRM)
                return


        if self.step == 10 and line ==KEY_CONFIRM:
            self.move = {}
            k=str(self.active_task)
            package_=False
            if self.vals['packed_qty']==self.new_uom_qty or self.new_uom_qty==0:
                package_ = True
            self.move = {
                'product_id': self.vals['product_id'],
                'package_id': self.vals['package_id'],
                'quantity': self.new_uom_qty,
                'src_location_id': self.vals['src_location_id'],
                'dest_location_id': self.loc['dest_location_id'],
                'do_pack':self.pack_type,
                'lot_id': self.vals['lot_id'],
                'user_id': self.user_id,
                'package': package_#self.vals['packed_qty']==self.new_uom_qty,
            }

            try:
                if self.new_uom_qty == 0 or self.new_uom_qty == self.vals['packed_qty']:
                    #Si la cantidad es la misma que el paquete, entonces product_id=False
                    self.move['product_id'] = False
                pack_destino = self.factory.odoo_con.get_package_of_lot_from_gun(self.user_id, self.move['dest_location_id'],self.move['lot_id'])
                res = self.factory.odoo_con.do_manual_transfer_from_gun(self.user_id, self.move)
                tag=[]
                for op in res:
                    message, print_tag = self.get_tags_message(op['do_pack'], pack_destino, op['product_id'])
                    if print_tag:
                        tag.append(op['result_package_id'])
                if tag:
                    res = self.factory.odoo_con.print_from_gun(self.user_id, tag)

            except Exception, e:
                str_error = u"Error"
                print (str_error + e.message)
                message = str_error + e.message
                self._snd(self.get_manual_transfer_packet(), message)
                return
            print "SE movio"
            self.vals={}
            self.loc={}
            self.move={}
            self.step = 0
            self._snd(self.get_manual_transfer_packet(), message)
            return True

        message = "\nNo te entiendo"
        self._snd(self.get_manual_transfer_packet(), message)
        return


    #DEPRECATED
    def get_manual_transfer_product(self):

        #Menu de opciones de movimiento manual
        #cuando se escanea un EAN
        self.state="manual_transfer_product"
        print "get manual menu:"

        packet=[]
        active_pack=str(self.active_task)
        if self.active_task and self.step>0:
            packet=self.vals['packets'][active_pack]
            ind = active_pack

        if self.pack_type=='do_pack':
            do_pack ='x'
            no_pack = ' '
        else:
            do_pack =' '
            no_pack = 'x'

        header = u"Mov. Manual (Producto):\n"
        delimiter = u"********************\n"
        menu_str = header
        if self.step == 0:
            menu_str =self.inverse(u"Introduce EAN\n")
        else:
            menu_str+=u'%s > %s %s\n\n'%(self.vals['product'], self.vals['virtual_available'], self.vals['uom'])
        if self.step ==1:
            ind = 0
            for k_ in self.vals['packets']:
                ind += 1
                k= self.vals['packets'][str(ind)]
                menu_str += u'%s> %s : %s %s \n  >>%s\n'%(self.inverse(str(ind)), k['package'] ,k['packed_qty'], k['uom'], k['location'])
            menu_str += self.inverse(u'\nOpcion o Scan Packet\n')

        if self.step == 4:
            #ya tenemos paqueete
            menu_str += u'%s : %s\n'%(packet['package'] ,packet['lot'])
            menu_str += u'%s %s (%s %s)\n'%(packet['packed_qty'], packet['uom'], packet['uos_qty'], packet['uos'])
            menu_str += u'De: %s\n'%packet['location']
            menu_str += self.inverse(u'\nIntroduce cantidad a mover\n')

        if self.step==6:
            #ya tenemos cantidad
            menu_str += u'%s : %s\n'%(packet['package'] ,packet['lot'])
            menu_str += u'%s %s (%s %s)\n'%(packet['packed_qty'], packet['uom'], packet['uos_qty'], packet['uos'])
            menu_str += u'De: %s\n'%packet['location']
            menu_str += u'Cantidad a Mover:\n(Max %s) %s %s'%(packet['packed_qty'], self.new_uom_qty, packet['uom'])
            menu_str += self.inverse(u'\nIntro Destino\n')

        if self.step==8:
            #Ya tenemos destino
            menu_str += u'%s : %s\n'%(packet['package'] ,packet['lot'])
            menu_str += u'%s %s (%s %s)\n'%(packet['packed_qty'], packet['uom'], packet['uos_qty'], packet['uos'])
            menu_str += u'De: %s\n'%packet['location']
            menu_str += u'(Max %s) %s %s\n'%(packet['packed_qty'], self.new_uom_qty, packet['uom'])
            menu_str += u'A: %s \n'%self.loc['dest_location']
            menu_str+= u'[%s] 1> Fusionar Paquete\n[%s] 2> Separar Paquete\n'%(do_pack, no_pack)
            menu_str += self.inverse(u'\nOpción o %s Mover\n'%KEY_CONFIRM)

        if self.step==10:
            #Ya tenemos destino
            menu_str += u'%s : %s\n'%(packet['package'] ,packet['lot'])
            menu_str += u'%s %s (%s %s)\n'%(packet['packed_qty'], packet['uom'], packet['uos_qty'], packet['uos'])
            menu_str += u'\nDe: %s\n'%packet['location']
            menu_str += u'(Max %s) %s %s\n'%(packet['packed_qty'], self.new_uom_qty, packet['uom'])
            menu_str += u'A: %s \n'%self.loc['dest_location']
            menu_str+= u'[%s] 1> Fusionar Paquete\n[%s] 2> Separar Paquete\n'%(do_pack, no_pack)
            menu_str += self.inverse(u'\n%s Mover\n'%KEY_CONFIRM)

        keys = u"%s Volver %s Atrás"%(KEY_VOLVER, KEY_CANCEL)
        if self.show_keys:
            menu_str +=keys

        return menu_str
    #DEPRECATED
    def handle_manual_transfer_product(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        message =''
        line_ = self.int_(line)

        if not order_line:
            if line == KEY_VOLVER:
                if self.step==0:
                    self.state="menu1"
                    self._snd(self.get_str_menu1())
                    return
                if self.step==1:
                    self.vals=[]
                    self.step = 0
                    self._snd(self.get_manual_transfer_packet())
                    return
                if self.step==4:
                    self.active_task=False
                    self.step = 1
                    self.loc = {}
                    self._snd(self.get_manual_transfer_product())
                    return
                if self.step==6:
                    self.new_uom_qty=0.0
                    self.step = 4
                    self._snd(self.get_manual_transfer_product())
                    return
                if self.step==8:
                    self.move={}
                    self.step = 6
                    self._snd(self.get_manual_transfer_product())
                    return
                if self.step==10:
                    self.step = 8
                    self._snd(self.get_manual_transfer_product())
                    return
            if line == KEY_CANCEL:
                self.vals={}
                if self.step==0:
                    self.state="menu1"
                    self._snd(self.get_str_menu1())
                    return
                else:
                    self.vals={}
                    self.step = 0
                    self._snd(self.get_manual_transfer_packet())
                    return

            if self.step == 1 and line =='0':
                self.step = 0
                self.vals ={}
                self.state = "manual_transfer_product"
                self.get_manual_transfer_product(line=line)
                return


            if self.step == 1 and line in self.vals['packets'].keys():
                pack = self.vals['packets'][line]
                package_id = pack['package_id']
                self.handle_manual_transfer_product('%s%s'%(PRE_PACK,package_id))
                return

        #Si en ccualquier momento despues de producto
        # meto un opaquete reinicio la operación
        if order_line == PRE_PACK and self.step >= 1:

            new_packet = 0
            new_packet_=False
            package_id= False
            self.pack_type = 'do_pack'
            for packs_ in self.vals['packets']:
                packs=self.vals['packets'][packs_]
                new_packet+=1
                if packs['package_id']==line_:
                    package_id = packs['package_id']
                    self.active_task=new_packet
                    self.new_uom_qty = packs['packed_qty']
                    new_packet_=True
                    break

            if new_packet_:
                self.move={}
                self.loc={}
                if package_id:
                    values = self.factory.odoo_con.get_pack_gun_info(self.user_id, package_id)
                    busy = self.factory.odoo_con.get_user_packet_busy(self.user_id, package_id)

                if values['exist'] == False:
                    message = "\nNo encuentro el paquete"
                    self._snd(self.get_manual_transfer_product(), message)
                    return
                else:
                    #self.package son los quants del packete
                    #self.package = self.factory.odoo_con.get_quant_pack_gun_info(self.user_id, package_id)
                    if False:
                        message = "\nNo encuentro quants para el paquete"
                        self._snd(self.get_manual_transfer_product(), message)
                        return
                    self.step=4
                    if busy:
                        message = "Ocupado en %s\n por \s"%(busy['ref'], busy['user'])
                    self._snd(self.get_manual_transfer_product(), message)
                    return

        if (self.step==4 or self.step==6) and not order_line:
            pack = self.vals['packets'][str(self.active_task)]
            new_qty = self.int_(line) or self.new_uom_qty
            if new_qty > pack['packed_qty']:
                message = u"Debe ser menor que %s %s\n"%(pack['packed_qty'], pack['uom'])
                self._snd(self.get_manual_transfer_product(), message)
                return
            self.new_uom_qty = new_qty
            self.step=6
            self._snd(self.get_manual_transfer_product(), message)
            return

        if (self.step== 6 or self.step ==8) and order_line == PRE_LOC:
            self.loc={}
            self.loc =  self.factory.odoo_con.get_location_gun_info(self.user_id, line, type = 'dest_')
            #es una localización
            if self.loc['exist']:
                if self.loc['usage']!='internal':
                    message = u"Seguro (No es interno)"
                self.step=8
                self._snd(self.get_manual_transfer_product(), message)
                return
            else:
                message = u"No encuentro este destino"
                self._snd(self.get_manual_transfer_product(), message)
                return

        if self.step ==8:
            if not order_line and line in ['1','2']:
                if line =='1':
                    self.pack_type = 'do_pack'
                if line=='2':
                    self.pack_type = 'no_pack'
                self._snd(self.get_manual_transfer_product(), message)
                return

            elif line == KEY_CONFIRM:
                self.step=10
                self.handle_manual_transfer_product(line=KEY_CONFIRM)
                return

        if self.step == 10 and line ==KEY_CONFIRM:
            self.move = {}
            k=str(self.active_task)
            self.step=10
            if self.vals['packets'][k]['packed_qty']!=self.new_uom_qty:
                self.move = {
                    'product_id': self.vals['product_id'],
                    'package_id': self.vals['packets'][k]['package_id'],
                    'quantity': self.new_uom_qty,
                    'src_location_id': self.vals['packets'][k]['location_id'],
                    'dest_location_id': self.loc['dest_location_id'],
                    'do_pack':self.pack_type,
                    'lot_id': self.vals['packets'][k]['lot_id'],
                    'user_id': self.user_id
                }
            else:
                self.move = {
                    'package_id': self.vals['packets'][k]['package_id'],
                    'src_location_id': self.vals['packets'][k]['location_id'],
                    'dest_location_id': self.loc['dest_location_id'],
                    'do_pack':self.pack_type,
                    'user_id': self.user_id,
                    'package':True
                }
            try:
                res = self.factory.odoo_con.s(self.user_id, self.move)
                for op in res:
                    package_to_print = op['result_package_id']
                    self.print_packs([package_to_print])
            except Exception, e:
                str_error = u"Error"
                print (str_error + e.message)
                message = str_error + e.message
                self._snd(self.get_manual_transfer_product(), message)
                return
            print "SE movio"
            self.vals=VALS
            self.loc={}
            self.move={}
            self.step = 0
            message = u"Mov Ok"
            self._snd(self.get_manual_transfer_packet(), message)
            return True

        if line == KEY_CANCEL:
            self.reset_all_vals(self.vals)
            self.vals ={}
            self.step = 0
            self.move={}
            message = u"Cancelado"
            self._snd(self.get_manual_transfer_product(), message)
            return True

        message = "\nNo te entiendo"
        self._snd(self.get_manual_transfer_product(), message)
        return

    def get_manual_picking_reposition(self):

        self.state="manual_picking_reposition"
        print "get manual menu picking reposition:"
        message=''
        header = u"Reposición Manual:\n"
        delimiter = u"********************\n"
        menu_str = header

        if self.step == 0:
            menu_str +=self.inverse(u"Introduce Ubicación\n")
            self.vals={
                    'specific_locations': True,
                    'selected_loc_ids':False,# [self.loc['src_location_id']],
                    'limit': 90,
                    'capacity': 70}

        if self.step>0:
            menu_str+=u'Reposición para :\n%s'%self.loc['src_location']

        menu_capacity = u'\nDesde %% de llenado: %s'%self.vals['capacity']
        menu_limit = u'\nMáx %% de llenado: %s'%self.vals['limit']

        if self.step==1:
            menu_capacity= self.inverse(menu_capacity)
            message= u"\nIntro Desde %%"
        if self.step==2:
            menu_limit= self.inverse(menu_limit)
            message= u"\nIntro Máx %%"
        if self.step>0:
            menu_str+=menu_capacity
            menu_str+=menu_limit
            message += self.inverse(u'\n%s para buscar\n')%KEY_CONFIRM
        # if self.step>0:
        #     message +=self.inverse(u'\n%s Volver ó %s para buscar\n')%(KEY_VOLVER, KEY_CONFIRM)

        keys = u"\n%s Atrás %s Cancelar"%(KEY_VOLVER, KEY_CANCEL)
        if self.show_keys:
            menu_str +=keys
        return menu_str + message

    def handle_manual_picking_reposition(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)
        if line_int<0:
            line_int = 0
        if line_int>100:
            line_int = 100

        if line==KEY_VOLVER:
            if self.step==0:
                self.step=0
                self.state='menu1'
                self._snd(self.get_str_menu1())
                return

            if self.step>0:
                self.step=0

                self.vals={
                    'specific_locations': True,
                    'selected_loc_ids':False,# [self.loc['src_location_id']],
                    'limit': 90,
                    'capacity': 70}
                self.loc={}
                self._snd(self.get_manual_picking_reposition())
                return



        if self.step>=1:
            if line==KEY_CONFIRM:
                new_repo, error = self.factory.odoo_con.create_reposition_from_gun(\
                    self.user_id,self.vals['selected_loc_ids'], self.vals['limit'], self.vals['capacity'])

                if new_repo:
                    self.handle_new_task()
                    return
                else:
                    self.step = 1
                    message= error
                    self._snd(self.get_manual_picking_reposition(), message)
                    return

        if self.step==1 and line_int:
            self.vals['capacity'] = line_int
            self.step=2
            self._snd(self.get_manual_picking_reposition())
            return
        if self.step==2 and line_int:
            self.vals['limit'] = line_int
            self.step=3
            self._snd(self.get_manual_picking_reposition())
            return

        if self.step==0 and order_line== PRE_LOC :
            self.loc={}
            self.loc =  self.factory.odoo_con.get_location_gun_info(self.user_id, line, type = 'src_')
            #es una localización
            if self.loc['exist']:
                if self.loc['zone']!='picking':
                    message = u"No es picking"
                    self.step=0
                    self._snd(self.get_manual_picking_reposition(), message)
                    return
                self.vals={
                    'specific_locations': True,
                    'selected_loc_ids': [self.loc['src_location_id']],
                    'limit': 90,
                    'capacity': 70}
                self.step=1
                self._snd(self.get_manual_picking_reposition())
                return

            else:
                message = u"No encuentro este PICK"
                self._snd(self.get_manual_picking_reposition(), message)
                return

        message = u"No te entiendo"
        self._snd(self.get_manual_picking_reposition(), message)
        return



    def handle_ops(self, line='0', confirm = False):

        type = self.tasks[str(self.active_task)]['type']
        if type == "ubication":
            res = self.handle_ops_ubi(line=line, confirm=confirm)

        if type == "reposition":
            res = self.handle_ops_repo_ubi(line=line, confirm=confirm)

    def get_views(self, line, message = ""):

        if self.type =='reposition':
            print "get_views: " + line + "task: " +str(self.task_id) + " > Op: " +str(self.op_id)
            self.op_id = self.ops[str(self.active_op)]['ID']
            vis = self.ops[str(self.active_op)]['VISITED']
            proc = self.ops[str(self.active_op)]['PROCESADO']
            #self.state ='ops'
            if self.views ==1: # filtrar visitados
                if vis:
                    #vamos a la siguiente O a la primera
                    self.handle_ops_repo_ubi(line=line)
                else:
                    self._snd(self.get_str_form_repo_ops())

            elif self.views == 2: # filtrar pendientes
                if proc:
                    #vamos a la siguiente O a la primera
                    self.handle_ops_repo_ubi(line=line)
                else:
                    self._snd(self.get_str_form_repo_ops())
            else:
                vis = self.ops[str(self.active_op)]['VISITED']
                print "OK. get_views"
                self._snd(self.get_str_form_repo_ops() + message)

        if self.type =='ubication':
            print "get_views: " + line + "task: " +str(self.task_id) + " > Op: " +str(self.op_id)
            self.op_id = self.ops[str(self.active_op)]['ID']
            vis = self.ops[str(self.active_op)]['VISITED']
            proc = self.ops[str(self.active_op)]['PROCESADO']
            #self.state ='ops'
            if self.views ==1: # filtrar visitados
                if vis:
                    #vamos a la siguiente O a la primera
                    self.handle_ops_ubi(line=line)
                else:
                    self._snd(self.get_str_form_ops())

            elif self.views == 2: # filtrar pendientes
                if proc:
                    #vamos a la siguiente O a la primera
                    self.handle_ops_ubi(line=line)
                else:
                    self._snd(self.get_str_form_ops())
            else:
                vis = self.ops[str(self.active_op)]['VISITED']
                print "OK. get_views"
                self._snd(self.get_str_form_ops() + message)

    def get_cameras_menu(self, type = False):
        """
        Devuelve el menú con las cámaras disponibles
        """
        self.last = "get_cameras_menu"
        delimiter = "\n********************\n"
        #str_menu = "0 -> Volver\n"
        str_menu=""
        if self.type== 'ubication':
            str_menu +=u"0-> Ubicación Manual\n"
        for key in self.factory.menu_cameras:
            key_ = str(key)
            intro = key_ + "-> "
            if key_ in self.camera_ids:
                intro = self.inverse(intro)
            str_menu += intro + (self.factory.menu_cameras[key][1] or 'Sin BCD Name') + "\n"
        if self.type== 'ubication':
            str_menu +=u"9-> Multipack\n"
        keys = u"%s Atrás "%KEY_VOLVER
        if self.camera_ids or self.type !='picking':
            keys += "%s Buscar"%KEY_CONFIRM

        str_menu+= keys
        return str_menu

    def handle_camera_selected(self, line):
        """
        Manejador de los estados location, reposition y picking, pide elegir
        cámara, en caso afirmativo trata de obtener una tarea ya existente
        o crearse una. Quizás halla que meter estado intermedio para que
        seleccione el modo manual de ubicar o el que te da las tareas.
        """

        if line == '0':
            task_id= self.factory.odoo_con.create_task_from_gun(self.user_id)
            self.check_task()
            self.task_id = task_id
            for tk in self.tasks:
                if self.tasks[tk]['id']==task_id:
                    self.active_task= tk
            self.camera_ids=[]
            self.state="list_ops"
            self._snd(self.get_str_list_ops())#, u'\nTarea Creada\nScanea en Playa')
            return

        if line == '9' and self.type == "ubication":
            self.state = 'multipack'
            self.packs=[]
            self.step=0
            self._snd(self.get_str_create_multipack_from_pick())
            return

        if line== KEY_VOLVER:
            self.state = "menu1"
            self.machine_id = False
            self.camera_ids = []
            self._snd(self.get_str_menu1())
            return False

        str_keys = [str(x) for x in self.factory.menu_cameras.keys()]

        if line in str_keys:
            if line not in self.camera_ids:
                self.camera_ids.append (line)
                temp_type_id = self.factory.menu_cameras[self.int_(line)][2]
                inc=1
                for item_ in self.factory.menu_cameras:
                    item = self.factory.menu_cameras[item_]
                    if item[2] == temp_type_id:
                        if not str(inc) in self.camera_ids:
                            self.camera_ids.append(str(inc))
                    inc+=1

            else:
                self.camera_ids.remove (line)
            self._snd(self.get_cameras_menu())
            return

        if line == KEY_CONFIRM and (self.type=='picking' and self.camera_ids) or self.type != 'picking':
            try:
                self.camera_id=[]
                for camera_ in self.camera_ids:
                    self.camera_id.append(self.factory.menu_cameras[self.int_(camera_)][0] or 'Sin BCD Name')
                date_planned=datetime.date.today().strftime("%Y-%m-%d")
                self._snd(u'Buscando Tarea ...')
                self.task_id = self.factory.odoo_con.get_task_of_type(self.user_id,
                                                                      self.camera_id,
                                                                      self.type,
                                                                      self.machine_id,
                                                                      self.route_id,
                                                                      date_planned)

            except Exception, e:
                print e.message
                self._snd_error(self.get_cameras_menu(), e.message)
                return

            if self.task_id:
                self.factory.odoo_con.set_to_process(self.user_id, self.task_id)
                self.check_task()
                self.active_task= self.get_active_task()
                self.camera_ids=[]
                if self.type=='picking':
                    self.state ='list_waves'
                    self._snd(self.get_str_list_waves(), u'\nTarea Creada')
                elif self.type == "ubication":
                    self.state = 'list_ops'
                    self._snd(self.get_str_list_ops(), u'\nTarea Creada')
                elif self.type == "reposition":
                    self.state = 'list_repo_ops'
                    self._snd(self.get_str_list_repo_ops(), u'\nTarea Creada')
                return
            if not self.task_id:
                self.last_state = self.state
                self.state = "tasks"
                self.vals = self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            message =u'\Error. No hay tareas'
            self._snd(self.get_cameras_menu(), message)
            return
            #
            #
            #     old_state = self.state
            #     self.state = next_state[old_state]
            #     self.op_data = self.get_operation_data()
            #     op_str = self.get_operation_str(mode='scan_op')
            #     self._snd(op_str)
        if line not in str_keys:
            str_error = u"La opcion %s no es valida.\nReintentar\n" % line
            self._snd(str_error + self.get_cameras_menu())
            return

    def get_machines_menu(self, type ):
        """
        Devuelve el menú con las cámaras disponibles
        """
        self.last = "get_machines_menu"
        delimiter = "\n********************\n"
        #str_menu = "0 -> Volver\n"
        str_menu=""

        self.menu_machines = self.factory.odoo_con.get_machines_menu(type)
        for key in self.menu_machines:
            str_menu += str(key) + " -> " + self.menu_machines[key][1] + "\n"
        keys = u"%s Atrás"%KEY_VOLVER
        str_menu += delimiter + keys
        return str_menu

    def get_routes_menu(self, type ='picking'):
        """
        Devuelve el menú con las cámaras disponibles
        """
        self.last = "get_routes_menu"
        delimiter = "\n********************\n"
        #str_menu = "0 -> Volver\n"
        str_menu=""

        self.routes = self.factory.odoo_con.get_routes_menu(self.user_id, type)
        inc=1
        if self.routes:
            for key in self.routes:
                key_ = int(key)
                if key_>= self.num_order_list_ops and key_<= self.num_order_list_ops + MAX_NUM_ONE:
                    str_menu += str(key) + " -> " + self.routes[key][1] + "\n"
        else:
            str_menu +=u"\nNo hay rutas validadas\n"
        keys = u"%s Volver"%KEY_VOLVER
        str_menu += delimiter + keys
        return str_menu

    def handle_route_selected(self, line=False):

        print "handle_route_selected" + str(line)
        if line== KEY_VOLVER:
            self.state = "menu1"
            self.machine_id = False
            self.route = False
            self.route_id = False
            self._snd(self.get_str_menu1())
            return

        if line == KEY_NEXT:
            if len(self.routes)>self.num_order_list_ops:
                self.num_order_list_ops +=MAX_NUM_ONE
            self._snd(self.get_routes_menu(self.type))
            return

        if line == KEY_PREV:
            self.num_order_list_ops -=MAX_NUM_ONE
            if self.num_order_list_ops <1:
                self.num_order_list_ops ==1
            self._snd(self.get_routes_menu(self.type))
            return


        if self.routes:
            str_keys = [str(x) for x in self.routes.keys()]
            str_keys.append([0])
            if line not in str_keys:
                str_error = u"La opcion %s no es valida.\nReintentar\n" % line
                self._snd(str_error + self.get_routes_menu(self.type))
                return
            else:
                self.camera_ids=[]
                self.route_id = self.routes[(line)][0]
                self.route = self.routes[(line)][1]
                self.state = "picking"
                self._snd(self.get_cameras_menu(type = 'picking'))
                return

        self.route = ""
        self.route_id = False
        self._snd(self.get_routes_menu(), u'No válido\n')
        return

    def handle_machine_selected(self, line=False):

        print "handle_mchines" + str(line)

        if line== KEY_VOLVER:
            self.state = "menu1"
            self.machine_id = False
            self._snd(self.get_str_menu1())
            return

        str_keys = [str(x) for x in self.menu_machines.keys()]
        str_keys.append([0])
        if line not in str_keys:
            str_error = u"La opcion %s no es valida.\nReintentar\n" % line
            self._snd(str_error + self.get_machines_menu(self.type))
            return
        else:
            if line=='0':
                self.machine_id=False
            else:
                self.machine_id = self.menu_machines[self.int_(line)][0]
        self.camera_ids = []
        self.state = self.type or 'ubication'# self.type
        self._snd(self.get_cameras_menu())

    def get_ops_data(self):
        op_data = {}
        try:
            op_data = self.factory.odoo_con.get_ops(self.user_id, self.task_id)


            # if op_data:
            #     self.state = "scan_op"
        except Exception, e:
            expt_str = e.message
            self._snd(expt_str)
        return op_data

    def get_operation_data(self):
        """
        Intenta devolver un diccionario con datos de la siguiente operacion
        no visitada.
        """
        op_data = {}
        try:
            op_data = self.factory.odoo_con.get_op_data(self.user_id, self.task_id)


            # if op_data:
            #     self.state = "scan_op"
        except Exception, e:
            expt_str = e.message
            self._snd(expt_str)
        return op_data

    def get_operation_str(self, mode='scan_op'):
        """
        LLamada después de get_operartion_data, devuelve un string formateado
        con los datos de la operación.
        """
        if not self.op_data:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")
        op_str = ""
        # TODO Excepción de que no haya op_data
        keys = (u"PRODUCTO", u"CANTIDAD", u"LOTE", u"PAQUETE", u"ORIGEN", u"DESTINO", u"PROCESADO")
        for k in keys:
            op_str += k + u":  " + self.op_data[k] + "\n"
        op_str += u"\n(Escriba '#C' para cancelar la operación)\n"
        if mode == 'scan_op':
            op_str += u"************************\nScan Producto/Paquete:"
        if mode == 'scan_location':
            op_str += u"************************\nScan Destino:"
        return op_str

    def cancel_operation(self):
        """
        Cancela la operación marcándola como visitada pero no para procesar
        y muestra la siguiente.
        """
        message = ""
        try:
            finish = self.factory.odoo_con.set_op_visited(self.user_id, self.task_id, self.op_data['ID'], False)  # False to mark as to_process
            if finish:  # No more operation, Return to back menu
                self.factory.odoo_con.finish_task(self.user_id, self.task_id)
                message += "Tarea Finalizada\n"
                message += self.get_str_menu1()
                self.state = "menu1"
                self.op_data = False
                self.task_id = False
            else:  # Get next operation
                self.op_data = self.get_operation_data()
                message += self.get_operation_str(mode='scan_op')
                if self.state in ['scan_op', 'scan_location']:
                    self.state = "scan_op"
                elif self.state in ['scan_op_rep', 'scan_location_rep']:
                    self.state = "scan_op_rep"
                elif self.state in ['scan_op_pick', 'scan_location_pick']:
                    self.state = "scan_op_pick"
            self._snd(message)
        except Exception, e:
            str_error = u"Error al cancelar la operacion o finalizar la tarea %s\n"
            self._snd(str_error + e.message)

    def handle_scan_op(self, line, next_state = False):
        """
        Manejador del estado scan_op. Si se escanea el producto o el paquete
        correctamente, se pasa al estado de escanear la ubicación.
        Si no se mantiene en ese estado
        """
        # Cancelar la operación y pasar a la siguiente.
        if line in KEY_CANCEL:
            self.cancel_operation()
            return
        try:
            done = self.factory.odoo_con.check_scan(self.user_id, self.task_id, self.op_data['ID'], line, 'pack_prod')
            if done:

                self.state = "scan_location"
                self.pack = line
                message = u"Scan correcto. Scanee la ubicación\n"
                message += self.get_operation_str(mode='scan_location')
            else:
                message = u"Scan incorrecto, Escanee de nuevo el paquete\n"
                message += self.get_operation_str(mode='scan_op')
            self._snd(message)
        except Exception, e:
            str_error = u"No se pudo identificar la etiqueta %s\n" % line
            self._snd(str_error + e.message)

    def handle_quantity(self, line):
        """
        Si leemos 2 veces producto/paquete psqamos a menu de cantidades


        """
        #ok

        if line in ["#c", "#C"]:
            self.cancel_operation()
            return
        try:
            if line:
               new_qty = self.op_data['CANTIDAD']
               #aqui tengo que escribir la nueva cantidad

            self.state = "scan_location"
            message = u"Scan correcto. Scanee la ubicación\n"
            message += self.get_operation_str(mode='scan_location')

        except Exception, e:
            str_error = u"Error al cambiar la cantidad %s\n" % line
            self._snd(str_error + e.message)

    def menu_intro_qty (self, from_state, line):
        self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
        op_=self.ops[str(self.active_op)]
        #introc cantidad o confirma la prpopuesta con f1
        message = u"Cantidad:/n <%s> para %s"%(KEY_CONFIRM, op_['CANTIDAD'])
        self.last_state = from_state
        self.state="intro_qty"
        self._snd(message)

    def handle_intro_qty(self, line):
        if line != KEY_CONFIRM:
            try:
                if self.task_id and self.op_id:
                    new_qty =  {
                        "cantidad": float(line)}

                    self.vals["cantidad"] = new_qty
                    res = self.factory.odoo_con.change_value
                    self.get_str_form_ops()
            except Exception, e:
                str_error = u"Error al introducir la cantidad: %s\n" % line
                self._snd(str_error + e.message)

    def handle_intro_origen (self, from_state, line):
        self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
        op_=self.ops[str(self.active_op)]
        #introc cantidad o confirma la prpopuesta con f1
        message = "Origen :/n <" + KEY_CONFIRM + "> para " + str(op_['ORIGEN'])
        self.last_state = from_state
        self.state="intro_origen"
        self._snd(message)

    def handle_intro_origen (self, line):
        if line != KEY_CONFIRM:
            try:
                if self.task_id and self.op_id:
                    #tenemds que buscar el nnuev
                    origen_id =  {
                        "ORIGEN": float(line)}

                    origen_name = self.factory.odoo_con.get(self.user_id, origen_id)
                    self.vals["origen"] = origen_id
                    res = self.factory.odoo_con.change_value(self.user_id, self.op_id, "location_id", origen_id)

                    self.get_str_form_ops()
            except Exception, e:
                str_error = u"Error al introducir la cantidad: %s\n" % line
                self._snd(str_error + e.message)

    def handle_intro_destino(self, from_state, line):
        self.ops = self.factory.odoo_con.get_ops(self.user_id, self.task_id)
        op_=self.ops[str(self.active_op)]
        message = "Destino :/n <" + KEY_CONFIRM + "> para " + str(op_['DESTINO'])
        self.last_state = from_state
        self.state="intro_origen"
        self._snd(message)

    def handle_scan_location(self, line):
        """
        Manejador del estado scan_location. Si se escanea correctamente la
        ubicación destino, se muestra la siguiente operación (volviendo al
        punto de escanear el paquete/producto) o se finaliza la tarea si ya
        no quedan más.
        """
        # Cancelar la operación y pasar a la siguiente.

        if line == KEY_CANCEL:
            self.cancel_operation()
            return
        if line == self.pack:
            #espera ubicacion, pero repite producto; entonce hay que cambiar la cantidad del op_data

            self.op_data = self.get_operation_data()
            message = self.get_operation_str(mode='scan_quantity')
            message += "Nueva cantidad:(%s)\n"%self.op_data['CANTIDAD']
            self.state = "scan_quantity"
            self._snd(message)
            return

        try:
            done = self.factory.odoo_con.check_scan(self.user_id, self.task_id, self.op_data['ID'], line, 'location')
            if done:  # Ubicación correctamente escaneada
                try:
                    message = u"Scan correcto.\n"
                    finish = self.factory.odoo_con.set_op_visited(self.user_id, self.task_id, self.op_data['ID'], True)  # True to mark as to_process
                    if finish:  # No more operation, Return to back menu
                        res = self.factory.odoo_con.finish_task(self.user_id, self.task_id)
                        if res:
                            self.print_task(self.task_id)
                        message += "Tarea Finalizada\n"
                        message += self.get_str_menu1()
                        self.state = "menu1"
                        self.op_data = False
                        self.task_id = False
                    else:  # Get next operation
                        self.op_data = self.get_operation_data()
                        message += self.get_operation_str(mode='scan_op')
                        self.state = "scan_op"
                except Exception, e:
                    str_error = u"Error al marcar la operacion o al finalizar tarea\n"
                    str_error += e.message + "\n"
                    message += str_error + self.get_operation_str(mode='scan_location')
            else:  # Ubicación mal escaneada, reintentar
                message = u"Scan incorrecto.\nEscanee de nuevo el destino\n"
                message += self.get_operation_str(mode='scan_location')
            self._snd(message)
        except Exception, e:
            str_error = u"No se pudo identificar la etiqueta %s\n" % line
            self._snd(str_error + e.message)

    def handle_scan_op_rep(self, line):
        """
        Manejador del estado scan_op_rep. Si se escanea el producto o el paquete
        correctamente, se pasa al estado de escanear la ubicación.
        Si no se mantiene en ese estado
        """
        # Cancelar la operación y pasar a la siguiente.
        if line in ["#c", "#C"]:
            self.cancel_operation()
            return

        try:
            done = self.factory.odoo_con.check_scan(self.user_id, self.task_id, self.op_data['ID'], line, 'pack_prod')
            if done:
                self.state = "scan_location"
                message = u"Scan correcto. Scanee la ubicación\n"
                message += self.get_operation_str(mode='scan_location')
            else:
                message = u"Scan incorrecto, Escanee de nuevo el paquete\n"
                message += self.get_operation_str(mode='scan_op')
            self._snd(message)
        except Exception, e:
            str_error = u"No se pudo identificar la etiqueta %s\n" % line
            self._snd(str_error + e.message)

    def handle_yes_no (self, line=KEY_NO):

        self.state = self.last_state
        res = line
        self.lineReceived(res, True)


    def function_keys(self, line):

        if line == KEY_F1:
            line = "F1"
        elif line == KEY_F2:
            line = "F2"
        elif line == KEY_F3:
            line = "F3"
        elif line == KEY_F4:
            line = "F4"
        elif line == KEY_F5:
            line = "F5"
        elif line == KEY_F6:
            line = "F6"
        elif line == KEY_F7:
            line = "F7"
        elif line == KEY_F8:
            line = "F8"
        elif line == KEY_F9:
            line = "F9"
        elif line == KEY_F10:
            line = "F10"
        elif line == KEY_F11:
            line = "F11"
        elif line == KEY_F12:
            line = "F12"

        elif line == KEY_UP:
            line = "KP"
        elif line == KEY_DOWN:
            line = "KD"
        else:
            line = False
        return line

    def reset_vals(self):

        for k in self.vals:
            self.vals[k] = False
        return True

    def reset_all_vals(self, vals):
        for k in vals:
            vals[k] = False
            if k=="do_pack":
                vals[k]='do_pack'
            if k=="quantity":
                vals[k]=0


        return True

    def inverse(self, strg):
        strg = u'%s'%strg
        if strg:
            res = COLORS_INV + strg + COLORS_0
        return res

    def tasks_paused(self):
        #Devuelve True si estan todas pausadas o no hay ninguna

        res = True
        for x in self.tasks:
            if self.tasks[x]['paused']==False:
                res = False
        return res

    def change_paquete(self, op_id, new_paquete_id):
        # primero tenemos que comprobar que el paque te no está asignado, si lo está
        # nº de operacion y usuario que la bloquea
        # si está libre canmbiamos el paquete ...
        self.factory.odoo_con.check_scan(self.user_id, self.task_id, self.op_data['ID'], op_id, 'pack_prod')

    def int_(self, str):
        res = 0
        try:
            res =int(str)
        except:
            res = 0
        return res

    def float_(self, str):

        try:
            res =float(str)
        except:
            res =0.00
        return res

    def get_menu_parametros(self):

        res = "x" if self.print_tag_option else " "
        menu_str = u"1 [%s] Imprimir etiquetas\n"%res
        res = "x" if self.factory.debug else " "
        menu_str += u"2 [%s] Debug\n"%res
        res = "x" if self.show_keys else " "
        menu_str += u"3 [%s] Ayuda Teclas\n"%res
        res = "x" if self.show_op_processed else " "
        menu_str += u"4 [%s] Mostrar OPS Pendientes\n"%res

        menu_str += u"9 >Volver\n"
        return menu_str

    def handle_menu_parametros(self, line):

        if line not in ["1", "2", "3", "4", "9"] and line != KEY_VOLVER:
            str_error = u"La opcion %s no es valida.\nReintentar:\n" % line
            self.state='tools'
            self._snd(self.get_menu_parametros(), str_error)
            return
        if line == "1":
            self.print_tag_option = not self.print_tag_option
            self._snd(self.get_menu_parametros())
            return
        if line == "2":
            self.factory.debug = not self.factory.debug
            if self.factory.debug:
                self.factory.users_codes.remove(self.code)
            else:
                self.factory.users_codes.append(self.code)
            self._snd(self.get_menu_parametros())
            return
        if line == "3":
            self.show_keys = not self.show_keys
            self._snd(self.get_menu_parametros())
            return
        if line == "4":
            self.show_op_processed= not self.show_op_processed
            self._snd(self.get_menu_parametros())
            return
        if line == "9" or line == KEY_VOLVER:
            self.state ="tools"
            self._snd(self.get_menu_tools())
            return

        str_error = u"La opcion %s no es valida.\nReintentar:\n" %line
        self._snd(self.get_menu_parametros(), str_error)
        return

    def get_menu_tools(self):

        menu_str = u"1 >Asignar Zona Picking\n" \
                   u"2 >Dividir Zona Picking\n" \
                   u"3 >Crear Multipack\n" \
                   u"4 >Info Producto\n" \
                   u"5 >Info Paquete\n" \
                   u"6 >Imprimir Etiquetas\n"\
                   u"8 >Parámetros\n"\
                   u"9 >Volver\n"
        # if self.show_keys:
        #     keys = "\n%s Atrás"%KEY_VOLVER
        #menu_str += # keys
        return menu_str

    def handle_menu_tool(self, line):

        print "Menu Tools"
        if line not in ["1", "3", "6", "8", "9"] and line != KEY_VOLVER:
            str_error = u"La opcion %s no es valida.\nReintentar:\n" % line
            self.state='tools'
            self._snd(self.get_menu_tools(), str_error)

        elif line=="9" or line == KEY_VOLVER:
            self.state='menu1'
            self._snd(self.get_str_menu1())

        elif line =='1':
            self.state = 'set_picking_zone'
            self.step=0
            self._snd(self.get_set_picking_zone())
        elif line == '2':
            self.state = 'create_picking_zone'
            self.step=0
            self._snd(self.get_str_create_picking_zone())
        elif line == '3':
            self.state = 'create_multipack'
            self.step=0
            self.num_order_list_ops = 1
            self.packs = []
            self._snd(self.get_str_create_multipack())
        elif line == '6':
            self.state = 'print_tags'
            self.step=0
            self.num_order_list_ops = 1
            self.packs = []
            self._snd(self.get_str_print_tags())
        elif line == '8':
            self.state = 'parametros'
            self.step=0
            self.num_order_list_ops = 1
            self.packs = []
            self._snd(self.get_menu_parametros())
        else:
            str_error = u"La opcion %s no está implementada.\nReintentar:\n" % line
            self.state='tools'
            self._snd(self.get_menu_tools(), str_error)
        return

    def get_str_create_multipack(self, message =''):

        str_menu=u"Crear Multipack\n"
        if self.step == 0:
            str_menu += self.inverse(u"Escanea los paquetes\n")
            #str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)

        if self.step == 1:
            str_menu += u"Escanea los paquetes\n"

            for inc in range(self.num_order_list_ops, self.num_order_list_ops+MAX_NUM_ONE):
                if inc <= len(self.packs):
                    str_menu += u'%s > %s\n'%(inc, self.packs[inc-1]['name'])

            if len(self.packs)>1:
                str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)
            str_menu += message
        return str_menu

    def handle_create_multipack(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)

        if line == KEY_NEXT:
            if self.num_order_list_ops + MAX_NUM_ONE <=len(self.packs):
                self.num_order_list_ops += MAX_NUM_ONE
            self._snd(self.get_str_create_multipack())
            return
        if line == KEY_PREV:
            self.num_order_list_ops -= MAX_NUM
            if self.num_order_list_ops <1:
                self.num_order_list_ops=1
            self._snd(self.get_str_create_multipack())
            return

        if order_line == PRE_PACK:
            add_pack = True
            for pack in self.packs:
                if line_int == pack['id']:
                    self.packs.remove(pack)
                    add_pack = False
                    message = u"\nPaquete Borrado"
                    break

            if add_pack:
                self.step=1
                new_pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                if new_pack['exist']:
                    self.packs.append({
                        'id': new_pack['package_id'],
                        'name': new_pack['package']
                    })

                    message = u'%s: %s\n%s %s'%(
                        new_pack['package'], new_pack['lot'],
                        new_pack['packed_qty'], new_pack['uom'])
                else:
                    message = u'\nPaquete no encontrado'
            self._snd(self.get_str_create_multipack(), message)
            return

        if line == KEY_CONFIRM and len(self.packs)>1:

            res = self.create_multipack_from_gun()
            message=''
            if res:
                message = u'Ok Multi: %s\n'%res
                self.step = 0
                self.packs =[]
                self._snd(self.get_str_create_multipack(), message)
            else:
                message=u'\nError.'
                self._snd(self.get_str_create_multipack(), message)
            return

        if line == KEY_VOLVER:
            self.packs = []
            self.step=0
            self.state='tools'
            self._snd(self.get_menu_tools())
            return

        message=u'\nNo te entiendo.'
        self._snd(self.get_str_create_multipack(), message)
        return

    def create_multipack_from_gun(self):
        if len(self.packs)<1:
            message = "\nNecesitas un paquete"
            return False, message
        packs = []
        for pack in self.packs:
            packs.append(pack['id'])
        res = self.factory.odoo_con.create_multipack_from_gun(self.user_id, packs)
        return res

    def get_str_create_multipack_from_pick(self, message =''):
        message=''
        str_menu=u"Crear Multipack\n"
        if self.step == 0:
            str_menu += u"\nEscanea un paquetes\npara seleccionar el albarán"
            #str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)

        if self.step >0:
            str_menu += u"%s\n"%self.packs['pick']
            ops = self.packs['ops']
            for inc in range(self.num_order_list_ops, self.num_order_list_ops+MAX_NUM_ONE):
                if inc <= len(ops):
                    op = ops[inc-1]
                    sel = 'x' if op['selected'] else ' '
                    str_menu += u'[%s] %s\n'%(sel, op['package'])

        if self.packs:
            if len(self.packs)>1:
                str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)

        str_menu += message
        return str_menu

    def handle_create_multipack_from_pick(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)
        if line ==KEY_VOLVER:
            if self.step==0:
                self.state = 'ubication'
                self._snd(self.get_cameras_menu())
                return
            if self.step>0:
                self.step=0
                self.num_order_list_ops=0
                self.packs=[]
                self._snd(self.get_str_create_multipack_from_pick())

        if line == KEY_NEXT:
            if self.num_order_list_ops + MAX_NUM_ONE <=len(self.packs):
                self.num_order_list_ops += MAX_NUM_ONE
            self._snd(self.get_str_create_multipack_from_pick())
            return
        if line == KEY_PREV:
            self.num_order_list_ops -= MAX_NUM
            if self.num_order_list_ops <1:
                self.num_order_list_ops=1
            self._snd(self.get_str_create_multipack_from_pick())
            return

        if order_line == PRE_PACK and not self.packs:
            self.packs = self.factory.odoo_con.get_packs_in_same_picking(self.user_id, line_int)

            if not self.packs:
                message = u"\nPaquete Vacío/Nada Seleccionado"
                self._snd(self.get_str_create_multipack_from_pick(), message)
                return
            else:
                self.step=1
                num_order_list_ops = len(self.packs['ops'])
                message = u"\nScan para Marcar/Desmarcar"
                self._snd(self.get_str_create_multipack_from_pick(), message)
                return


        if order_line == PRE_PACK and self.packs:
            add_pack = True
            message = ''
            inc=0
            ops = self.packs['ops']
            for op in ops:
                if line_int ==  op['package_id']:
                    self.packs['ops'][inc]['selected']= not self.packs['ops'][inc]['selected']
                    break

                inc +=1
            self._snd(self.get_str_create_multipack_from_pick(), message)
            return

        if line == KEY_CONFIRM and len(self.packs)>1:
            pick_id = self.packs['pick_id']
            list_ops = []
            for op in self.packs['ops']:
                if op ['selected']:
                    list_ops.append(op['id'])
            message=''
            if list_ops:
                res = self.factory.odoo_con.create_multipack_from_pick(self.user_id, pick_id, list_ops)
                if res:
                    message = u'Ok Multi: %s\n'%res
                    self.step = 0
                    self.packs =[]
                    self._snd(self.get_str_create_multipack_from_pick(), message)
                else:
                    message=u'\nError.'
                    self._snd(self.get_str_create_multipack_from_pick(), message)
                return
            else:
                message=u'\nNecesitas + de 1 paquete.'
                self._snd(self.get_str_create_multipack_from_pick(), message)
                return
        message=u'\nNo te entiendo.'
        self._snd(self.get_str_create_multipack_from_pick(), message)
        return

    def get_str_print_tags(self, message =''):

        str_menu=u"Imprimir Etiquetas\n"
        if self.step == 0:
            str_menu += self.inverse(u"Escanea los paquetes\n")
            str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)

        if self.step == 1:
            str_menu += u"Escanea los paquetes\n"

            for inc in range(self.num_order_list_ops, self.num_order_list_ops+MAX_NUM_ONE):
                if inc <= len(self.packs):
                    str_menu += u'%s > %s\n'%(inc, self.packs[inc-1]['name'])

            str_menu += self.inverse(u"%s Confimar"%KEY_CONFIRM)
            str_menu += message
        return str_menu

    def handle_print_tags(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)

        if line == KEY_VOLVER:
            self.packs = []
            self.step=0
            self.state='tools'
            self._snd(self.get_menu_tools())
            return


        if line == KEY_NEXT:
            if self.num_order_list_ops + MAX_NUM_ONE <=len(self.packs):
                self.num_order_list_ops += MAX_NUM_ONE
            self._snd(self.get_str_print_tags())
            return
        if line == KEY_PREV:
            self.num_order_list_ops -= MAX_NUM
            if self.num_order_list_ops <1:
                self.num_order_list_ops=1
            self._snd(self.get_str_print_tags())
            return

        if order_line == PRE_PACK:
            add_pack = True
            for pack in self.packs:
                if line_int == pack['id']:
                    self.packs.remove(pack)
                    add_pack = False
                    message = u"\nPaquete Borrado"
                    break

            if add_pack:
                self.step=1
                new_pack = self.factory.odoo_con.get_pack_gun_info(self.user_id, line_int)
                if new_pack['exist'] and new_pack['packed_qty']>0:
                    self.packs.append({
                        'id': new_pack['package_id'],
                        'name': new_pack['package']
                    })

                    message = u'%s: %s\n%s %s'%(
                        new_pack['package'], new_pack['lot'],
                        new_pack['packed_qty'], new_pack['uom'])
                else:
                    message = u'\nPaquete no encontrado\n o vacio'
            self._snd(self.get_str_print_tags(), message)
            return
        if line == KEY_CONFIRM:
            for tag_ in self.packs:
                tag=[]
                tag.append(tag_['id'])
                res = self.factory.odoo_con.print_from_gun(self.user_id, tag)
            message =u"\nEnviadas a Imprimir"
            self.step = 0
            self.packs =[]
            self._snd(self.get_str_print_tags(), message)
            return
        message =u"\nNo te entiendo"
        self._snd(self.get_str_print_tags(), message)
        return

    def print_task(self, task_id):
        return
        if not self.print_tag_option:
            return
        res = self.factory.odoo_con.print_task(self.user_id, task_id)
        return

    def print_packs(self, packs):
        print "Imprimiendo: %s"%packs[0]
        if not self.print_tag_option:
            return
        if len(packs)<1:
            message = "\nNecesitas un paquete"
            return False, message
        res = self.factory.odoo_con.print_from_gun(self.user_id, packs)
        return res


    def handle_create_picking_zone(self, line):


        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        line_int = self.int_(line)

        if line == KEY_VOLVER:
            self.vals={}
            self.step=0
            self.state= 'tools'
            self._snd(self.get_menu_tools())
            return

        if self.step == 0:
            self.vals = {}
            if order_line ==PRE_LOC:
                pick_zone = self.factory.odoo_con.get_location_gun_info(self.user_id, location_id = line_int)
                if pick_zone['exist']:
                    self.vals={
                        'location_id' : pick_zone['location_id'],
                        'bcd_name': pick_zone['bcd_name'],
                        'sub_cols':0
                        }
                    self.step =1
                    self._snd(self.get_str_create_picking_zone())
                    return
                self.step =0
                message = u'No encontrado'
                self._snd(self.get_str_create_picking_zone(), message)
                return

        if self.step==1:
            if line in ['2','3','4','5', '6','7','8','9']:
                self.vals['sub_cols']= line_int
                self.step=2
                self._snd(self.get_str_create_picking_zone())
                return
            self.step =1
            message = u'no Valido'
            self._snd(self.get_str_create_picking_zone(), message)
            return

        if self.step==2 and line==KEY_CONFIRM:
            res = self.factory.odoo_con.create_picking_sublocation_from_gun(self.user_id, self.vals['location_id'],self.vals['sub_cols'])
            if res:
                message= u'Ubicaciones creadas\n'
                print res
                self.step=0
                self._snd(self.get_str_create_picking_zone(), message)
                return
            else:
                message= u'Error desconocido\n'
                self.step=0
                self._snd(self.get_str_create_picking_zone(), message)
                return


            message = u'no Valido'
            self._snd(self.get_str_create_picking_zone(), message)
            return

        message = u'no Valido'
        self._snd(self.get_str_create_picking_zone(), message)
        return

    def get_str_create_picking_zone(self):

        str_menu=u"Dividir Zona de Picking\n"

        if self.step == 0:
            str_menu += self.inverse(u"\nScan Pick Zone\n")

        if self.step ==1:
            str_menu += u'Zona de Pick a partir:\n%s\n'%self.vals['bcd_name']
            str_menu += self.inverse(u"\nDivisiones [2-9]\n")

        if self.step ==2:
            str_menu += u'Zona de Pick a partir:\n%s\n'%self.vals['bcd_name']
            str_menu += u'Divisiones: %s\n'%self.vals['sub_cols']
            str_menu += self.inverse(u"\n%s Confirma\n"%KEY_CONFIRM)

        return str_menu

    def get_set_picking_zone(self):

        str_menu=u"Asignar Zona de Picking\n"
        if self.step == 0:
            str_menu += self.inverse(u"\nScan Paquete\n")

        if self.step ==3:
            str_menu += u"\n%s\n(%s)"%(self.vals['product'], self.old_zone or "Sin Zona de Picking")
            str_menu += self.inverse(u"\n\nSCAN Zona Picking\n")

        if self.step == 6:
            str_menu += u"\n%s\n(%s)"%(self.vals['product'], self.old_zone or "Sin Zona de Picking")
            str_menu += u"\nNueva zona:\n%s"%(self.vals['bcd_picking_location'])
            if self.step==6:
                str_menu += self.inverse(u"\n\n%s Si %s No")%(KEY_YES, KEY_CANCEL)

        keys = u"\n%s Volver"%KEY_VOLVER

        if self.show_keys:
            str_menu +=keys

        return str_menu

    def handle_set_picking_zone(self, line, confirm=False):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        message =''

        if line == KEY_VOLVER:
            self.state='tools'
            self._snd(self.get_menu_tools())
            return

        if self.step==0:
            self.vals = False
            product_id = False

            if order_line==PRE_PACK:
                self.vals =  self.factory.odoo_con.get_pack_gun_info(self.user_id, line)
                if not self.vals:
                    message=u"\nNo encuentro el paquete"
                    self._snd(self.get_set_picking_zone(), message)
                    return
                product_id = self.vals['product_id']
            elif order_line == PRE_PROD:
                product_id = line

            if product_id:
                self.vals =  self.factory.odoo_con.get_product_gun_complete_info(self.user_id, product_id = product_id)
                if not self.vals:
                    message="\nNo encuentro el\nProducto/EAN"
                    self._snd(self.get_set_picking_zone(), message)
                    return
                else:
                    self.old_zone_id = self.vals["bcd_picking_location"] or False
                    self.old_zone = self.vals["bcd_picking_location"] or "Sin Asignar"
                    self.step=3
                    self._snd(self.get_set_picking_zone())
                    return
            message=u"\nNo te entiendo"
            self._snd(self.get_set_picking_zone(), message)
            return

        if (self.step == 3 or self.step==6) and order_line == PRE_LOC:

            res = self.factory.odoo_con.get_location_gun_info(
                    self.user_id, self.int_(line))

            if res['exist'] == False:
                message = u"\nLocation Not Found"
                self.step=3
                self._snd(self.get_set_picking_zone(), message)
                return

            if res['temp_type_id'] != self.vals['temp_type_id'] or res['zone']!='picking':
                message = u"\nNot picking zone or \n not temperature OK "
                self.step=3
                self._snd(self.get_set_picking_zone(), message)
                return
            try:
                res = self.factory.odoo_con.check_picking_zone(
                    self.user_id, self.vals['product_id'], self.int_(line))
            except Exception,e:

                message = u"\nLocation not available"
                self.step=3
                self._snd(self.get_set_picking_zone(), message)
                return

            if res:
                self.vals =  self.factory.odoo_con.get_product_gun_complete_info(self.user_id, self.vals['product_id'])
                self.step=6
                self._snd(self.get_set_picking_zone())
                return
            else:
                message = u"Error.No Asignada"
                self.vals =  self.factory.odoo_con.get_product_gun_complete_info(self.user_id, self.vals['product_id'])
                self.step=3
                self._snd(self.get_set_picking_zone(), message)
                return
            message = u"Not valid Zone"
            self._snd(self.get_set_picking_zone(), message)
            return

        if self.step == 6:
            if line ==KEY_YES:
                message = u"Asig: %s \npara: %s\n"% (self.vals["bcd_picking_location"],self.vals['product'])
                self.step = 0
                self.old_zone_id = False
                self._snd(self.get_set_picking_zone(), message)
                return

            else:
                #Cualquier otra cosa cancela la operación ...
                res = self.factory.odoo_con.check_picking_zone(
                    self.user_id, self.vals['product_id'], self.old_zone_id)
                self.old_zone_id = self.vals["bcd_picking_location"] or False
                self.old_zone = self.vals["bcd_picking_location"] or u"Sin Asignar"
                message = u"Canceled\n"
                self.step = 0
                self._snd(self.get_set_picking_zone(), message)
                return
        message = u"Opción no válida"
        self._snd(self.get_set_picking_zone(), message)
        return

    def get_str_select_picking_subzone(self, parent_pick_id = False, message = ''):

        menu_strg =''
        menu_strg += "Selecciona Subzona:\n"
        if not parent_pick_id:
            parent_pick_id = self.parent_pick_id
        else:
            self.parent_pick_id = parent_pick_id

        self.subzones = self.factory.odoo_con.get_subpicking_zones(self.user_id, location_id = parent_pick_id)
        inc=1
        for x in self.subzones:
            str = u'%s > %s\n'%(inc, x['bcd_name'])
            if self.selected_subzone == x['id']:
                str = self.inverse(str)
            menu_strg += str
            inc +=1

        self.selected_subzone = False
        menu_strg += u'SubZona [1 - %s]\n'%(inc-1)
        menu_strg += u'%s Volver\n'%KEY_VOLVER
        self._snd(menu_strg, message)
        return menu_strg

    def handle_select_picking_subzone(self, line):

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        line_int = self.int_(line)

        if line == KEY_VOLVER:
            self.parent_pick_id = False
            self.selected_subzone = False
            self.state = self.last_state
            self.lineReceived(KEY_VOLVER)
            return
        if line == KEY_CONFIRM:
            message = u'\nNo implementado'
            self._snd(self.get_str_select_picking_subzone(self.parent_pick_id), message)
            return


        elif line_int and line_int>0 and line_int<=len(self.subzones):

            self.parent_pick_id = self.subzones[line_int-1]['id']
            self.selected_subzone = self.parent_pick_id
            self.state = self.last_state
            self.lineReceived(u'%s%s'%(PRE_LOC, self.selected_subzone))
            return

        else:
            message = u'\nNo te entiendo\n'
            self._snd(self.get_str_select_picking_subzone(self.parent_pick_id))
            return

        #
        # if self.menu_anterior == 'get_str_form_repo_ops':
        #     self._snd(self.get_str_form_repo_ops())
        # elif self.menu_anterior == 'get_str_manual_transfer_packet':
        #     self._snd(self.get_str_manual_transfer_packet())
        #
        # return
        #

    # def get_location_gun_info(self, user_id, location_id = False, bcd_code = False, type =''):
    #
    #     res = self.factory.odoo_con.get_location_gun_info(self.user_id,
    #                                                       location_id = location_id,
    #                                                       bcd_code = bcd_code,
    #                                                       type = type)
    #     if not res['childs']:
    #         self.last_state = self.state
    #         self.state = 'sel_sub_picking_zone'
    #
    #
    #
    #     return res

            #es que es una sububicación de picking

    #def get_str_show_package(self, location_id):
        # aqui mostramos el contenido del paquete.
        #

    def create_package_from_gun(self, op):

        values = {
            'uos_qty': op['uos_qty'],
            'uos_id': op['uos_id'],
        }

    def get_tags_message(self, opcion = False, pack = False, product = False):
        message = ''
        print_tag = False
        if not product:
            if opcion =='do_pack':
                if pack:
                    message = u'\nOk. Etiqueta Destino\nPierde Origen'
                else:
                    message = u'\nOk. Etiqueta Origen'
            else:
                if pack:
                    message = u'\nOk. Origen + Destino.'
                else:
                    message = u'\nOk. Etiqueta Origen'

        if product:
            if opcion =='do_pack':
                if pack:
                    message = u'\nOk. Etiqueta Destino'
                else:
                    message = u'\nOk. Etiqueta Nueva'
                    print_tag = True
            else:
                print_tag = True
                if pack:
                    message = u'\nOk. Etiqueta Nueva\nConserva Destino'
                else:
                    message = u'\nOk. Etiqueta Nueva'

        return self.inverse(message), print_tag

# Asigna a cada conexión un protocolo ScanGunProtocol
class ScanGunFactory(Factory):
    def __init__(self):
        # Códigos telnet de usuarios registrados
        self.users_codes = []



        server, port, db, user, password = get_connection_params(
            ['odoo_host', 'odoo_port', 'odoo_db', 'odoo_user',
             'odoo_password'])
        try:
            # Conexión general con odoo
            self.odoo_con = OdooDao(server, port, db, user, password)
            # Obtener menu de camaras
            self.menu_cameras = self.odoo_con.get_cameras_menu()
        except:
            print u"Ocurrió un error al intentar conectarse con odoo"
            sys.exit(0)

    def buildProtocol(self, addr):
        return ScanGunProtocol(self)

# Para hacer el bucle de escucha del servidor

reactor.listenTCP(5000, ScanGunFactory())
reactor.run()
