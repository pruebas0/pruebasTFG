# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------------
#                               MODULOS Y LIBRERIAS
#---------------------------------------------------------------------------------
from multiprocessing import Queue
from threading import Thread
from lib import Server_v0
from enum import Enum
import time

#---------------------------------------------------------------------------------
#                               ESTADOS FSM TUIO1
#---------------------------------------------------------------------------------
class Tuio1State(Enum):
    IDLE = 0  # Estado inicial de la maquina de estados. Sin comunicaciones
    MAIN = 1  # Estado principal de la aplicación. Comunicaciones establecidas.
    GAME = 2  # Juego activo.
    EXIT = 3  # Estado final de la aplicación

#---------------------------------------------------------------------------------
#                           APLICACIÓN PRINCIPAL TUIO1
#---------------------------------------------------------------------------------
class Tuio1(object):
    def __init__(self):
        self.fsm = Tuio1FSM()                  # Objeto para la maquina de estados
        Thread(target=self.tuio1fsm,).start()  # Iniciar hilo maquina de estados TUIO1

    def tuio1fsm(self):
        while not self.fsm.current == Tuio1State.EXIT:
            self.fsm.next()  #Ejecutar el método para manejo de eventos en la máquina de estados

#---------------------------------------------------------------------------------
#                           MAQUINA DE ESTADOS FSM TUIO1
#---------------------------------------------------------------------------------
class Tuio1FSM(object):
    def __init__(self):
        self.server = Server_v0.Server()     # Objeto para las comunicaciones
        event = ("init_server", "")          # Evento: iniciar servidor
        self.server.fsm.create_event(event)  # Crear evento en servidor
        self.current = Tuio1State.IDLE       # Estado inicial de TUIO1
        self.events = Queue()                # Cola de eventos en FSM TUIO1


    #---------------------------------------------------------------------------------
    #                   METODOS PARA MANEJO DE EVENTOS FSM TUIO1
    #---------------------------------------------------------------------------------
    # Obtener proximo evento
    def next(self):
        # Eventos FSM TUIO1
        if not self.events.empty():
            ev = self.events.get()   # Obtener nuevo evento
            self.dispatch_event(ev)  # Procesar nuevo evento

        # Eventos TUIO2 (client)
        if not self.server.fsm.data_from_client.empty():
            ev = self.server.fsm.data_from_client.get()  #Obtener evento de comunicaciones
            self.dispatch_event(ev)                      #Procesar nuevo evento

    # Metodo crear evento.
    # Argumento de entrada ev: evento para almacenar en la cola
    def create_event(self, ev):
        self.events.put(ev)  #Almacenar evento en la cola

    # Manejo de eventos.
    # Argumento de entrada ev: evento para manejar (tipo y data)
    def dispatch_event(self, ev):
        tipo = ev[0] # Tipo de evento
        data = ev[1] # Datos para enviar a TUIO2

        # Evento dispositivo TUIO2 conectado. Llama al método tuio2_connect()
        if tipo == "tuio2_connect":
            self.tuio2_connect()

        # Evento dispositivo TUIO2 desconectado. LLamada al método tuio2_disconect()
        if tipo == "tuio2_disconnect":
            self.tuio2_disconnect()

        # Evento datos recividos desde el dispositivo TUIO2.
        # Llamada al método data_received(). Argumento de entrada: data (datos recibidos)
        if tipo == "data_received":
            self.data_received(data)

        # Evento obtener datos del dispositivo TUIO2.
        # Llamada al método request_data(). Argumento de entrada: data (datos solicitados)
        if tipo == "request_data":
            self.request_data(data)

        # Evento empezar juego en ambos dispositivos
        if tipo == "start_game":
            self.start_game()

        # Evento detener juego en ambos dispositivos
        if tipo == "stop_game":
            self.stop_game()

        # Evento salir del dispositivo TUIO1
        if tipo == "exit_tuio1":
            self.exit_tuio1()

    #---------------------------------------------------------------------------------
    #                         TRANSICIONES FSM TUIO1
    #---------------------------------------------------------------------------------
    # Metodo para transicion de estado IDLE a MAIN.
    # El dispositivo TUIO2 esta conectado.
    def tuio2_connect(self):
        if self.current == Tuio1State.IDLE:
            self.current = Tuio1State.MAIN

    # Transicion al estado IDLE.
    # El dispositivo TUIO2 esta desconectado
    def tuio2_disconnect(self):
        self.current = Tuio1State.IDLE

    # Datos recibidos desde TUIO2
    # Argumento de entrada data: datos recibidos desde TUIO2
    def data_received(self,data):
        if self.current == Tuio1State.GAME:
            print("Datos recibidos desde el cliente" , data)

    # Obtener datos de TUIO2.
    # Argumento de entrada data: datos solicitados a TUIO2
    def request_data(self,data):
        if self.current == Tuio1State.GAME:
            event = ('send_data',data)           # Evento: mandar datos a TUIO1
            self.server.fsm.create_event(event)  # Crear evento para el servidor

    # Transicion desde el estado MAIN a GAME
    # Comienza el juego en TUIO1 y TUIO2
    def start_game(self):
        if self.current == Tuio1State.MAIN:
            self.current = Tuio1State.GAME
            event = ("send_data", (b'start_game', b''))  # Evento: mandar datos a TUIO2 (empezar juego)
            self.server.fsm.create_event(event)          # Crear evento para el servidor

    # Transicion desde el estado GAME a MAIN
    # Juego detenido en TUIO1 y TUIO2
    def stop_game(self):
        if self.current == Tuio1State.GAME:
            self.current = Tuio1State.MAIN
            event = ("send_data", (b'stop_game', b''))  # Evento: mandar datos a TUIO2 (detener juego)
            self.server.fsm.create_event(event)         # Crear evento para el servidor.

    # Transicion al estado EXIT
    # El dispositivo TUIO1 sale de la aplicacion
    def exit_tuio1(self):
        self.current = Tuio1State.EXIT
        event = ("close_server", "")         # Evento: cerrar servidor
        self.server.fsm.create_event(event)  # Crear evento para el servidor


if __name__ == '__main__':
    tuio1 = Tuio1()                                       # Crear el objeto Tuio1
    time.sleep(10)                                        # Tiempo de espera
    event = ("start_game","")                             # Evento: comenzar juego
    tuio1.fsm.create_event(event)                         # Crear evento en fsm TUIO1
    time.sleep(10)                                        # Tiempo de espera
    event = ("request_data",(b'mpu_9255',b'data_sensor')) # Evento: obtener datos del sensor mpu9255
    tuio1.fsm.create_event(event)                         # Crear evento en fsm TUIO1
    time.sleep(80)                                        # Tiempo de espera
    event = ("exit_tuio1","")                             # Evento: salir de TUIO1
    tuio1.fsm.create_event(event)                         # Crear evento en fsm TUIO1
