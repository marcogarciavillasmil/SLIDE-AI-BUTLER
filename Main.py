# ── INSTANCIA ÚNICA ───────────────────────────────────────────────────────────
# Si AIDEN ya está corriendo (este Main.py o Main_AlwaysOn.py), esta copia se cierra
# de inmediato para no duplicar el asistente ni gastar el doble de memoria.
import sys as _sys
import socket as _socket
_instancia_lock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
try:
    _instancia_lock.bind(("127.0.0.1", 50607))
except OSError:
    print("AIDEN ya está corriendo; cierro esta instancia para no duplicar.")
    _sys.exit(0)

from Voz_Slide.Transcriptor import escuchador_de_usuario
from Nucleo_Slide.Cerebro import proceso_de_ia, iniciar_centinela, estado_aiden
import Nucleo_Slide.Cerebro as cerebro   # para leer cerebro.ultima_interrumpida
from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
from Funciones_Slide.Productividad.Tareas_Hilos_Comandos import iniciar_hilos
from Funciones_Slide.Sistema.Comandos_Asistente import Reconocimiento_Facial, Abrir_Apps
from Voz_Slide.VAD import Reconocimiento_de_habla
from Interfaz.Interfaz_En_Python import ejecutar_slide
from Funciones_Slide.Comunicacion.Funciones_Variadas import Enviar_mensaje_Whatsapp
from Funciones_Slide.Sistema.Funciones_Sistema import control_musica
from Funciones_Slide.Productividad.Rutina import briefing
from Funciones_Slide.Productividad.Alertas_Mercado import iniciar_alertas
from Funciones_Slide.Productividad.Descanso import iniciar_guardian_descanso
from Funciones_Slide.Info.Bitacora import contar_actividad
from Funciones_Slide.Comunicacion.Telegram_Control import iniciar_telegram
from Funciones_Slide.Productividad.Anticipacion import iniciar_anticipacion
from Funciones_Slide.Sistema.Presencia import iniciar_presencia
iniciar_hilos()



def Procesar_Peticion(texto, ventana):
    # El while permite el "barge-in": si AIDEN es interrumpido, volvemos a
    # escuchar al usuario de inmediato (sin repetir la palabra clave).
    while texto and texto.strip():
        texto = texto.strip().lower()
        ya_hablado = False

        if "abre " in texto:
            abrir_a_app = texto.split("abre ")[1].strip()
            Abrir_Apps(abrir_a_app)
            respuesta_slide = f"Hecho señor, aplicación {abrir_a_app} abierta."

        elif texto.startswith("escribele a "):
            partes = texto.replace("escribele a ", "").split(" diciendo ")
            if len(partes) == 2:
                contacto = partes[0].strip()
                mensaje = partes[1].strip()
                Enviar_mensaje_Whatsapp(contacto, mensaje)
                respuesta_slide = f"Mensaje enviado a {contacto}, señor."
            else:
                respuesta_slide = "El mensaje no se pudo enviar"

        elif texto in ("pausa", "pausar", "reanuda", "play", "siguiente", "siguiente cancion",
                       "anterior", "cancion anterior", "detener", "parar", "para la musica"):
            # Atajo SIN LLM (cuesta $0): comandos de musica directos.
            _mapa = {"pausa": "pausa", "pausar": "pausa", "reanuda": "play", "play": "play",
                     "siguiente": "siguiente", "siguiente cancion": "siguiente",
                     "anterior": "anterior", "cancion anterior": "anterior",
                     "detener": "parar", "parar": "parar", "para la musica": "parar"}
            respuesta_slide = control_musica(_mapa[texto])

        elif "cambié de opinión" in texto or "ayúdame con el código" in texto or "ayudame" in texto:
            if estado_aiden["hay_error"]:
                ventana.enviar_texto_a_html("AIDEN >> Revisando la memoria de errores...", "#d500f9")
                prompt = f"Hay un SyntaxError: '{estado_aiden['detalle_error']}' en la línea {estado_aiden['linea']}. Código: \n{estado_aiden['codigo']}\nDame una solución corta."
                respuesta_slide = proceso_de_ia(prompt)
                ya_hablado = True
            else:
                respuesta_slide = "No tengo registros de errores de sintaxis en su código actualmente, señor."

        else:
            respuesta_slide = proceso_de_ia(texto)
            ya_hablado = True

        ventana.enviar_texto_a_html(f"AIDEN >> {respuesta_slide}", "#d500f9")
        print(f"AIDEN: {respuesta_slide}")

        # ¿AIDEN fue interrumpido al hablar?
        if ya_hablado:
            interrumpido = cerebro.ultima_interrumpida          # vino de proceso_de_ia
        else:
            interrumpido = hablado_del_asistente(respuesta_slide)  # frases fijas

        if interrumpido:
            ventana.enviar_texto_a_html("AIDEN >> (te escucho...)", "#00ffcc")
            print("[BARGE-IN] escuchando al usuario sin palabra clave...")
            texto = escuchador_de_usuario()   # captura el nuevo comando
            ventana.enviar_texto_a_html(f"USER (Voz) >> {texto}", "#ffffff")
            print(f"USER (Voz): {texto}")
            continue                          # y lo procesa en la siguiente vuelta

        # Conversación continua: ventana corta para un follow-up sin repetir la palabra clave.
        ventana.enviar_texto_a_html("AIDEN >> (sigo aquí, señor...)", "#00ffcc")
        seguimiento = escuchador_de_usuario(timeout=5)   # 5s para que sigas hablando
        if seguimiento and seguimiento.strip():
            texto = seguimiento
            ventana.enviar_texto_a_html(f"USER (Voz) >> {texto}", "#ffffff")
            print(f"USER (Voz): {texto}")
            continue
        break

def Voz(ventana_slide):
    ventana_slide.enviar_texto_a_html("AIDEN >> Escuchando...", "#00ffcc")
    texto_escuchado = escuchador_de_usuario()
    ventana_slide.enviar_texto_a_html(f"USER (Voz) >> {texto_escuchado}", "#ffffff")
    Procesar_Peticion(texto_escuchado, ventana_slide)


# El control remoto por Telegram arranca ANTES del login facial y la palabra clave,
# para poder controlar el PC desde el celular AUNQUE Marco no esté presente.
# Su seguridad es independiente: queda bloqueado a tu chat_id (no necesita la cámara).
iniciar_telegram()

hablado_del_asistente("Iniciando sistema de seguridad...")
print("Iniciando sistema de seguridad...")

verificacion = Reconocimiento_Facial()

if verificacion == "Bienvenido Marco":
    # Solo esperamos la palabra clave si el login facial fue exitoso.
    # (Antes esto corria SIEMPRE: si entraba un extrano, AIDEN se quedaba
    #  escuchando para siempre sin negar el acceso hasta que alguien hablara.)
    Activado, Texto = Reconocimiento_de_habla()
    hablado_del_asistente("Bienvenido Marco")
    hablado_del_asistente(briefing())
    _n_notis = contar_actividad()
    if _n_notis > 0:
        hablado_del_asistente(
            f"Por cierto señor, mientras no estaba llegaron {_n_notis} notificaciones. "
            "Si quiere saber qué pasó, pídame el resumen."
        )
    iniciar_alertas(hablado_del_asistente)
    iniciar_guardian_descanso(hablado_del_asistente)
    iniciar_anticipacion(hablado_del_asistente)   # anticipación proactiva (clima, trasnochadas)
    iniciar_presencia(hablado_del_asistente)      # te saluda al llegar al PC (ve tu cara)
    ejecutar_slide(funcion_texto=Procesar_Peticion, funcion_voz=Voz)
    
    while Activado: 
        hablado_del_asistente("Iniciando sistemas...")
        
        
        ejecutar_slide(funcion_texto=Procesar_Peticion, funcion_voz=Voz) 
        
        Activado, Texto = Reconocimiento_de_habla()

else:
    hablado_del_asistente("Acceso denegado")
    print("Acceso denegado")






    