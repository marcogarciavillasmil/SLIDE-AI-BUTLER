from Cerebro import proceso_de_ia
from Transcriptor import escuchador_de_usuario
import Transcriptor
import Cerebro
from Herramientas_del_asistente import hablado_del_asistente
from Comandos_Asistente import Reconocimiento_Facial
from Comandos_Asistente import Abrir_Apps
from Comandos_Asistente import abrir_camara
from Comandos_Asistente import Abrir_Videos_Youtube
from Comandos_Asistente import Buscar_en_Google
from Comandos_Asistente import Salir
from Interfaz_En_Python import ejecutar_slide
from Comandos_Asistente import Programacion_de_Tareas
from Tareas_Hilos_Comandos import iniciar_hilos
from Funciones_Variadas import Enviar_mensaje_Whatsapp
from Funciones_Variadas import llamada_whatsapp
from VAD import Reconocimiento_de_habla

iniciar_hilos()



Prohibidas = ["HABLAR","FOTO","CAMARA","YOUTUBE","RECONOCIMIENTO","INTERNET","SALIR","PROGRAMAR","MENSAJE","LLAMAR","ESCONDER","MOSTRAR"]





def Etiquetas_Y_Acciones(texto,ventana):
    Etiqueta, texto_puro = proceso_de_ia(texto)
    texto_puro = texto_puro.strip()
    Etiqueta_limpia = Etiqueta.replace("[","").replace("]","").strip()
    ventana.enviar_texto_a_html(f"SLIDE >> {texto_puro}", "#d500f9")
    print(Etiqueta_limpia)

    hablado_del_asistente(texto_puro)
    

    if Etiqueta_limpia not in Prohibidas:
     print("entro pyauto")
     print(Etiqueta_limpia)
     Abrir_Apps(Etiqueta_limpia)
    elif Etiqueta_limpia == "FOTO" or Etiqueta_limpia == "CAMARA":
     abrir_camara()
    elif Etiqueta_limpia == "YOUTUBE":
     
     i,c,r = texto_puro.partition("[")
     busqueda = c + r
     busqueda_limpia = busqueda.replace("[","").replace("]","").strip()
     Abrir_Videos_Youtube(busqueda_limpia)

    elif Etiqueta_limpia == "RECONOCIMIENTO":
     Reconocimiento_Facial()
    elif Etiqueta_limpia == "INTERNET":
      print("Entro internet")
      i,c,r = texto_puro.partition("[")
      busqueda = c + r
      busqueda_limpia = busqueda.replace("[","").replace("]","").strip()
      Buscar_en_Google(busqueda_limpia)
    elif Etiqueta_limpia=="PROGRAMAR":
      Programacion_de_Tareas(texto_puro)
      hablado_del_asistente("Tarea programada con exito, señor")
    elif Etiqueta_limpia == "MENSAJE":
    
      i,c,r = texto_puro.partition("[")
      nombre = c+r
      print(nombre)
      nombre = nombre.replace("[","").replace("]","").strip()
      mensaje = texto_puro.split("|")[1].strip()
      print(nombre)
      print(mensaje)
      
      Enviar_mensaje_Whatsapp(nombre,mensaje)

    elif Etiqueta_limpia=="LLAMAR":
      print("entro a llamar")
      i,c,r = texto_puro.partition("[")
      nombre = c+r
      nombre = nombre.replace("[","").replace("]","").strip()
      llamada_whatsapp(nombre)
    elif Etiqueta_limpia == "SALIR":
      Salir()
def Voz(ventana_slide):
    ventana_slide.enviar_texto_a_html("SLIDE >> Escuchando...", "#00ffcc")
    texto_escuchado = escuchador_de_usuario()
    ventana_slide.enviar_texto_a_html(f"USER (Voz) >> {texto_escuchado}", "#ffffff")
    

    Etiquetas_Y_Acciones(texto_escuchado, ventana_slide)


hablado_del_asistente("Iniciando sistema de seguridad...")
print("Iniciando sistema de seguridad...")






verificacion = Reconocimiento_Facial()


Activado, Texto = Reconocimiento_de_habla()
if verificacion == "Bienvenido Marco":
 hablado_del_asistente("Bienvenido marco")
 while Activado: 
 
  hablado_del_asistente("Hola señor, en que lo puedo ayudar hoy")
  ejecutar_slide(funcion_texto=Etiquetas_Y_Acciones,funcion_voz=Voz)
  Activado, Texto = Reconocimiento_de_habla()



else:
   hablado_del_asistente("Acceso denegado")
   print("Acceso denegado")
   verificacion = Reconocimiento_Facial()




    