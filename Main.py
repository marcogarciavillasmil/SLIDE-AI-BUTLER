from Voz_Slide.Transcriptor import escuchador_de_usuario
from Nucleo_Slide.Cerebro import proceso_de_ia
from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
from Funciones_Slide.Tareas_Hilos_Comandos import iniciar_hilos
from Funciones_Slide.Comandos_Asistente import Reconocimiento_Facial
from Voz_Slide.VAD import Reconocimiento_de_habla
from Interfaz.Interfaz_En_Python import ejecutar_slide
from Funciones_Slide.Comandos_Asistente import Abrir_Apps
from Funciones_Slide.Funciones_Variadas import Enviar_mensaje_Whatsapp
from Funciones_Slide.Comandos_Asistente import Abrir_Apps
from Nucleo_Slide.Cerebro import iniciar_centinela, estado_aiden
iniciar_hilos()



def Procesar_Peticion(texto, ventana):
  
    texto = texto.strip()
    
    texto = texto.lower()

    if "abre " in texto:
        
        abrir_a_app = texto.split("abre ")[1].strip() 
        
        Abrir_Apps(abrir_a_app)
        respuesta_slide = f"Hecho señor, aplicación {abrir_a_app} abierta."

    elif texto.startswith("escribele a "):
      
      partes = texto.replace("escribele a ","").split(" diciendo ")
      
      if len(partes) == 2: 
        contacto = partes[0].strip()
        mensaje = partes[1].strip()
        
        Enviar_mensaje_Whatsapp(contacto,mensaje)

        respuesta_slide =f"Mensaje enviado a {contacto}, señor."
      else:
         respuesta_slide = "El mensaje no se pudo enviar"

    elif "cambié de opinión" in texto or "ayúdame con el código" in texto or "ayudame" in texto:
        if estado_aiden["hay_error"]:
            ventana.enviar_texto_a_html("AIDEN >> Revisando la memoria de errores...", "#d500f9")
            prompt = f"Hay un SyntaxError: '{estado_aiden['detalle_error']}' en la línea {estado_aiden['linea']}. Código: \n{estado_aiden['codigo']}\nDame una solución corta."
            respuesta_slide = proceso_de_ia(prompt)
        else:
            respuesta_slide = "No tengo registros de errores de sintaxis en su código actualmente, señor."

    
    else:
        
     respuesta_slide = proceso_de_ia(texto) 
    
    ventana.enviar_texto_a_html(f"AIDEN >> {respuesta_slide}", "#d500f9")
    print(f"AIDEN: {respuesta_slide}")
    hablado_del_asistente(respuesta_slide)

def Voz(ventana_slide):
    ventana_slide.enviar_texto_a_html("AIDEN >> Escuchando...", "#00ffcc")
    texto_escuchado = escuchador_de_usuario()
    ventana_slide.enviar_texto_a_html(f"USER (Voz) >> {texto_escuchado}", "#ffffff")
    
    Procesar_Peticion(texto_escuchado, ventana_slide)


hablado_del_asistente("Iniciando sistema de seguridad...")
print("Iniciando sistema de seguridad...")

verificacion = Reconocimiento_Facial()
Activado, Texto = Reconocimiento_de_habla()

if verificacion == "Bienvenido Marco":
    hablado_del_asistente("Bienvenido Marco")
    ejecutar_slide(funcion_texto=Procesar_Peticion, funcion_voz=Voz) 
    
    while Activado: 
        hablado_del_asistente("Hola señor, ¿en qué lo puedo ayudar hoy?")
        
        
        ejecutar_slide(funcion_texto=Procesar_Peticion, funcion_voz=Voz) 
        
        Activado, Texto = Reconocimiento_de_habla()

else:
    hablado_del_asistente("Acceso denegado")
    print("Acceso denegado")


  



    