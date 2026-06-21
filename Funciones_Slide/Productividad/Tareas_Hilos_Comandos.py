import threading
import time
import json
import os
from datetime import datetime
from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
from Funciones_Slide.Comunicacion.Funciones_Variadas import Enviar_mensaje_Whatsapp, llamada_whatsapp, colgar
def monitor_de_tareas():
    while True:
        # Si todavia no hay archivo de tareas, esperamos y reintentamos (no crashea).
        if not os.path.exists("tareas.json"):
            time.sleep(30)
            continue

        with open("tareas.json","r") as f:
            tareas = json.load(f)
        tiempo = datetime.now().strftime("%d/%m %H:%M")
        cambio = False

        hubo_notificacion = False
        for i in tareas:

            if i["hora"]==tiempo and i["estado"]=="pendiente":

                if i["accion"] == "WHATSAPP":
                    Enviar_mensaje_Whatsapp(i["target"],i["info"])
                elif i["accion"] == "LLAMAR":
                     llamada_whatsapp(i["target"])
                elif i["accion"] == "NOTIFICAR":
                     hablado_del_asistente(f"Recordatorio, señor: {i['info']}")
                     hubo_notificacion = True

                i["estado"]="completado"
                cambio = True
        if cambio == True:
            with open("tareas.json","w") as f:
                json.dump(tareas,f,indent=4)
            if not hubo_notificacion:
                hablado_del_asistente("Se completo la tarea, señor ")


        time.sleep(30)

def iniciar_hilos():
    hilo_secundario = threading.Thread(target=monitor_de_tareas, daemon=True)    
    hilo_secundario.start()    

