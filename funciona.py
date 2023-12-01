from machine import Pin
from hcsr04 import HCSR04
from time import sleep
import network
import time
import urequests
from utelegram import Bot

token = "5953821526:AAH3qHHfJ_-qwOb6fehN7eBquiNoRlIA4AY"
url = "https://api.thingspeak.com/update?api_key=VALQ6YRPNMDR7R9U&field1="

bot = Bot(token)
medidor = HCSR04(trigger_pin=2, echo_pin=4)
led = Pin(5, Pin.OUT)
bomba = Pin(23, Pin.OUT)  # Pin para controlar la mini bomba sumergible
# ---------------------------------[ CONECTAR WIFI ]-----------------------------------------

def conectaWifi(red, password):
    global miRed
    miRed = network.WLAN(network.STA_IF)
    if not miRed.isconnected():  # Si no está conectado…
        miRed.active(True)  # activa la interfaz
        miRed.connect(red, password)  # Intenta conectar con la red
        print('Conectando a la red', red + ".........")
        timeout = time.time()
        while not miRed.isconnected():  # Mientras no se conecte...
            if time.ticks_diff(time.time(), timeout) > 10:
                return False
    return True

# ------------------------------------[Respuesta de conexión WIFI]---------------------------------------------------------------------#

if conectaWifi("GT OPERACIONES 2", "lalas1234"):  # Clave de conexión a la red de Wokwi

    print("Conexión exitosa!")
    print('Datos de la red (IP/netmask/gw/DNS):', miRed.ifconfig())
    print("Ok, Ya está funcionando")

    # Variable para controlar el estado del sistema
    sistema_activado = False
    falta_agua_enviado = False  # Variable para controlar el envío del mensaje "Falta agua"

    # ------------------------------------[BOT Decoradores]---------------------------------------------------------------------#
    @bot.add_message_handler("Menú")
    def help_menu(update):
        global sistema_activado, falta_agua_enviado
        sistema_activado = False
        falta_agua_enviado = False
        update.reply("""¡Bienvenido! 
        \n Menu Principal                                        
        \n GyFCompany \U0001F916
        \n Elije una opción:   
        Encender el sistema: On                                                                                                 
        \n Sistema de monitoreo de abrevadero.
        \n Gracias  \U0001F600
        \n Ver en línea tu gráfica: https://thingspeak.com/channels/2363441/charts/1?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=60&type=line&update=15
        \n """)

    @bot.add_message_handler("On")
    def handle_on(update):
        bomba.value(0)
        global sistema_activado, falta_agua_enviado
        sistema_activado = True
        falta_agua_enviado = False
        update.reply("Sistema activado")
        print("Sistema activado")

        while sistema_activado:
            try:
                distancia = round(medidor.distance_cm(), 2)
                print("Distancia: ", distancia)
                respuesta = urequests.get(url + "&field1=" + str(distancia))
                respuesta.close()
                sleep(1)
                if distancia < 9:
                    led.value(0)
                    print("Nivel de agua normal")
                    bomba.value(1)  # Apagar la bomba
                    sleep(1)
                    if falta_agua_enviado:
                        falta_agua_enviado = False  # Restablecer el indicador de envío
                elif distancia > 12:
                    led.value(1)
                    print("Se necesita agua")
                    if not falta_agua_enviado:
                        update.reply("LLenando abrevadero")
                        falta_agua_enviado = True  # Establecer el indicador de envío
                    bomba.value(0)  # Encender la bomba
                    sleep(1)
                else:
                    print("Nivel de agua normal")
                    bomba.value(1)  # Apagar la bomba
                    if falta_agua_enviado:
                        falta_agua_enviado = False  # Restablecer el indicador de envío
            except Exception as e:
                print("Error:", e)

    bot.start_loop()

else:
    print("Imposible conectar")
    miRed.active(False)
    
    bot.start_loop()