import json
import os 
import webbrowser
import pyautogui
import time
import importlib
import Auto_Programacion


def guardar_en_json(accion,target,info,hora):
    archivo = "tareas.json"

    with open(archivo,"r") as f:
        tareas = json.load(f)

    nueva_tarea = {
        "accion": accion,
        "target": target,
        "info": info,
        "hora": hora,
        "estado": "pendiente"
    }
    tareas.append(nueva_tarea)

    with open(archivo,"w") as f:
        json.dump(tareas,f,indent=4)





