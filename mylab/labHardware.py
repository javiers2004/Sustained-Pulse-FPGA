from __future__ import unicode_literals, print_function, division

import os
import time
from mylab import weblab, redis
import paramiko

#from weblablib import weblab_user
from labdiscoverylib import weblab_user
"""import RPi.GPIO as gpio"""


"""
This module is just an example of how you could organize your code. Here you would
manage any code related to your hardware, for example.

In this case, we're going to have a very simple laboratory that we will create
in a Redis database (in memory). You will have:

 - 10 lights (0..9)
 - 1 microcontroller, which interacts with the lights

In Redis, we'll work with 11 variables for this:

 - hardware:lights:0 {on|off}
 - hardware:lights:1 {on|off}
 - hardware:lights:2 {on|off}
 - hardware:lights:3 {on|off}
 - hardware:lights:4 {on|off}
 - hardware:lights:5 {on|off}
 - hardware:lights:6 {on|off}
 - hardware:lights:7 {on|off}weblab_user
 - hardware:lights:8 {on|off}
 - hardware:lights:9 {on|off}
 - hardware:microcontroller {empty|programming|programmed|failed}
"""

INTERRUPTORS =10
PULSATORS = 4
SLIDERS = 2


ssh = None


@weblab.on_start
def start(client_data, server_data):
    global ssh
    print("************************************************************************")
    print(f"Preparing laboratory for user {weblab_user.username}...")
    weblab_user.data['local_identifier'] = weblab.create_token()
    print(f"Generated identifier: {weblab_user.data['local_identifier']}")
    print("************************************************************************")

    # Inicialización de hardware en Redis
    for interruptor in range(INTERRUPTORS):
        redis.set(f'hardware:interruptors:{interruptor}', 'off')
    for pulsator in range(PULSATORS):
        redis.set(f'hardware:pulsator:{pulsator}', 'off')
    for slider in range(SLIDERS):
        redis.set(f'hardware:sliders:{slider}', 50)
    redis.set('hardware:microcontroller', 'empty')

    raspberry_ip = "192.168.0.213"  # Cambia esto a la IP de tu Raspberry Pi
    username = "weblab"             # Usuario SSH
    password = "letmein"        # Contraseña SSH

    # Comandos para cargar el archivo .bit y configurar los GPIO
    bit_file_path = "~/test_weblab_24_25.bit"
    gpio_commands = """
import RPi.GPIO as gpio
gpio.cleanup() 
gpio.setmode(gpio.BCM)
pins = [4, 17, 27, 22, 5, 6, 13, 19, 26, 21, 20, 16]
pins2 = [26, 21, 20, 16]
for pin in pins:                                                    
    gpio.setup(pin, gpio.OUT)
    gpio.output(pin, 0)
for pin in pins2:                                                    
    gpio.setup(pin, gpio.OUT)
    gpio.output(pin, 0)

    """            

    try:
        # Conectar vía SSH
        print("Conectando a la Raspberry Pi...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(raspberry_ip, username=username, password=password)

        # Cargar el archivo .bit en la FPGA
        print("Cargando el archivo .bit en la FPGA...")
        command = f"sudo openFPGALoader -b basys3 {bit_file_path}"
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())

        # Esperar unos segundos para asegurarse de que el proceso terminó
        time.sleep(2)

        # Configurar los pines GPIO remotamente
        print("Configurando los pines GPIO...")
        command = f"sudo python -c \"{gpio_commands}\""
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())

        # Cerrar la conexión
        #command = f"sudo openFPGALoader -r"
        #stdin, stdout, stderr = ssh.exec_command(command)
        #print(stdout.read().decode())
        #print(stderr.read().decode())
        #ssh.close()
        print("Tarea completada con éxito.")

    except Exception as e:
        print(f"Error: {e}")
    

def clean_resources():
    global ssh
    """
    This code could be in dispose(). However, since we want to call this low-level
    code from outside any request and we can't (since we're using
    weblab_user.username in dispose())... we separate it. This way, this code can
    be called from outside using 'flask clean-resources'
    """
    redis.set('hardware:microcontroller', 'empty')
    print("Microcontroller restarted")
    try:
        gpio_commands = """
import RPi.GPIO as gpio
gpio.cleanup()
        """.format(pins[number], pins[number])
        command = f"sudo python -c \"{gpio_commands}\""
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stdout.read().decode())
        print(stderr.read().decode())
    except Exception as e:
        print(f"Error: {e}")




def switch_interruptor(number, state):
    global ssh
    pins = [4, 17, 27, 22, 5, 6, 13, 19, 26, 21, 20, 16]
    if state:
        print("************************************************************************")
        print("  User {} (local identifier: {})".format(weblab_user.username, weblab_user.data['local_identifier']))
        print("  Interruptor {} has been turned on!                                  ".format(number + 1))
        print("************************************************************************")
        redis.set('hardware:interruptors:{}'.format(number), 'on')
        try:
            gpio_commands = """
import RPi.GPIO as gpio
gpio.cleanup() 
gpio.setmode(gpio.BCM)
gpio.setup({}, gpio.OUT)
gpio.output({}, 1)
            """.format(pins[number], pins[number])
            command = f"sudo python -c \"{gpio_commands}\""
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read().decode())
            print(stderr.read().decode())
        except Exception as e:
            print(f"Error: {e}")
        
    else:
        print("************************************************************************")
        print("  Interruptor {} has been turned off!                                 ".format(number + 1))
        print("************************************************************************")
        redis.set('hardware:interruptors:{}'.format(number), 'off')
        try:
            gpio_commands = """
import RPi.GPIO as gpio
gpio.cleanup() 
gpio.setmode(gpio.BCM)
gpio.setup({}, gpio.OUT)
gpio.output({}, 0)
            """.format(pins[number], pins[number])
            command = f"sudo python -c \"{gpio_commands}\""
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read().decode())
            print(stderr.read().decode())
        except Exception as e:
            print(f"Error: {e}")


def change_slider(number, value):
    print("************************************************************************")
    print("  User {} (local identifier: {})".format(weblab_user.username, weblab_user.data['local_identifier']))
    print("  Slider {} new value is {}                                  ".format(number + 1, value))
    print("************************************************************************")
    redis.set('hardware:slider:{}'.format(number), value)


def press_pulsador(number):
    print("************************************************************************")
    print("  User {} (local identifier: {})".format(weblab_user.username, weblab_user.data['local_identifier']))
    print("  Pulsator {} has been turned on!                                  ".format(number + 1))
    print("************************************************************************")
    redis.set('hardware:pulsator:{}'.format(number), 1)
    

def is_interruptor_on(number):
    return redis.get('hardware:interruptors:{}'.format(number)) == 'on'

def slider_value(number):
    return redis.get('hardware:sliders:{}'.format(number))

def get_microcontroller_state():
    return redis.get('hardware:microcontroller')

def loadGit(file):
    """
    Carga un archivo .bit en la FPGA utilizando openFPGALoader.

    :param file: Objeto FileStorage que hace referencia a un archivo almacenado en la carpeta /uploads.
    """
    try:
        upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
        bit_file_path = os.path.join(upload_folder, file.filename)

        print("aqui" + bit_file_path)

        if not os.path.isfile(bit_file_path):
            raise FileNotFoundError(f"El archivo {bit_file_path} no existe en la carpeta /uploads.")

        print(f"Cargando el archivo .bit en la FPGA desde {bit_file_path}...")

        command = f"sudo openFPGALoader -b basys3 {bit_file_path}"

        stdin, stdout, stderr = ssh.exec_command(command)

        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()

        if stdout_output:
            print("Output:")
            print(stdout_output)
        
        if stderr_output:
            print("Errores:")
            print(stderr_output)

    except Exception as e:
        print(f"Error al cargar el archivo en la FPGA: {str(e)}")


@weblab.task()
def program_device(code):

    if weblab_user.time_left < 10:
        print("************************************************************************")
        print("Error: typically, programming the device takes around 10 seconds. So if ")
        print("the user has less than 10 secons to use the laboratory, don't start ")
        print("this task. Otherwise, the user session will still wait until the task")
        print("finishes, delaying the time assigned by the administrator")
        print("************************************************************************")
        return {
            'success': False,
            'reason': "Too few time"
        }

    print("************************************************************************")
    print("You decided that you wanted to program the robot, and for some reason,  ")
    print("this takes time. In weblablib, you can create a 'task': something that  ")
    print("you can start, and it will be running in a different thread. In this ")
    print("case, this is lasting for 10 seconds from now ")
    print("************************************************************************")
    if redis.get('hardware:microcontroller') == 'programming':
        # Just in case two programs are sent at the very same time
        return {
            'success': False,
            'reason': "Already programming"
        }

    redis.set('hardware:microcontroller', 'programming')
    for x in range(10):
        time.sleep(1)
        print("Still programming...")


    if code == 'division-by-zero':
        print("************************************************************************")
        print("Oh no! It was a division-by-zero code! Expect an error!")
        print("************************************************************************")
        redis.set('hardware:microcontroller', 'failed')
        10 / 0 # Force an exception to be raised

    print("************************************************************************")
    print("Yay! the robot has been programmed! Now you can retrieve the result ")
    print("************************************************************************")
    redis.set('hardware:microcontroller', 'programmed')





    return {
        'success': True
    }

