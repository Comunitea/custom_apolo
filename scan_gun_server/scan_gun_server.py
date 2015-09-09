#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Para probar la codificación
"""
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from OdooCon import OdooDao
import sys
import string


params = {}  # se guardará la configuración del archivo aquí


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


# Devuelve datos de conexión del archivo de configuración guardado en params
def get_connection_params(return_params=[]):
    return [params[k] for k in return_params if k in params]


# Protocolo para manejar las conexiones, una instancia por conexión
class ScanGunProtocol(LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.state = "register"
        self.user_id = False
        self.code = False
        self.camera_id = False
        self.task_id = False
        self.op_data = False

    def connectionMade(self):
        """
        Método del framework. Mensaje al establecer la conexión
        """
        self._snd(u"**************************\nIntroduzca su código de " + chr(27)+"[7;31m" + "operador:" + chr(27)+"[0m")
    def connectionLost(self, reason):
        """
        Método del framework. Mensaje al perder la conexión
        """
        if self.code in self.factory.users_codes:
            self.factory.users_codes.remove(self.code)
        self._snd(u"Se perdio la conexión")

    def lineReceived(self, line):
        """
        Método del framework. LLamado cada vez que se recibe una linea
        """
        try:
            if line == "quit":
                sys.exit(0)
            elif self.state == "register":
                self.handle_register(line)
            elif self.state == "menu1":
                self.handle_menu1(line)
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
            else:
                self._snd(u"Introduciste %s, pero paso olimpicamente:" % line)
        except Exception, e:
            str_error = u"Ocurrió un " + chr(27)+"[7;31m" + "error.\n" + chr(27)+"[0m"
            str_error += e.message
            self._snd(str_error)

    def _snd(self, line, custom_format=True):
        """
        Formatea la salida, al enviar mensaje al cliente
        """
        clean = u'\n' * 20

        if custom_format:
            cutstr = self.cut_in_lines(line)
            self.sendLine((clean + cutstr).encode("UTF-8"))
        else:
            self.sendLine((clean + line).encode("UTF-8"))

    def cut_in_lines(self,line):
        """
        Corta la cadena de caracteres quitándole los símbolos \n, que son los
        que indican el ambio de línea.
        """
        limit_screen = 26 #caracteres que tiene de ancho la pantalla
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
        limit_screen = 26
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
            self._snd(u"Ya hay un usuario con ese código registrado\n**************************\nIntroduzca código operador")
            return

        if self.get_odoo_connexion(code):
            str_menu = self.get_str_menu1()
            self._snd(str_menu)
            self.state = "menu1"
        else:
            self._snd(u"No se pudo establecer la conexión.\nIntroduzca código de nuevo")

    def get_odoo_connexion(self, code):
        """
        LLamado en estado register, si se establece la conexión, se guarda el
        usuario y el código telnet usado para comprobar si alguíen introdue
        el mismo
        """
        res = True
        try:
            user_id = self.factory.odoo_con.get_user_by_code(code)
            self.user_id = user_id
            self.code = code
            self.factory.users_codes.append(code)
        except Exception, e:
            res = False
        return res

    def get_str_menu1(self):
        """
        Método que devuelve el menú principal
        """
        delimiter = u"\n**************************"
        menu_str1 = u"\n1->Tarea de ubicación"
        menu_str2 = u"\n2->Tarea de reposición"
        menu_str3 = u"\n3->Tarea de picking"
        menu_str4 = u"\n4->Transferencia manual"
        return delimiter + menu_str1 + menu_str2 + menu_str3 + menu_str4 + delimiter

    def handle_menu1(self, line, custom_format=True):
        """
        Manejador del estado menu1. Para tareas muestra un menú con las
        cámaras a seleccionar, y cambia al siguiente estado si la ubicación es
        correcta.
        """
        if line not in ["1", "2", "3", "4", "5"]:
            str_error = u"La opción %s no es válida.\nReintentar:\n" % line
            self._snd(str_error + self.get_str_menu1())
        elif line == "1":
            self.state = "ubication"
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        elif line == "2":
            self.state = "reposition"
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        elif line == "3":
            self.state = 'picking'
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        elif line == "4":
            self.state = 'manual_transfer'
            menu_str = self.get_cameras_menu()
            self._snd(menu_str)
        else:
            self._snd(u"No implementado aún")

    def get_cameras_menu(self):
        """
        Devuelve el menú con las cámaras disponibles
        """
        delimiter = "\n**************************"
        str_menu = ""
        for key in self.factory.menu_cameras:
            str_menu += "\n" + str(key) + "->" + self.factory.menu_cameras[key][1]
        return delimiter + str_menu + delimiter

    def handle_camera_selected(self, line):
        """
        Manejador de los estados location, reposition y picking, pide elegir
        cámara, en caso afirmativo trata de obtener una tarea ya existente
        o crearse una. Quizás haya que meter estado intermedio para que
        seleccione el modo manual de ubicar o el que te da las tareas.
        """
        next_state = {
            'ubication': 'scan_op',
            'reposition': 'scan_op_rep',
            'picking': 'scan_op_pick',
        }
        str_keys = [str(x) for x in self.factory.menu_cameras.keys()]
        if line not in str_keys:
            str_error = u"La opcion %s no es válida.\nReintentar\n" % line
            self._snd(str_error + self.get_cameras_menu())
        else:
            try:
                self.camera_id = self.factory.menu_cameras[int(line)][0]
                self.task_id = self.factory.odoo_con.get_task_of_type(self.user_id, self.camera_id, self.state)
                old_state = self.state
                self.state = next_state[old_state]
                self.op_data = self.get_operation_data()
                op_str = self.get_operation_str(mode='scan_op')
                self._snd(op_str)
            except Exception, e:
                expt_str = e.message
                str_error = expt_str + u"\nIntroduzca cámara de nuevo\n"
                self._snd(str_error + self.get_cameras_menu())

    def get_operation_data(self):
        """
        Intenta devolver un diccionario con datos de la siguiente operacion
        no visitada.
        """
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
        keys = (u"PRODUCTO", u"CANTIDAD", u"LOTE", u"PAQUETE", u"ORIGEN", u"DESTINO")
        for k in keys:
            op_str += k + u":  " + self.op_data[k] + "\n"
        op_str += u"\n(Escriba '#C' para cancelar la operación)\n"
        if mode == 'scan_op':
            op_str += u"\n**************************\nScan Producto/Paquete:"
        if mode == 'scan_location':
            op_str += u"\n**************************\nScan Destino:"
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
            str_error = u"Error al cancelar la operación o finalizar la tarea %s\n"
            self._snd(str_error + e.message)

    def handle_scan_op(self, line):
        """
        Manejador del estado scan_op. Si se escanea el producto o el paquete
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
                message = u"Scan " + chr(27)+"[7;31m" + "incorrecto" + chr(27)+"[0m" + ", Escanee de nuevo el paquete\n"
                message += self.get_operation_str(mode='scan_op')
            self._snd(message)
        except Exception, e:
            str_error = u"\nNo se pudo identificar la etiqueta %s\n" % line
            self._snd(str_error + e.message)

    def handle_scan_location(self, line):
        """
        Manejador del estado scan_location. Si se escanea correctamente la
        ubicación destino, se muestra la siguiente operación (volviendo al
        punto de escanear el paquete/producto) o se finaliza la tarea si ya
        no quedan más.
        """
        # Cancelar la operación y pasar a la siguiente.
        if line in ["#c", "#C"]:
            self.cancel_operation()
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
                    str_error = u"Error al marcar la operación o al finalizar tarea\n"
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
