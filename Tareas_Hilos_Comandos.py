import threading
import time
import json
from datetime import datetime
from Herramientas_del_asistente import hablado_del_asistente
from Comandos_Asistente import Programacion_de_Tareas
from Funciones_Variadas import Enviar_mensaje_Whatsapp
from Funciones_Variadas import llamada_whatsapp
from Funciones_Variadas import colgar

def monitor_de_tareas():
    while True:
        with open("tareas.json","r") as f:
            tareas = json.load(f)
        tiempo = datetime.now().strftime("%d/%m %H:%M")
        cambio = False
        
        for i in tareas:

            if i["hora"]==tiempo and i["estado"]=="pendiente":

                if i["accion"] == "WHATSAPP":
                    Enviar_mensaje_Whatsapp(i["target"],i["info"])
                elif i["accion"] == "LLAMAR":
                     llamada_whatsapp(i["target"])




                i["estado"]="completado"
                cambio = True
        if cambio == True:
            with open("tareas.json","w") as f:
                json.dump(tareas,f,ident=4)
                hablado_del_asistente("Se completo la tarea, señor ")
                
                
        time.sleep(30)

def iniciar_hilos():
    hilo_secundario = threading.Thread(target=monitor_de_tareas, daemon=True)    
    hilo_secundario.start()    

