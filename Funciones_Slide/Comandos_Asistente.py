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
from Funciones_Slide.Gestion_datos import guardar_en_json
import json





captura = cv2.VideoCapture(0, cv2.CAP_DSHOW)
Cara = cv2.imread(os.path.join(os.path.dirname(os.path.dirname(__file__)), "Imagenes", "Marco.jpg"))

def abrir_camara(): 
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

def Reconocimiento_Facial():

    Localizacion_cara = face_recognition.face_locations(Cara)[0]
    Vectores_referencia = face_recognition.face_encodings(Cara, known_face_locations=[Localizacion_cara])[0]
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
   
   
   _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   ubicacion = pyautogui.locateOnScreen(
       os.path.join(_base, "Guias_Python", "Buscador_Guia3.png"), confidence=0.7
   )

   if ubicacion is not None:
      centrado = pyautogui.center(ubicacion)
      pyautogui.moveTo(centrado)
      pyautogui.click()
      pyautogui.write(Aplicacion,interval=0.095)
      pyautogui.press("enter")

      #ubicacion2 = pyautogui.locateOnScreen(r"C:\Users\Usuario\Desktop\Python Proyecto\Guias_Python\Icono_Abrir.png", confidence=0.4)
   
      #if ubicacion2 is not None:
       #centrado = pyautogui.center(ubicacion2)
       #pyautogui.moveTo(centrado)
       #pyautogui.click() 
       #print("Ejecutado Correctamente")       
   else:
      print("No se encontro la Aplicacion")

def Abrir_WhattsApp(Aplicacion_os):
   os.startfile("whatsapp://")

def Abrir_Videos_Youtube(Tipo_Video):
   busqueda_limpia = urllib.parse.quote_plus(f"{Tipo_Video} youtube")
   webbrowser.open(f"https://www.google.com/search?q={busqueda_limpia}&btnI")

def Buscar_en_Google(Pagina):
   busqueda_limpia = urllib.parse.quote_plus(f"{Pagina}")
   webbrowser.open(f"https://www.google.com/search?q={busqueda_limpia}&btnI")

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
   with open("tareas.json","r") as f: 
      tareas = json.load(f)

   tarea_limpia = []

   for t in tareas:
      if t["estado"] == "pendiente":
         tarea_limpia.append(t)

   with open("tareas.json","w") as f: 
      json.dump(tarea_limpia,f,ident=4)



   

      







   