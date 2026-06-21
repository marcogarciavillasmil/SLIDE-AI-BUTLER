import cv2
import webbrowser
import os
import subprocess
import pyautogui
import face_recognition
import face_recognition_models
import time 
import urllib.parse
import sys
from Funciones_Slide.Productividad.Gestion_datos import guardar_en_json
import json





Cara = cv2.imread(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Imagenes", "Marco.jpg"))

def abrir_camara():
 captura = cv2.VideoCapture(0, cv2.CAP_DSHOW)
 cv2.namedWindow("Camara_IA",cv2.WND_PROP_FULLSCREEN)
 cv2.setWindowProperty("Camara_IA",cv2.WND_PROP_FULLSCREEN,cv2.WND_PROP_FULLSCREEN)

 while True:
    
    resultado, imagen = captura.read()
    if not resultado:
        break
    
    resultado = cv2.imshow("Camara_IA",imagen)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

 captura.release()
 cv2.destroyAllWindows()
 return "Cámara cerrada, señor"

def Reconocimiento_Facial():

    Localizacion_cara = face_recognition.face_locations(Cara)[0]
    Vectores_referencia = face_recognition.face_encodings(Cara, known_face_locations=[Localizacion_cara])[0]
    captura = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    tiempo_inicio = time.time()
    segundos_maximos = 20
    cv2.namedWindow("Camara_IA", cv2.WND_PROP_FULLSCREEN) 
    cv2.setWindowProperty("Camara_IA", cv2.WND_PROP_FULLSCREEN, cv2.WND_PROP_FULLSCREEN)
    contador = 0
    while True:
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        resultado, imagen = captura.read()
        contador += 1
        if not resultado:
            break
        
        imagen = cv2.flip(imagen, 1)
        if contador %6 == 0 : 
         Localizacion_cara_Frames = face_recognition.face_locations(imagen)
        
         if len(Localizacion_cara_Frames) > 0:
            Vectores_cara_Frames = face_recognition.face_encodings(imagen, known_face_locations=Localizacion_cara_Frames)[0]
            result = face_recognition.compare_faces([Vectores_referencia], Vectores_cara_Frames)
            if result[0]:
               
               print("Acceso Confirmado...")
               captura.release()
               cv2.destroyAllWindows()
               return "Bienvenido Marco"
        if tiempo_transcurrido > segundos_maximos:
           break
        
        cv2.imshow("Camara_IA", imagen)

        if cv2.waitKey(33) & 0xFF == ord("q"):
            break
   
    captura.release()
    cv2.destroyAllWindows()
    return "Persona extraña"

def Abrir_Apps(Aplicacion):
   # Abre apps por el BUSCADOR de Windows (tecla Win), sin depender de imagenes.
   # Esto es mucho mas confiable que ubicar un screenshot en pantalla.
   pyautogui.press("win")
   time.sleep(0.6)
   pyautogui.typewrite(Aplicacion, interval=0.04)
   time.sleep(0.7)
   pyautogui.press("enter")
   return f"Abriendo {Aplicacion}, señor."

def Abrir_WhattsApp(Aplicacion_os):
   os.startfile("whatsapp://")

def Abrir_Videos_Youtube(Tipo_Video):
   busqueda_limpia = urllib.parse.quote_plus(f"{Tipo_Video} youtube")
   webbrowser.open(f"https://www.google.com/search?q={busqueda_limpia}&btnI")
   return f"Reproduciendo {Tipo_Video}, señor"

def Buscar_en_Google(Pagina):
   busqueda_limpia = urllib.parse.quote_plus(f"{Pagina}")
   webbrowser.open(f"https://www.google.com/search?q={busqueda_limpia}")
   return f"Buscando {Pagina} en Google, señor"

def Salir():
   sys.exit()

def Programacion_de_Tareas(texto):
   texto = texto.strip()
   partes = texto.split("|")

   if len(partes)==4:

      accion = partes[0].strip()
      target = partes[1].strip()
      info = partes[2].strip()
      hora = partes[3].strip()
      guardar_en_json(accion,target,info,hora)

def limpiar_historial():
   if not os.path.exists("tareas.json"):
      return "No hay historial de tareas que limpiar, señor."

   with open("tareas.json","r") as f:
      tareas = json.load(f)

   tarea_limpia = []

   for t in tareas:
      if t["estado"] == "pendiente":
         tarea_limpia.append(t)

   with open("tareas.json","w") as f:
      json.dump(tarea_limpia,f,indent=4)

   return "Historial limpiado, señor."



   

      







   