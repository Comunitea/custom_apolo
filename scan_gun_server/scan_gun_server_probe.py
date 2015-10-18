#!/usr/bin/python
# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.manhole.telnet import Shell
from twisted.manhole.telnet import ShellFactory
import sys
from OdooCon import OdooDao

params = {}


def read_file():
    #import ipdb; ipdb.set_trace()
    if sys.argv:
        telnet_cfg = sys.argv
    else:
        telnet_cfg = 'telnet.cfg'
    with open(sys.argv, 'r') as configfile:
        for line in configfile:
            key = line[:line.index('=')]
            value = line[line.index('=') + 1:].replace('\n', '')
            if value.isdigit():
                value = int(value)
            if key == 'allowed_ips':
                value = value.split(',')
            params[key] = value
read_file()


def get_connection_params(return_params=[]):
    return [params[k] for k in return_params if k in params]


class Connection:

    def __init__(self, handler, uid):
        self.handler = handler
        self.current_mode = False
        self.uid = uid



class ConnectionManager:

    def __init__(self):
        self.connections = {}
        server, port, db, user, password = get_connection_params(
            ['odoo_host', 'odoo_port', 'odoo_db', 'odoo_user',
             'odoo_password'])
        self.odoo_con = OdooDao(server, port, db, user, password)
        self.user_id = False
        self.user_name = 'username'

    def new_connection(self, handler, user_code):
        """
            Solo se permite una conexion por usuario, en caso de establecer
            una nueva conexion se cierra y elimina la anterior.
        """
        if self.connections.get(user_code, False):
            self.destroy_connection(user_code)
        user_id, user_name = self.odoo_con.get_user_by_code(user_code)
        self.user_name = user_name
        self.user_id = user_id
        self.connections[user_code] = Connection(handler, user_id[0])

    def destroy_connection(self, user_code):
        if not self.connections.get(user_code, False):
            return
        self.connections.get(user_code).handler.finish()
        self.connections.pop(user_code, None)
        return




    # def new_connection(self, handler, user_code):
    #     """
    #         Solo se permite una conexion por usuario, en caso de establecer
    #         una nueva conexion se cierra y elimina la anterior.
    #     """
    #     if self.connections.get(user_code, False):
    #         self.destroy_connection(user_code)
    #     user_id = self.odoo_con.get_user_by_code(user_code)
    #     self.user_id = user_id
    #     self.connections[user_code] = Connection(handler, user_id[0])

    # def destroy_connection(self, user_code):
    #     if not self.connections.get(user_code, False):
    #         return
    #     self.connections.get(user_code).handler.finish()
    #     self.connections.pop(user_code, None)
    #     return


class ConnectionManager2():
    def __init__(self, user_id):
        # self.connections = {}
        server, port, db, user, password = get_connection_params(
            ['odoo_host', 'odoo_port', 'odoo_db', 'odoo_user',
             'odoo_password'])
        self.odoo_con = OdooDao(server, port, db, user, password)
        self.user_id = user_id


class ScanGunHandler(Shell):

    # manager = ConnectionManager()

    # manager = ConnectionManager2()
    variable = "1"
    def welcomeMessage(self):
        return chr(12) + "Hola, ¿Quién eres?" + "\n"

    def connectionLost(self, reason):
        self._twr("Se perdió la conexión")

    def checkUserAndPass(self, username, password):
        self.transport.write('Me fiare que eres %s y tu pass es %s\n' %
                             (username, password))
        self.user = username
        self.password = password
        # self.manager.user_id = username + "#" + password
        self.manager = ConnectionManager2(username)
        res = False
        # try:
        #     self.manager.new_connection(self, password)
        #     res = True
        # except ValueError:
        #     self._twr('Error al logearse. Probablemente mal usuario y pass')
        #     res = False
        # return res
        return True

    def _get_menu(self):
        menu = "1 - Modo Automático\n2 - Modo Manual\n3 - Do read\n4 - user?l\n5 - user2"
        return menu

    def loggedIn(self):
        menu = self._get_menu()
        self.state = 'menu'
        self._twr(menu)

    def _twr(self, string):
        clean = '\n' * 10
        self.transport.write(str(clean + string + '\n'))

    def doCommand(self, cmd):
        string = 'nada'
        if cmd == 'quit':
            sys.exit(0)
        elif cmd == 'qq':
            self.variable="qq"
        elif cmd == 'ww':
            self.variable="ww"
        elif cmd == "ee":
            self._twr(self.variable)
        elif cmd == '3' and self.state == 'menu':
            aa = self.manager.odoo_con.connection.read('res.users', self.manager.user_id, ['name'])
            self._twr(aa[0]['name'])
        elif cmd == '4' and self.state == 'menu':
            self._twr(self.manager.user_id)
        elif cmd == '5' and self.state == 'menu':
            self._twr(self.user)
        else:
            string = 'Introduciste comando: %s, pero paso\r' % cmd
        self._twr(string)
        # self.transport.write()

if __name__ == "__main__":
    shell = ShellFactory()
    shell.protocol = ScanGunHandler
    reactor.listenTCP(50000, shell)
    reactor.run()
