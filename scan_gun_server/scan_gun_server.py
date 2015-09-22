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
KEY_F5 = '9b31367e' #'\x9b16~'
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

KEY_PAUSE = "F2"
KEY_MANUAL ="F3"
KEY_PRINT = "F4"

KEY_RUN = "F5"
KEY_FINISH = "F5"

KEY_ORIGEN = "F6"
KEY_WAVE_OPS = "F6"
KEY_PAQUETE = "F7"
KEY_QTY = "F8"
KEY_DESTINO = "F9"
KEY_CALCULADORA = "F8"

KEY_NO_REALIZADA = "F10"

KEY_NO ="F11"
KEY_CANCEL = "F11"

KEY_VOLVER = "F12"

VALS = {'paquete': False, 'destino' : False, 'origen' : False, 'cantidad' : 0, 'lote' : False}
VALS_MANUAL = {'exist': False, 'package_id': False, 'product_id' : False, 'quantity': 0,
               'lot_id': False, 'src_location_id': False, 'dest_location_id': False, 'do_pack': 'no_pack',
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
MAX_NUM =8
# Para leer el archivo de configuración y guardarlo en params
def read_file():
    with open('telnet.cfg', 'r') as configfile:
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
        self.state = "register"
        self.last_state = self.state
        self.user_id = False
        self.user_name = False
        self.code = False

        self.show_keys = True
        self.views = 0 # ver pendientes, 1# ver no vistas, 2 ver todoas
        self.reset_self_task()
        self.reset_self_op()
        self.last = False


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

        self.loc_id = False  #se usa para confirmar una segunda lectura
        self.step = 0
        self.new_qty =0.00
        self.uom_var = False
        self.uos_var = False
        self.qty_calc = []
        self.package ={}

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

    def connectionMade(self):
        """
        Método del framework. Mensaje al establecer la conexión
        """
        self.debug=True
        self._snd(u"Introduzca su codigo de operador:")

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
        """
        Método del framework. LLamado cada vez que se recibe una linea
        """

        print "Estado: " +self.state + " Anterior: " + self.last_state
        izq = line.encode('hex')[0:2]
        if izq == "8f" or izq == "9b":
            #son teclas de fucnion
            line = self.function_keys(line.encode('hex'))

        print "Entrada: " + str(line)
        line= str(line)

        # try:


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
        elif self.state =="machines":
            self.handle_machine_selected(line)
        elif self.state =="manual_transfer":
            self.handle_manual_menu(line)
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
        elif self.state == "form_repo_ops":
            self.handle_form_repo_ops(line)
        elif self.state == "form_ops":
            self.handle_form_ubi_ops(line, confirm=confirm)
            #self.handle_ops(line, confirm=confirm)
        elif self.state in ["ubication", "reposition", "picking"]:
            self.handle_camera_selected(line)
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
        else:
            self._snd(u"Introduciste %s, pero paso olimpicamente:" % line)
        # except Exception, e:
        #     str_error = u"Ocurrio un error <line>.\n" + "state: " + self.state + "\n" + "line: " + str(line) + "\n"
        #     #str_error += e.messages
        #     self.state = "tasks"
        #     self.menu1_tasks()
        #     self.task_id = False
        #     self._snd(self.menu1_tasks(), message = str_error)

    def handle_error(self, line):

        if line == KEY_CONFIRM:
            self.state=self.last_state
            self._snd (self.next_str)




    def _snd_error(self, str, message, custom_format=True):
        #import ipdb; ipdb.set_trace()
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
        clean = u'\n' * 25
        self.debug = True
        if self.debug==True:
            clean ='Menu: ' + str(self.last) + \
                    '\nState: ' + str(self.state) + \
                    '\nStep:' + str(self.step) + \
                    '\nTask id: ' + str(self.task_id) + \
                    ' \nOp id: ' + str(self.op_id)+\
                    clean
        self.last = '-'

        if self.user_id:
            cabecera = self.user_name
        else:
            cabecera=''
        delimiter = u"\n*******************************\n"
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
        if code in self.factory.users_codes:
            self._snd(u"Ya hay un usuario con ese codigo registrado\nIntroduzca codigo operador")
            return

        if self.get_odoo_connexion(code):
            self.state = "tasks"
            self.menu1_tasks()
            return
        else:
            self._snd(u"No se pudo establecer la conexion.\nIntroduzca codigo de nuevo")

    def get_str_menu1(self, paused = False):
        """
        Método que devuelve el menú principal
        """
        #import ipdb; ipdb.set_trace()
        self.last = "get_str_menu1"
        if not self.tasks:
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
        if self.show_keys:
            keys = "<" + KEY_VOLVER +"> Salir"
        menu_str += delimiter + keys
        return menu_str

    def handle_menu1(self, line):
        """
        Manejador del estado menu1. Para tareas muestra un mení con las
        cámaras a seleccionar, y cambia al siguiente estado si la ubicación es
        correcta.
        """
        #import ipdb; ipdb.set_trace()
        self.step = 0
        print "handle_menu" + str(line)
        if line not in ["0", "1", "2", "3", "4", "5"] and line != KEY_VOLVER:
            str_error = u"La opcion %s no es valida.\nReintentar:\n" % line
            self.state='menu1'
            self._snd(str_error + self.get_str_menu1(True))
        elif line =="0_":
            self.state = "register"
            self.factory.users_codes.remove(self.code)
            self.user_id = False
            self.code = False
            self.handle_register('0')
        elif line == "1":
            self.state = "machines"
            self.type = 'ubication'
            menu_str = self.get_machines_menu(self.type)
            self._snd(menu_str)
        elif line == "2":
            self.state = "machines"
            self.type = "reposition"
            menu_str = self.get_machines_menu(self.type)
            self._snd(menu_str)
        elif line == "3":
            self.state = 'machines'
            self.type = 'picking'
            menu_str = self.get_machines_menu(self.type)
            self._snd(menu_str)
        elif line == "4":
            self.state = 'manual_transfer'
            self.vals = VALS_MANUAL
            menu_str = self.get_manual_menu()
            self._snd(menu_str)
        elif line == "0":
            self.state = 'tasks'
            menu_str = self.get_str_menu_task()
            self._snd(menu_str)
        elif line == KEY_VOLVER:
            self.state = 'register'
            self.user_id = False
            self.user_name =""
            self.connectionLost(u"Sesion Cerrada\nIntroduce código para iniciar\n")
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


    def check_task(self):
        #buscamos tareas asignadas al self.user_id
        #import ipdb; ipdb.set_trace()
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
        #import ipdb; ipdb.set_trace()

        self.last = "get_str_menu_task"

        header = "Tareas Asignadas:\n"
        delimiter = "********************\n"
        strg = header

        task_data_not_paused = False
        paused_ok = False
        run_ok = False
        #Iniciamos taraas activas
        self.task_id = False
        self.active_task = False
        self.op_id = False
        self.active_op = False
        if not self.tasks:
            self.check_task()

        #esto saca todo el texto de las tareas,
        #Si hay una en activo, queda para el final
        strg_data = ''
        strg_data_not_paused =''
        for task_ in self.tasks:
            task = self.tasks[task_]
            data =  task_ + " -> " + task['ref'] \
                    + '(' + str(task['ops']) + ' op)\n'
            if task['paused']:
                paused_ok = True
                strg_data += data
            else:
                run_ok=True
                strg_data_not_paused += self.inverse(data)
                self.type = task['type']
                self.task_id = task['id']
                self.active_task = task_

        strg += strg_data_not_paused + strg_data
        if not self.tasks:
            strg += "\n NO HAY TAREAS"

        #Miramo las teclas que necesitamos
        #Pause /Run tasks
        keys=''
        if run_ok:
            keys +="<F2> Pausar"
        if paused_ok:
            keys +="<F5> Run"

        keys +="\n<" + KEY_VOLVER + " > Atras"
        if self.show_keys:
            strg += keys
        return strg

    def handle_tasks(self, line='0', confirm = False):
        #import ipdb; ipdb.set_trace()
        line_in_keys = False
        if line == "" or not line:
            line="0"

        if line in self.tasks.keys():
            self.type = self.tasks[line]['type'] or 'ubication'
            self.task_id = self.tasks[line]['id']
            self.active_task = line
            line_in_keys = True

        #Ponemso una tara en pausa, la ponemos en RUN
        if line == KEY_RUN:
            self.ops = False
            if len(self.tasks)==1:
                try:
                    res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                                     self.tasks['0']['id'], False)
                    self.check_task()
                    message = u"Ok"
                except Exception, e:
                    message = u"Error de tarea"
                self._snd(self.get_str_menu_task(), message)
                return

        if line[1:3] == KEY_RUN:
            self.ops = False
            k = line[0:1]
            if k in self.tasks.keys():
                    try:
                        res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                                         self.tasks[k]['id'], False)
                        self.check_task()
                        message = "Ok"
                    except Exception, e:
                        message = "Error de tarea(%s)"%k
                        self.state = "tasks"
                    self._snd(self.get_str_menu_task(), message)
                    return

        #Ponemso una tarea en run , la ponemos en PAUSE. No hace falta preguntar cual
        #es la que tiene self.task_id
        if line == KEY_PAUSE:
            self.ops = False
            if self.task_id:
                try:
                    res = self.factory.odoo_con.set_task_pause_state(self.user_id,
                                                                     self.tasks[self.active_task]['id'], True)
                    self.check_task()
                    message = "Ok"
                except Exception, e:
                    message = "Error de tarea(%s)"%k
                    self.state = "tasks"
                self._snd(self.get_str_menu_task(), message)
                return

        #volvemos a menu principal
        if line == KEY_VOLVER:
            self.ops = False
            self.last_state = self.state
            self.state = "menu1"
            self._snd(self.get_str_menu1())
            return

        elif line == KEY_CANCEL:
            self.ops = False
            self._snd(self.get_str_menu_task())
            return

        elif line == KEY_CONFIRM and self.task_id and self.ops and confirm==False:
            task_ops_finish = True
            for op in self.ops:
                if not self.ops[op]['PROCESADO']:
                    task_ops_finish = False

            if task_ops_finish:
                message = "Todas las operaciones OK\nConfirmar tarea finalizada : \n"\
                          + self.tasks[self.active_task]['ref']\
                          + "\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
            else :
                message = "Falta operaciones\nConfirmar tarea finalizada\n de todas formas: \n"\
                          + self.tasks[self.active_task]['ref']\
                          + "\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
            #llamamos a confirmar tarea
            self.last_state= "tasks" #queremos que vuelva a tareas
            self.state=10
            self.state = "yes_no"
            self._snd(message)
            return

        elif line == KEY_CONFIRM and confirm == True:
            ok = self.factory.odoo_con.finish_task(self.user_id, self.task_id)
            ok_task = self.check_task()
            self.ops = False
            self.step=0
            if self.task_id:
                self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
                self.step=0
                self.state ='tasks'
                self._snd(self.get_str_menu_task())
            else:
                self.state ='menu1'
                self._snd(self.get_str_menu1())
            return

        elif line == KEY_YES and self.step==10:
            self.handle_tasks(line=KEY_CONFIRM, confirm= True)
            return
        elif line == KEY_NO and self.step==10:
            self.handle_tasks(line=KEY_CANCEL)
            self.step=0
            return



        else:
            #
            if line_in_keys:
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
        #import ipdb; ipdb.set_trace()
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
        #import ipdb; ipdb.set_trace()
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
        #import ipdb; ipdb.set_trace()
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
            self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
        header = "Operaciones en %s)\n"%str(self.tasks[self.active_task]['ref'])
        return self.get_str(self.ops, header)

    def handle_list_repo_ops(self, line, confirm=False):

        #import ipdb; ipdb.set_trace()
        # Manejador de lista de operaciones de ubicacion

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if not order_line:
            if line == KEY_CONFIRM:
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM, confirm=False)
                return
            if line == KEY_VOLVER:
                #import ipdb; ipdb.set_trace()
                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM <=len(self.ops):
                    self.num_order_list_ops += MAX_NUM
                self._snd(self.get_str_list_repo_ops())
                return
            if line == KEY_PREV:
                self.num_order_list_ops -= MAX_NUM
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self._snd(self.get_str_list_repo_ops())
                return
            if line in self.ops.keys():
                self.step=0
                self.handle_list_repo_ops("PK%s"%self.ops[line]['paquete_id'])
                return
            if line=='0' or line =='':
                self.step=0
                self.last_state = "list_repo_ops"
                self.state = 'form_repo_ops'
                self.handle_form_repo_ops(line="0")
                return
            message ="\nNo te entiendo"
            self._snd(self.get_str_list_repo_ops(), message)
            return

        if order_line == PRE_PACK:
           #Es un paquete
           for op_ in self.ops:
                op = self.ops[op_]
                if op['PAQUETE'] == line or op['paquete_id'] == self.int_(line):
                    self.last_state = "list_repo_ops"
                    self.active_op = self.int_(op_)
                    self.op_id = op['ID']
                    self.step=1
                    self.state = 'form_repo_ops'
                    self.handle_form_repo_ops(order_line + line)
                    return
                message = u'\nPaquete no Válido'
                self._snd(self.get_str_list_repo_ops(), message)
                return

    def get_str_form_repo_ops(self):

       #import ipdb; ipdb.set_trace()
        self.last = "get_str_form_ops"

        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
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
            self.vals["paquete"]=op_['PAQUETE']
            self.vals["destino"]=op_['DESTINO']

        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")

        header = "Tarea: %s OP: %s\nNo vistas %s Ok %s\n"\
                 %(self.tasks[self.active_task]['ref'],
                   str(self.op_id), str(num_ops-not_vis), str(not_proc))

        if self.tasks[self.active_task]['paused'] == True:
            header = self.inverse(header)

        # header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
        #          + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "***************************\n"
        strg = header

        k = u"PRODUCTO"
        k_ = u"PROD"
        strg += k_ + u":" + op_[k] + "\n"

        k = u"CANTIDAD"
        k_= u'CANT'
        strg += k_ + u":" + str(op_[k]) + " " + op_['uom'] + "\n"

        k = u"LOTE"
        k_ = u'LOT'
        strg += k_ + u":" + op_[k] + "\n"

        k = u"PAQUETE"
        k_ = u'PACK'
        op_ok = True
        if not self.vals['paquete']:
            strg +=self.inverse(k_ +   u"(" + str(op_['paquete_id']) + "):" + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k_ +   u"(" + str(op_['paquete_id']) + "):" + str(op_[k]) +  "\n"

        k = u"ORIGEN"
        k_ = u'ORIG'
        if not self.vals['origen']:
            strg += self.inverse(k_ +   u"(" + str(op_['origen_id']) + "):" + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k_ +   u"(" + str(op_['origen_id']) + "):" + str(op_[k]) +  "\n"


        k = u"DESTINO"
        k_=u'DEST'
        strg +=k_ +   u"(" + str(op_['destino_id']) + "):" + str(op_[k]) +  "\n"


        k = u"PROCESADO"
        if op_[k]:
            str_proc =u'SI'
        else:
            str_proc = self.inverse(u'NO')


        strg += k + u":" + str_proc + "\n"

        keys = ""
        if op_['PROCESADO']:
            keys += "<" + KEY_CANCEL +"> Cancel OP"
        keys += "<" + KEY_VOLVER + "> Atras"
        if self.show_keys:
            strg += delimiter + keys
        return strg


    def handle_form_repo_ops(self, line, confirm=False):

        #import ipdb; ipdb.set_trace()
        order_line = line[0:2]

        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if line == KEY_VOLVER:
            #import ipdb; ipdb.set_trace()
            if self.last_state == 'list_repo_ops':
                self.state = 'list_repo_ops'
                self.reset_vals()
                self.step =0
                self._snd(self.get_str_list_repo_ops())
                return
            self.last_state = self.state
            self.state = "tasks"
            self.reset_vals()
            self.step =0
            self._snd(self.get_str_menu_task())
            return

        #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
        if line == KEY_NEXT:
            import ipdb; ipdb.set_trace()
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
            self._snd(self.get_str_form_repo_ops() + u'\nTarea en pausa')
            return

        #Si la operación está procesada, solo permito Cancelar el Proceso
        if line == KEY_CANCEL:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.ops = self.factory.odoo_con.get_ops(self.task_id)
            self.reset_vals()
            self.step =0
            self._snd(self.get_str_form_repo_ops())
            return

        #Si está procesada, no pasa de este if
        if self.ops[str(self.active_op)]['PROCESADO']== True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_repo_ops() + u'\nOpción no Válida')
            return

        #paso 0 solo permito introducit Paquete
        if self.step == 0 or self.step==1:
            #import ipdb; ipdb.set_trace()
            if order_line == PRE_PACK:

                if line == self.ops[str(self.active_op)]['PAQUETE'] or\
                    self.int_(line) == self.ops[str(self.active_op)]['paquete_id']:
                    self.vals ['paquete'] = self.ops[str(self.active_op)]['paquete_id']
                    self.step = 1
                    message =u"\nEscanea Origen"
                    try:
                        self._snd(self.get_str_form_repo_ops() + message)
                    except:
                        import ipdb; ipdb.set_trace()
                        ee=1
                    return
                else:
                    self.reset_vals()
                    self.step = 0
                    message = u'\nPaquete no Válido'
                    self._snd(self.get_str_form_repo_ops() + message)
                    return

        #import ipdb; ipdb.set_trace()
        if self.step == 1:
            if order_line == PRE_LOC:
                #Lo que leo es una ubicación
                #Si lo que leo es la ubicación que me da la tarea, perfecto paso a step 3
                if line == str(self.ops[str(self.active_op)]['origen_id']) or\
                    line == str(self.ops[str(self.active_op)]['ORIGEN']):
                    self.vals['origen'] = str(self.ops[str(self.active_op)]['origen_id'])
                    self.vals['nuevo_destino'] = self.vals['origen']
                    self.step = 3
                    message =u"\nConfirma Operación\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
                    self._snd(self.get_str_form_repo_ops() + message)
                    return

                if line != str(self.ops[str(self.active_op)]['origen_id']):
                    if not self.int_(line) in self.factory.odoo_con.get_locations_ids():
                        self.step=1
                        message =u"\nError. Escanea Ubicación"
                        self._snd(self.get_str_form_repo_ops() + message)
                        return
                    self.vals['nuevo_destino'] = line
                    self.step = 2
                    message =u"\nConfirma Nueva Ubicación"
                    self._snd(self.get_str_form_repo_ops() + message)
                    return


        if self.step == 2:
            if order_line == PRE_LOC:
                if line == self.vals['nuevo_destino']:
                    #Lo cambiamos en la ubicación
                    res = self.factory.odoo_con.change_packet_op(self.user_id, self.op_id, 'location_id', self.int_(line))
                    self.vals['origen'] = line
                    self.vals['nuevo_destino'] = line
                    self.ops = self.factory.odoo_con.get_ops(self.task_id)
                    self.step = 3
                    message =u"\nConfirma Operación\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
                    self._snd(self.get_str_form_repo_ops() + message)
                    return
                else:
                    self.step= 1
                    message =u"\nError. Escanea Ubicación"
                    self._snd(self.get_str_form_repo_ops(), message)
                    return

        if self.step ==3:
            #si llegamos aquí, tenemos que confirmar

            if line == KEY_YES:
                new_state = True
            elif line == KEY_NO:
                new_state = False
            else:
                self.step= 1
                message =u"\nError. Escanea Ubicación"
                self._snd(self.get_str_form_repo_ops(), message)
                return

            print "Enviando " + str(new_state) + " para id :" +str(self.op_id)
            task_ops_finish = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, new_state)
            self.ops = self.factory.odoo_con.get_ops(self.task_id)
            #task_ops_finish es que están todas finalizadas.

            if not task_ops_finish:
                #llamamos a confirmar tarea
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM)
                return
            else:
                self.step = 0
                message = u"\nProcesada OK"
                self.handle_form_repo_ops(KEY_NEXT)
                return

        if self.step==0:
            message =u"\nEscanea Paquete"
            self._snd(self.get_str_form_repo_ops(), message)
            return

        #Si llega aquí, hay un error no localizado.
        self.reset_all_vals(self.vals)
        self.step = 1
        message = u"\nNo te entiendo"
        self._snd(self.get_str_form_repo_ops(), message)
        return

    def get_str_list_ops(self):
        self.last = "get_str_list_ops"
        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
        header = "Operaciones en %s\n"%self.tasks[self.active_task]['ref']
        return self.get_str(self.ops, header)

    def get_str_list_waves(self):
        self.last = "get_str_list_waves"
        #import ipdb; ipdb.set_trace()
        # En vez de operaciones, sacamos wave_reports
        self.active_wave = 1
        self.waves = self.factory.odoo_con.get_wave_reports_from_task(self.task_id, self.type)
        header = "Picks(%s)\n" %self.task_id
        return self.get_str(self.waves , header)

    def get_str_list_wave_ops(self):
        self.last = "get_str_list_wave_ops"
        data_ = self.factory.odoo_con.get_ops(self.wave_id, self.type)
        header = "Ops en pick:(%s)\n"%str(self.tasks[self.active_task]['wave_id'])
        return self.get_str(data_, header)

    def get_str(self, data_, header =''):
        #import ipdb; ipdb.set_trace()
        #Saca una lista de operaciones o picks
        if self.type=='ubication':
            not_vis = 0
            not_proc = 0
            for op in data_:
                op__=data_[op]
                if op__['VISITED']:
                    not_vis += 1
                if op__['PROCESADO']:
                    not_proc += 1
            header1=''
            header1 += "Total %s Vistos %s Ok %s\n"%(len(data_), str(not_vis), str(not_proc))

        delimiter = "********************\n"
        strg = header #+ delimiter
        #lo que mostramos como a continuación de paquete
        #depende de si es ubicaion o picking
        if self.type == 'ubication':
            after_PAQUETE = 'DESTINO'
        else:
            after_PAQUETE = 'ORIGEN'


        for k in range(self.num_order_list_ops, self.num_order_list_ops +MAX_NUM):
            k_ = str(k)
            if k_ in data_:
                if k <= len(data_):
                    k_ = str(k)
                    op = k_ + '>'

                    if not data_[k_]['PROCESADO']:
                        op = self.inverse(op)
                    op +=data_[k_]['PAQUETE'] + ': ' + data_[k_][after_PAQUETE] + '\n'
                    strg += op

        keys =''
        if self.num_order_list_ops > 1:
            keys += "<%s>"%KEY_PREV
        if len(data_)-self.num_order_list_ops >=MAX_NUM:
            keys += "<%s>"%KEY_NEXT

        keys += "<%s>"%KEY_VOLVER
        if self.tasks[self.active_task]['type']=="ubication":
            keys += "<%s>Finalizar Tarea"%KEY_CONFIRM

        if self.show_keys:
            strg += delimiter + keys
        return strg

    def handle_list_waves(self, line, confirm):

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
                #marcamos la tarea como finalizada
                #llamamos a finish_partial_task de stock_task
                ok = self.factory.odoo_con.finish_task(self.user_id, self.task_id)
                self.step=0
                self.last_state = "list_waves"
                self.state ='tasks'
                self.waves=False
                self.ops = False
                self.task_id=False
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return


            if line in self.waves.keys():
                #seleccionamos un elemento del menu
                #aqui tengo que abrir list_ops
                self.last_state = "list_waves"
                self.active_op = self.int_(line)
                self.active_wave = self.int_(line)
                self.step =0
                self.wave_id = self.waves[line]['ID']
                self.state = 'form_wave'
                self._snd(self.get_str_form_wave(), '')
                return

            message ="\nNo te entiendo"
            self._snd(self.get_str_list_waves(), message)
            return

        if order_line == PRE_PACK:
            for op_ in self.waves:
                op = self.waves[op_]
                if op['PAQUETE'] == line or op['paquete_id'] == self.int_(line):
                    #es un paquete de la lista de paquetes de esta tarea
                    self.last_state = "list_waves"
                    self.num_order_list_ops=0
                    self.step=0
                    self.handle_form_wave(order_line + line)
                    return

        if order_line == PRE_LOC:
            for op_ in self.waves:
                op = self.waves[op_]
                if op['origen'] == line or op['origen_id'] == self.int_(line) and self.step == 0:
                    #es un paquete de la lista de paquetes de esta tarea
                    self.last_state = "list_waves"
                    self.step=1
                    self.num_order_list_ops=0
                    self.handle_form_wave(order_line + line)
                    return

        message = u'\nPaquete no Válido'
        self._snd(self.get_str_list_waves(), message)
        return

    def handle_list_wave_ops(self, line, confirm):

        #import ipdb; ipdb.set_trace()
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if not order_line:
            if line == KEY_VOLVER:
                #import ipdb; ipdb.set_trace()
                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
                return
            #NOS MOVEMOS POR LOS FORMULARIOS DE OPERACIONES
            if line == KEY_NEXT:
                if self.num_order_list_ops + MAX_NUM <=len(self.ops):
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
                #import ipdb; ipdb.set_trace()
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
        #import ipdb; ipdb.set_trace()



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

    def handle_form_wave(self, line, confirm=False):

        #import ipdb; ipdb.set_trace()#import ipdb; ipdb.set_trace()
        #lo modifico para
        #step = 0: Espera localizacióny pasa a step 1
        #step 1, espera pack , si ok pasa a step9

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        wave_= self.waves[str(self.active_wave)]
        if order_line == PRE_PACK and self.step in [0,1,2]:
           #Es un paquete
            for op_ in self.waves:
                op = self.waves[op_]
                if op['PAQUETE'] == line or op['paquete_id'] == self.int_(line):
                    #es un paquete de la lista de paquetes de esta tarea
                    self.last_state = "list_waves"
                    self.active_op = op_
                    self.wave_id = op['ID']
                    self.state = 'form_wave'
                    self.qty_calc = []
                    self.new_uos_qty=0.00
                    self.new_uom_qty=0.00
                    self.product = self.factory.odoo_con.get_product_gun_complete_info(op['product_id'])
                    self.fc = self.factory.odoo_con.conv_units_from_gun(op['product_id'], op['uom_id'], op['uos_id'])
                    self.step = 1
                    self._snd(self.get_str_form_wave(), '')
                    return
                else:
                    message = u'\nPaquete no Válido'
                    self._snd(self.get_str_form_wave(), message)
                    return
        if order_line == PRE_LOC and self.step in [0,1,2]:
            for op_ in self.waves:
                op = self.waves[op_]
                if op['origen'] == line or op['origen_id'] == self.int_(line):
                    #es un paquete de la lista de paquetes de esta tarea
                    self.last_state = "list_waves"
                    self.active_op = op_
                    self.wave_id = op['ID']
                    self.state = 'form_wave'
                    if self.step == 1:
                        self.step=2
                    self._snd(self.get_str_form_wave(), '')
                    return
                else:
                    message = u'\nOrigen no Válido'
                    self._snd(self.get_str_form_wave(), message)
                    return




        if line in [KEY_CONFIRM, KEY_CANCEL, KEY_NEXT, KEY_PREV, KEY_QTY,KEY_VOLVER]:

            if line == KEY_CANCEL:
                if self.step>2:
                    self.handler_form_wave('PKL' +  self.waves[str(self.active_wave)]['paquete_id'])
                    return

                if self.step<=2:
                    self.step= 0
                    self._snd(self.get_str_form_wave(), '')
                    return

            if line == KEY_NEXT:
                if self.num_order_list_ops < len(self.waves):
                    self.num_order_list_ops += 1
                self.step=0

                self._snd(self.get_str_wave_form())
                return

            if line == KEY_PREV:
                self.num_order_list_ops -= 1
                if self.num_order_list_ops <1:
                    self.num_order_list_ops=1
                self.step=0
                self._snd(self.get_str_form_wave())
                return

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
                    self.step =1
                    self.qty_calc = []
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.state in [3,5,5,6,7,8,9]:
                    self.step =2
                    self.new_uos_qty=0
                    self.new_uom_qty=0
                    self.qty_calc = []
                    self._snd(self.get_str_form_wave(), '')
                    return

            if line==KEY_CONFIRM:
                if self.step ==2 :
                    self.new_uos_qty=self.waves[str(self.active_wave)]['uos_qty']
                    self.new_uom_qty=self.waves[str(self.active_wave)]['CANTIDAD']
                    self.step = 10
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==3:
                    self.step = 5
                    for qty in self.qty_calc:
                        self.new_uom_qty= self.int_(qty)
                    self.new_uos_qty = len(self.qty_calc)
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step == 4:
                    self.step = 6
                    for qty in self.qty_calc:
                        self.new_uos_qty+=qty
                    self.new_uom_qty+= len(self.qty_calc)
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==5:
                    self.step = 10
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
                    self.waves[str(self.active_wave)]['uos_qty']=self.new_uos_qty
                    self.waves[str(self.active_wave)]['CANTIDAD']=self.new_uom_qty
                    task_ops_finish = self.factory.odoo_con.set_wave_ops_values(self.wave_id, self.user_id , 'to_process', False)
                    self.step = 0
                    self.state = "list_waves"
                    self._snd(self.get_str_list_waves(), 'Wave Finish')
                    return

            if line ==KEY_NO_REALIZADA:
                if self.step == 10:
                    wave_id = 11
                    vals={
                        'to_revised': True,
                        'uos_qty': self.new_uos_qty,
                        'uom_qty': self.new_uom_qty
                    }
                    wave_id_to_revised =  self.factory.odoo_con.set_wave_reports_values(self.wave_id, self.user_id, vals, True)
                    self.step = 0
                    self.state = "list_waves"
                    self._snd(self.get_str_list_waves(), 'Wave Finish. To Revised')
                    return


            if line == KEY_QTY:
                if self.step ==2 :
                    if self.product['var_coeff_un_id'] or self.product['var_coeff_ca_id']:
                        self.step = 3
                    else:
                        self.step = 8
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step==3:
                    self.step = 4
                    self.new_uos_qty=0
                    self.new_uom_qty=0
                    self.qty_cal=[]
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step==4:
                    self.step=3
                    self.new_uos_qty=0
                    self.new_uom_qty=0
                    self.qty_cal=[]
                    self._snd(self.get_str_form_wave(), '')
                    return

                if self.step ==8:
                    self.step+=9
                    self._snd(self.get_str_form_wave(), '')
                    return
                if self.step ==9 :
                    self.step-=8
                self._snd(self.get_str_form_wave(), '')
                return

        line_is_number=True
        if line_is_number== True:
            line_ = self.float_(line)
            if self.step in [3,4]:

                if line_>0:
                    self.qty_calc.append(line_)
                else:
                    try:
                        self.qty_calc.remove(line_*-1)
                    except:
                        res = False
                self._snd(self.get_str_form_wave(), '')
                return

            if self.step==5:
                self.new_uos_qty = line_
                self.step=10
                self._snd(self.get_str_form_wave(), '')
                return

            if self.step==6:
                self.new_uom_qty = line_
                self.step=10
                self._snd(self.get_str_form_wave(), '')
                return


            if self.step == 8:
                line_ = self.float_(line)
                self.new_uom_qty = line_
                self.new_uos_qty = round(line_ * self.fc, 2)
                self._snd(self.get_str_form_wave(), '')
                return

            if self.step == 9:
                line_ = self.float_(line)
                self.new_uos_qty = line_
                self.new_uom_qty = round(line_ / self.fc, 2)
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
        self.product = self.factory.odoo_con.get_product_gun_complete_info(wave_['product_id'])
        header = "Pick(%s)\n"%str(wave_['ID'])

        menu_str = wave_['PRODUCTO'] + '(%s)\n'%wave_['product_id']
        menu_str += wave_['EAN'] + ' ' + wave_['LOTE'] + '\n'

        if self.step in[0] :
            menu_str+= self.inverse(wave_['PAQUETE'] + '\n')
        else:
            menu_str += wave_['PAQUETE'] +'\n'

        if self.step in [1]:
            menu_str+= self.inverse(wave_['ORIGEN'] + '\n')
        else:
            menu_str += wave_['ORIGEN'] +'\n'

        cantidad=''
        cantidad_uos =''
        message =''

        if self.step <= 2:
            cantidad += str(wave_['CANTIDAD']) + ' ' + wave_['uom']  + '\n'
            cantidad_uos += str(wave_['uos_qty']) + ' ' + wave_['uos'] + '\n'

        if self.step ==2:
             message = u"%s Ok %s Cantidades\n"%(KEY_CONFIRM, KEY_QTY)
             message = self.inverse(message)

        if self.step == 3:
            qty_calc = 0
            for qty in self.qty_calc:
                qty_calc+=qty
            len_qty = len(self.qty_calc)
            cantidad += '(%s) %s %s\n'%(qty_calc, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(len_qty, wave_['uos_qty'], wave_['uos'])
            cantidad = self.inverse(cantidad)
            message = KEY_QTY + " Ok uom\n"

        if self.step == 4:
            qty_calc = 0
            for qty in self.qty_calc:
                qty_calc+=qty
            len_qty = len(self.qty_calc)
            cantidad += '(%s) %s %s\n'%(len_qty, str(wave_['CANTIDAD']), wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(qty_calc, str(wave_['uos_qty']), wave_['uos'])
            cantidad_uos = self.inverse(cantidad_uos)
            message = KEY_QTY + " Ok uos\n"

        if self.step == 5:
            cantidad += '(%s) %s %s\n'%(self.new_uom_qty, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(self.new_uos_qty, wave_['uos_qty'], wave_['uos'])
            cantidad_uos = self.inverse(cantidad_uos)
            message = "%s Ok Uos, o intro nuevo\n"%(KEY_CONFIRM)

        if self.step == 6:
            cantidad += '(%s) %s %s\n'%(self.new_uom_qty, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(self.new_uos_qty, wave_['uos_qty'], wave_['uos'])
            cantidad = self.inverse(cantidad)
            message = "%s Ok Uom, o intro nuevo\n"%(KEY_CONFIRM)


        if self.step == 8:
            #Aqui es peso fijo, introducimos cantidad para uom
            cantidad += '(%s) %s %s\n'%(self.new_uom_qty, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(self.new_uos_qty, wave_['uos_qty'], wave_['uos'])
            message = KEY_QTY + u"cambiar a %s o intro %s\n"%(wave_['uos'], wave_['uom'])
            cantidad = self.inverse(cantidad)

        if self.step == 9:
            cantidad += '(%s) %s %s\n'%(self.new_uom_qty, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(self.new_uos_qty, wave_['uos_qty'], wave_['uos'])
            message = KEY_QTY + u"cambiar a %s o intro %s\n"%(wave_['uom'], wave_['uos'])
            cantidad_uos = self.inverse(cantidad_uos)

        if self.step == 10:
            cantidad += '(%s) %s %s\n'%(self.new_uom_qty, wave_['CANTIDAD'], wave_['uom'])
            cantidad_uos += '(%s) %s %s\n'%(self.new_uos_qty, wave_['uos_qty'], wave_['uos'])
            message =u"%s Confirmar Operación\n"%KEY_CONFIRM
            message = self.inverse(message)

        menu_str += cantidad + cantidad_uos + message
        keys =''
        keys += KEY_VOLVER + u' Atrás '  + KEY_WAVE_OPS + u' Ops'
        menu_str = header + menu_str + keys
        return menu_str

    def handle_list_ubi_ops(self, line, confirm=False):
        #import ipdb; ipdb.set_trace()
        # Manejador de lista de operaciones de ubicacion

        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if not order_line:
            if line == KEY_CONFIRM:
                self.state="tasks"
                self.step=0
                self.handle_tasks(line=KEY_CONFIRM, confirm=False)
                return


            if line == KEY_VOLVER:
                #import ipdb; ipdb.set_trace()
                self.last_state = self.state
                self.state = "tasks"
                self.reset_vals()
                self._snd(self.get_str_menu_task())
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
                self.handle_form_ubi_ops(order_line + line)
                return

            message ="\nNo te entiendo"
            self._snd(self.get_str_list_ops(), message)
            return

        if order_line == PRE_PACK:
           #Es un paquete
           for op_ in self.ops:
                op = self.ops[op_]
                if op['PAQUETE'] == line or op['paquete_id'] == self.int_(line):
                    self.last_state = "list_ops"
                    self.active_op = self.int_(op_)
                    self.op_id = op['ID']
                    self.state = 'form_ops'
                    self._snd(self.get_str_form_ops(), '')
                    return
                else:
                    message = u'\nPaquete no Válido'
                    self._snd(self.get_str_list_ops(), message)

    def get_str_form_ops(self):
        #import ipdb; ipdb.set_trace()
        self.last = "get_str_form_ops"

        if not self.ops:
            self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
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
            self.vals["paquete"]=op_['PAQUETE']
            self.vals["destino"]=op_['DESTINO']

        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")

        header = "Tarea: %s OP: %s\nNo vistas %s Ok %s\n"\
                 %(self.tasks[self.active_task]['ref'],
                   str(self.op_id), str(num_ops-not_vis), str(not_proc))

        if self.tasks[self.active_task]['paused'] == True:
            header = self.inverse(header)

        # header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
        #          + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "***************************\n"
        strg = header

        k = u"PRODUCTO"
        k_ = u"PROD"
        strg += k_ + u":" + op_[k] + "\n"

        k = u"CANTIDAD"
        k_= u'CANT'
        strg += k_ + u":" + str(op_[k]) + " " + op_['uom'] + "\n"

        k = u"LOTE"
        k_ = u'LOT'
        strg += k_ + u":" + op_[k] + "\n"

        k = u"PAQUETE"
        k_ = u'PACK'
        op_ok = True
        if not self.vals['paquete']:
            strg +=self.inverse(k_ +   u"(" + str(op_['paquete_id']) + "):" + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k_ +   u"(" + str(op_['paquete_id']) + "):" + str(op_[k]) +  "\n"

        k = u"ORIGEN"
        k_ = u'ORIG'
        strg += k_ + u"(" + str(op_['origen_id']) + "):" + str(op_[k]) +   "\n"

        k = u"DESTINO"
        k_=u'DEST'
        if not self.vals['destino']:
            strg += self.inverse(k_ +   u"(" + str(op_['destino_id']) + "):" + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k_ +   u"(" + str(op_['destino_id']) + "):" + str(op_[k]) +  "\n"


        k = u"PROCESADO"
        if op_[k]:
            str_proc =u'SI'
        else:
            str_proc = self.inverse(u'NO')


        strg += k + u":" + str_proc + "\n"

        keys = ""
        if op_['PROCESADO']:
            keys += "<" + KEY_CANCEL +"> Cancel OP"
        keys += "<" + KEY_VOLVER + "> Atras"
        if self.show_keys:
            strg += delimiter + keys
        return strg


    def handle_ops_ubi(self, line='0', confirm = False):
        # aqui veremos line en la pantalla de tasks
        #
        # used_keys = "0123456789." + KEY_VOLVER + KEY_NEXT + KEY_PREV + KEY_FINISH + KEY_CONFIRM_QTY + KEY_CHANGE_QTY + KEY_CANCEL
        import ipdb; ipdb.set_trace()
        print "handle_ops_ubi" + str(line)
        self.op_id = self.ops[str(self.active_op)]['ID']
        message =''

        if confirm == True and (line == KEY_YES or line == KEY_NO):
            #import ipdb; ipdb.set_trace()
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
                self._snd("Todas las operaciones OK\nConfirmar tarea finalizada : \n"
                          + "\nRef: " + str(self.task_id)
                          + "\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
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
            #import ipdb; ipdb.set_trace()
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
            #import ipdb; ipdb.set_trace()
            if self.tasks[self.active_task]['paused'] == False:
                self.last_state= self.state
                self.state = "yes_no"
                self._snd("Confirmar el movimiento : \n"
                          + "\nPaquete: " + self.vals ['paquete']
                          + "\nDestino: " + self.vals ['destino']
                          + "\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
                          )
            else:
                self._snd("Error: Tarea en pausa\n" + self.get_str_form_ops())

        elif line == KEY_DESTINO:
            self.menu_intro_destino
        elif line == KEY_QTY:
            self.menu_intro_qty
        elif line == KEY_ORIGEN:
            self.menu_intro_orien

        else:
            #si no está en pausa ni procesado podemos introduir paquete y destino
            #import ipdb; ipdb.set_trace()
            if self.tasks[self.active_task]['paused'] == False and self.ops[str(self.active_op)]['PROCESADO']!= True:
                if line == str(self.ops[str(self.active_op)]['paquete_id']) and (self.vals['paquete']==False):
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
                        self.ops = self.factory.odoo_con.get_ops(self.task_id, self.type)
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

    def get_manual_menu(self):
        #Menu de opciones de movimiento manual
        self.last = "get_str_manual_menu"
        if not self.state == 'manual_transfer':
            self.state='menu1'
            self._snd(self.get_str_menu1())
        print "get manual menu:"

        #import ipdb; ipdb.set_trace()
        header = u"Movimiento Manual:\n"
        delimiter = u"********************\n"
        menu_str = header
        if self.vals['package_id']!=False:
            menu_str+=u"Paquete:" + self.vals['package'] + u"\n"
        if self.package:
            for key_ in self.package.keys():
                package = self.package[key_]
                menu_str+=u'%s > %s %s\n'%(package['product'], package['quantity'], package['uom'])
        if self.vals['src_location_id']!=False:
            menu_str+=u"Origen:" + self.vals['src_location'] + u"\n"
        if self.vals['dest_location_id']!=False:
            menu_str+=u"Destino:" + self.vals['dest_location'] + u"\n"
            #menu_str+=u"Empaquetar:" + self.vals['do_pack'] + u"\n"

        if self.step==0:
            menu_str+= self.inverse(u"Paquete\n")
        if self.step==1:
            menu_str+= self.inverse(u"EAN, origen o teclea cantidad\n")
            if self.vals['src_location_id']!= False:
                menu_str += "<%s> Seguir ...\n"%KEY_CONFIRM
        if self.step==2:
            if not self.vals['src_location_id']:
                menu_str += "Escanea Origen\n"
            menu_str+= self.inverse(u"<%s> Destino ...\n")%(KEY_CONFIRM)
        if self.step==3:

            menu_str+= self.inverse(u"<%s> Destino ...\n")%(KEY_CONFIRM)
            #menu_str+= self.inverse(u"Cantidad (%s)\no <%s> Destino ...\n")%(self.vals['quantity'], KEY_CONFIRM)

        if self.step==5:
            menu_str+= self.inverse(u"destino Ó %s Confirma\n"%KEY_CONFIRM)
        if self.step==6:
            menu_str+= u"1 -> Sin Paquete\n2 -> Palet\n3 -> Caja\n" + self.inverse("<" + KEY_CONFIRM + u"> Conf Movimiento (Sin Paquete)\n")
        if self.step==7:
            menu_str += self.inverse("%s Confirma Movimiento\n"%KEY_CONFIRM)

        keys = "<" + KEY_VOLVER + "> Volver <" + KEY_CANCEL + "> Canc"
        if self.show_keys:
            menu_str +=keys

        return menu_str

    def handle_manual_menu(self, line):
        #menu eventos en manual
        #import ipdb; ipdb.set_trace()
        order_line = line[0:2]
        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False
        message =''
        if line == KEY_VOLVER:
            if self.step==0:
                self.state="menu1"
                self._snd(self.get_str_menu1())
                return
            if self.step==5:
                self.step -= 2
                self._snd(self.get_manual_menu())
                return
            if self.step==7:
                self.step -= 3
                self._snd(self.get_manual_menu())
                return
            if self.step==2:
                self.step -= 0
                self._snd(self.get_manual_menu())
                return
            if self.step==3:
                self.step -= 2
                self._snd(self.get_manual_menu())
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
                self._snd(self.get_manual_menu())
                return

        self.vals['exist'] = False
        vals = {}
        #Si en ccualquier momento meto un opaquete reinicio la operación
        if order_line == PRE_PACK:
            package_id = self.int_(line)
            vals = self.factory.odoo_con.get_pack_gun_info(self.user_id, package_id)
            busy = self.factory.odoo_con.get_user_packet_busy(self.user_id, package_id)

            if vals['exist'] == False:
                message = "\nNo encuentro el paquete"
                self._snd(self.get_manual_menu(), message)
                return
            else:
                self.vals={}
                for k in vals:
                    self.vals[k]=vals[k]
                self.package = self.factory.odoo_con.get_quant_pack_gun_info(self.user_id, package_id)
                if not self.package:
                    message = "\nNo encuentro el paquete"
                    self._snd(self.get_manual_menu(), message)
                    return
                self.step=2
                if busy:
                    message = "Ocupado en %s\n por \s"%(busy['ref'], busy['user'])
                self._snd(self.get_manual_menu(), message)
                return

        if self.step==2:
            if not self.vals['src_location_id']:
                line_id = self.int_(line)
                if order_line ==PRE_LOC:
                    vals =  self.factory.odoo_con.get_location_gun_info(self.user_id, line_id, 'src_')
                    if vals['exist']:
                        #es una localización
                        for k in vals:
                            self.vals[k]=vals[k]
                        self.step=2
                        self._snd(self.get_manual_menu())
                        return
                message = "\nNo te entiendo.\nNo Hay origen"
                self._snd(self.get_manual_menu(), message)
                return
            else:
                if line == KEY_CONFIRM:
                    self.step = 5
                    self._snd(self.get_manual_menu())
                    return

                line_id = self.int_(line)
                if order_line ==PRE_LOC:
                    vals =  self.factory.odoo_con.get_location_gun_info(self.user_id, line_id, 'dest_')
                    if vals['exist']:
                        #es una localización
                        for k in vals:
                            self.vals[k]=vals[k]
                        self.step=7
                        self._snd(self.get_manual_menu())
                        return

                if order_line == False:
                    #aqui solo vale cantidad
                    if line.isdigit():
                        self.vals['quantity'] = line
                        self.step=3
                        self._snd(self.get_manual_menu())
                        return

            message = "\nNo te entiendo"
            self._snd(self.get_manual_menu(), message)
            return

        if self.step==3:
            #Aqui solo vale Lote o Loca
            if line == KEY_CONFIRM:
                self.step = 5
                self._snd(self.get_manual_menu())
                return

            if line == KEY_VOLVER:
                self.step = 2
                self._snd(self.get_manual_menu())
                return

            if order_line == False:
                #aqui solo vale cantidad
                if line.isdigit():
                    self.vals['quantity'] = line
                    self.step=3
                    self._snd(self.get_manual_menu())
                    return

            message = "\nNo te entiendo"
            self._snd(self.get_manual_menu(), message)
            return

        if self.step==5:

            if line == KEY_CONFIRM and \
                    self.vals['dest_location_id'] != False:
                self.step = 7
                self._snd(self.get_manual_menu())
                return

            if order_line != False:
                line_id = self.int_(line)
                if order_line ==PRE_LOC:
                    vals =  self.factory.odoo_con.get_location_gun_info(self.user_id, line_id, 'dest_')
                    if vals['exist']:
                        #es una localización
                        for k in vals:
                            self.vals[k]=vals[k]
                        self.step=5
                        self._snd(self.get_manual_menu())
                        return

            message = "\nNo te entiendo"
            self._snd(self.get_manual_menu(), message)
            return


        if self.step==7:
            #import ipdb; ipdb.set_trace()
            if order_line == False:
                if line == KEY_CONFIRM:
                    self.vals['do_pack'] ='no_pack'
                    #confirmar tarea
                    self.vals['user_id']=self.user_id

                    try:
                        res = self.factory.odoo_con.do_manual_trasfer_from_gun(self.vals)

                    except Exception, e:
                        str_error = u"Error"
                        print (str_error + e.message)
                        message = str_error + e.message
                        self._snd(self.get_manual_menu(), message)
                        return

                    #import ipdb; ipdb.set_trace()
                    print "SE movio"
                    self.reset_all_vals(self.vals)
                    self.package = {}
                    self.step = 0
                    message = u"Mov Ok"
                    self._snd(self.get_manual_menu(), message)
                    return True

            elif line == KEY_CANCEL:
                self.reset_all_vals(self.vals)
                self.package = {}
                self.step = 0
                message = u"Cancelado"
                self._snd(self.get_manual_menu(), message)
                return True

        message = "\nNo te entiendo"
        self._snd(self.get_manual_menu(), message)
        return

    def handle_form_ubi_ops(self, line, confirm=False):
        #import ipdb; ipdb.set_trace()
        order_line = line[0:2]

        if order_line in (PRE_LOC, PRE_LOT, PRE_PACK, PRE_PROD):
            line = line [2:]
        else:
            order_line = False

        if line == KEY_VOLVER:
            #import ipdb; ipdb.set_trace()
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
            import ipdb; ipdb.set_trace()
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
            self._snd(self.get_str_form_ops() + u'\nTarea en pausa')
            return

        #Si la operación está procesada, solo permito Cancelar el Proceso
        if line == KEY_CANCEL:
            res = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, False)
            self.ops = self.factory.odoo_con.get_ops(self.task_id)
            self.reset_vals()
            self.step =0
            self._snd(self.get_str_form_ops())
            return

        #Si está procesada, no pasa de este if
        if self.ops[str(self.active_op)]['PROCESADO']== True:
            self.reset_vals()
            self.step = 0
            self._snd(self.get_str_form_ops() + u'\nOpción no Válida')
            return

        #paso 0 solo permito introducit Paquete
        if self.step == 0:
            #import ipdb; ipdb.set_trace()
            if order_line == PRE_PACK:
                if line == self.ops[str(self.active_op)]['PAQUETE'] or\
                    self.int_(line) == self.ops[str(self.active_op)]['paquete_id']:
                    self.vals ['paquete'] = self.ops[str(self.active_op)]['paquete_id']
                    self.step = 1
                    message =u"\nEscanea Ubicación"
                    try:
                        self._snd(self.get_str_form_ops() + message)
                    except:
                        import ipdb; ipdb.set_trace()
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
        #import ipdb; ipdb.set_trace()
        if self.step == 1:
            if order_line == PRE_LOC:
                #Lo que leo es una ubicación
                #Si lo que leo es la ubicación que me da la tarea, perfecto paso a step 3
                if line == str(self.ops[str(self.active_op)]['destino_id']) or\
                    line == str(self.ops[str(self.active_op)]['DESTINO']):
                    self.vals['destino'] = str(self.ops[str(self.active_op)]['destino_id'])
                    self.vals['nuevo_destino'] = self.vals['destino']
                    self.step = 3
                    message =u"\nConfirma Operación\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
                    self._snd(self.get_str_form_ops() + message)
                    return

                if line != str(self.ops[str(self.active_op)]['destino_id']):
                    if not self.int_(line) in self.factory.odoo_con.get_locations_ids():
                        self.step=1
                        message =u"\nError. Escanea Ubicación"
                        self._snd(self.get_str_form_ops() + message)
                        return
                    self.vals['nuevo_destino'] = line
                    self.step = 2
                    message =u"\nConfirma Nueva Ubicación"
                    self._snd(self.get_str_form_ops() + message)
                    return


        if self.step == 2:
            if order_line == PRE_LOC:
                if line == self.vals['nuevo_destino']:
                    #Lo cambiamos en la ubicación
                    res = self.factory.odoo_con.change_packet_op(self.user_id, self.op_id, 'location_dest_id', self.int_(line))
                    self.vals['destino'] = line
                    self.vals['nuevo_destino'] = line
                    self.ops = self.factory.odoo_con.get_ops(self.task_id)
                    self.step = 3
                    message =u"\nConfirma Operación\nSi <" + KEY_YES + "> NO <" + KEY_NO + ">"
                    self._snd(self.get_str_form_ops() + message)
                    return
                else:
                    self.step= 1
                    message =u"\nError. Escanea Ubicación"
                    self._snd(self.get_str_form_ops(), message)
                    return

        if self.step ==3:
            #si llegamos aquí, tenemos que confirmar

            if line == KEY_YES:
                new_state = True
            elif line == KEY_NO:
                new_state = False
            else:
                self.step= 1
                message =u"\nError. Escanea Ubicación"
                self._snd(self.get_str_form_ops(), message)
                return

            print "Enviando " + str(new_state) + " para id :" +str(self.op_id)
            task_ops_finish = self.factory.odoo_con.set_op_to_process(self.user_id, self.task_id, self.op_id, new_state)
            self.ops = self.factory.odoo_con.get_ops(self.task_id)
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
                self.handle_form_ubi_ops(KEY_NEXT)
                return
        #Si llega aquí, hay un error no localizado.
        self.reset_all_vals(self.vals)
        self.step = 1
        message = u"\nNo te entiendo"
        self._snd(self.get_str_form_ops(), message)
        return

    def get_str_menu_picking(self):
        d=1

    def handle_picking(self):
        e=1

    def handle_ops(self, line='0', confirm = False):
        #import ipdb; ipdb.set_trace()
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

    def get_cameras_menu(self):
        """
        Devuelve el menú con las cámaras disponibles
        """
        self.last = "get_cameras_menu"
        delimiter = "\n********************\n"
        #str_menu = "0 -> Volver\n"
        str_menu=""
        for key in self.factory.menu_cameras:
            key_ = str(key)
            intro = key_ + "-> "
            if key_ in self.camera_ids:
                intro = self.inverse(intro)
            str_menu += intro + self.factory.menu_cameras[key][1] + "\n"

        keys = "<" + KEY_VOLVER +"> Salir"
        if self.camera_ids:
            keys += "<" + KEY_CONFIRM +"> Buscar"

        str_menu+= keys
        return str_menu



    def handle_camera_selected(self, line):
        """
        Manejador de los estados location, reposition y picking, pide elegir
        cámara, en caso afirmativo trata de obtener una tarea ya existente
        o crearse una. Quizás halla que meter estado intermedio para que
        seleccione el modo manual de ubicar o el que te da las tareas.
        """
        print "handle_cmaera_selected" + str(line)
        next_state = {
            'ubication': 'scan_op',
            'reposition': 'scan_op_rep',
            'picking': 'scan_op_pick',
        }
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
            else:
                self.camera_ids.remove (line)
            self._snd(self.get_cameras_menu())
            return



        if line == KEY_CONFIRM and self.camera_ids:
            try:
                self.camera_id=[]
                for camera_ in self.camera_ids:
                    self.camera_id.append(self.factory.menu_cameras[self.int_(camera_)][0])
                import ipdb; ipdb.set_trace()
                date_planned=datetime.date.today().strftime("%Y-%m-%d")
                self.task_id = self.factory.odoo_con.get_task_of_type(self.user_id,self.camera_id, self.type, self.machine_id,date_planned)

            except Exception, e:
                import ipdb; ipdb.set_trace()
                print e.message
                #expt_str = e.message
                #str_error = expt_str + u"\nIntroduzca camara de nuevo\n"
                self._snd_error(self.get_cameras_menu(), e.message)
                return

            if self.task_id:
                self.factory.odoo_con.set_to_process(self.user_id, self.task_id)
                self.check_task()
                self.active_task='0'

                if self.type=='picking':
                    self.state ='list_waves'
                    self._snd(self.get_str_list_waves(), u'\nTarea Creada')
                else:
                    self.state = 'list_ops'
                    self._snd(self.get_str_list_ops(), u'\nTarea Creada')
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
        keys = "<" + KEY_VOLVER +"> Salir"
        str_menu += delimiter + keys
        return str_menu

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
                self.packet = line
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
        #import ipdb; ipdb.set_trace()
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
        self.ops = self.factory.odoo_con.get_ops(self.task_id)
        op_=self.ops[str(self.active_op)]
        #introc cantidad o confirma la prpopuesta con f1
        message = "Cantidad:/n <%s> para "%(KEY_CONFIRM, op_['CANTIDAD'])
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
        self.ops = self.factory.odoo_con.get_ops(self.task_id)
        op_=self.ops[str(self.active_op)]
        #introc cantidad o confirma la prpopuesta con f1
        message = "Origen :/n <" + KEY_CONFIRM + "> para " + str(op_['ORIGEN'])
        self.last_state = from_state
        self.state="intro_origen"
        self._snd(message)

    def handle_intro_origen(self, line):
        if line != KEY_CONFIRM:
            try:
                if self.task_id and self.op_id:
                    #tenemds que buscar el nnuev
                    origen_id =  {
                        "ORIGEN": float(line)}

                    origen_name = self.factory.odoo_con.get(origen_id)
                    self.vals["origen"] = origen_id
                    res = self.factory.odoo_con.change_value(self.user_id, self.op_id, "location_id", origen_id)

                    self.get_str_form_ops()
            except Exception, e:
                str_error = u"Error al introducir la cantidad: %s\n" % line
                self._snd(str_error + e.message)

    def handle_intro_destino(self, from_state, line):
        self.ops = self.factory.odoo_con.get_ops(self.task_id)
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
        if line == self.packet:
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
                        self.factory.odoo_con.finish_task(self.user_id, self.task_id)
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
        #import ipdb; ipdb.set_trace()
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
    def inverse(self, str):
        if str:
            res = COLORS_INV + str + COLORS_0
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
        res =0
        try:
            res =int(str)
        except:
            res =0
        return res

    def float_(self, str):
        res =0.00
        try:
            res =float(str)
        except:
            res =0.00
        return res

    def get_str_form_ops2(self):
        #import ipdb; ipdb.set_trace()
        self.ops = self.factory.odoo_con.get_ops(self.task_id)

        op_=self.ops[str(self.active_op)]
        op_['VISITED'] = True
        not_vis = 0
        not_proc = 0
        for op in self.ops:
            op__=self.ops[op]
            if op__['VISITED']:
                not_vis += 1
            if op__['PROCESADO']:
                not_proc += 1


        self.op_id = op_['ID']
        if op_['PROCESADO']:
            self.vals["paquete"]=op_['PAQUETE']
            self.vals["destino"]=op_['DESTINO']

        if not op_:
            raise Exception(u"No hay datos de la operacion\nImposible imprimir operacion")

        header = "Tarea:" + str(self.task_id) + " (" + str(not_vis) + " - " + str(not_proc)\
                 + ")\n"

        if self.tasks[self.active_task]['paused']== True:
            header = self.inverse(header)
        header += "Operation: " + str(op_['ID']) + "(" + str(self.active_op) \
                 + " de "  + str(len(self.ops)) + ")"+ "\n"
        delimiter = "********************\n"
        strg = header

        k = u"PRODUCTO"
        strg += k + u":  " + op_[k] + "\n"

        k = u"CANTIDAD"
        strg += k + u":  " + str(op_[k]) + "\n"

        k = u"LOTE"
        strg += k + u":  " + op_[k] + "\n"

        k = u"PAQUETE"
        op_ok = True
        if not self.vals['paquete']:
            strg +=self.inverse(k +   u"(" + str(op_['paquete_id']) + "):  " + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k +   u"(" + str(op_['paquete_id']) + "):  " + str(op_[k]) +  "\n"

        k = u"ORIGEN"
        strg += k + u"(" + str(op_['origen_id']) + "):  " + str(op_[k]) +   "\n"

        k = u"DESTINO"
        if not self.vals['destino']:
            strg += self.inverse(k +   u"(" + str(op_['destino_id']) + "):  " + str(op_[k])) + "\n"
            op_ok = False
        else:
            strg +=k +   u"(" + str(op_['destino_id']) + "):  " + str(op_[k]) +  "\n"


        k = u"PROCESADO"
        if op_[k]:
            str_proc =u'SI'
        else:
            str_proc = u'NO'
        strg += k + u":  " + str_proc + "\n"

        keys = ""

        if len(self.ops)>1:
            keys += "<" + KEY_PREV + "> <" + KEY_NEXT + ">\n"


        if op_['PROCESADO']:
            keys += "<" + KEY_CANCEL +"> Cancel OP"
        else:
            if op_ok:
                keys += "<" + KEY_CONFIRM + "> Conf OP"

        keys += "<" + KEY_VOLVER + "> Atras"
        if self.show_keys:
            strg += delimiter + keys
        return strg

# Asigna a cada conexión un protocolo ScanGunProtocol
class ScanGunFactory(Factory):
    def __init__(self):
        # Códigos telnet de usuarios registrados
        self.users_codes = []
        #import ipdb; ipdb.set_trace()
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
