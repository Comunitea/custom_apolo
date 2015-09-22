Las pistolas mandan texto y reciben texto via telnet.
Este módulo contiene el servidor de telnet que sirve las peticiones a las
distintas sesiones telnet.

Para configurar la pistola contra el servidor:
1. Necesitamos conectar la pistola a la red local
2. Editamos en el archivo telnet.cfg el nombre de la bbdd el usuario la
   contraseña y el puerto.
2. Abrimos la aplicación Psion Tekterm, con ctrl + alt + 0 abrimos la ventana
   donde podemos configurar los parámetros del sistema, necesitamos establecer
   la ip del servidor y el puerto indicado en telnet.cfg, con lo que creamos
   una sesión de telnet para el servidor.
3. Cuando usemos la aplicación con el nuevo parámetyro que acabamos de crear
   sera como hacer en una consola telnet ip puerto y nos comunicaremos
   iterativamente con ella.
