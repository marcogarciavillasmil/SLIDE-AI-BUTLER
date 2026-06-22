# ─────────────────────────────────────────────────────────────────────────────
# AIDEN — versión ALWAYS-ON (siempre encendido)
#
# Diferencia con Main.py: AIDEN hace login UNA sola vez y luego vive en un bucle
# infinito que NUNCA termina, alternando:
#   - REPOSO: escucha la palabra clave (barato; Whisper/Kokoro/LLM en reposo).
#   - ACTIVO: abre la esfera y conversa; al cerrar la ventana, vuelve a REPOSO.
# Si la palabra clave no se detecta, sigue esperando (no se apaga).
#
# Es un archivo APARTE: Main.py queda intacto. Para probarlo: F5 sobre este archivo.
# Si te convence, cambia el lanzador (AIDEN.bat) para que corra Main_AlwaysOn.py.
# ─────────────────────────────────────────────────────────────────────────────

# ── INSTANCIA ÚNICA ───────────────────────────────────────────────────────────
# Si AIDEN ya está corriendo, esta copia se cierra de inmediato (antes de cargar
# modelos) para no duplicar el asistente ni gastar el doble de memoria.
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
from Interfaz.Interfaz_En_Python import SlideHUD
import Interfaz.Interfaz_En_Python as interfaz
import sys
import os
import threading
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
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
        elif any(p in texto for p in ("quédate", "quedate", "mantente", "no te ocultes")):
            ventana.pedir_fijar.emit(True)
            respuesta_slide = "Aquí me quedo, señor."
        elif any(p in texto for p in ("ocúltate", "ocultate", "escóndete", "escondete", "ya descansa", "puedes descansar")):
            ventana.pedir_fijar.emit(False)
            ventana.pedir_ocultar.emit()
            respuesta_slide = "Como guste, señor."

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


# ── ARRANQUE (always-on con inversión de Qt) ─────────────────────────────────
# Arquitectura:
#   - HILO PRINCIPAL = Qt: app + ventana (persistente, oculta) + icono en bandeja,
#     corriendo SIEMPRE con app.exec(). Eso da el "vive de fondo" y el tray reactivo.
#   - HILO DE FONDO  = cerebro de REPOSO: escucha la palabra clave (micrófono) y,
#     al detectarla, pide MOSTRAR la ventana (por señal). La conversación dentro de
#     la ventana sigue igual que siempre (clic en la esfera -> Voz; escribir -> texto).
#   - La ventana se oculta sola tras 60s de inactividad (timer) -> vuelve a REPOSO.
# DECISIÓN DE SEGURIDAD: el login FACIAL (cámara) se hace en el HILO PRINCIPAL (como
# Main.py, que ya funciona). Solo la escucha de palabra clave (mic) va al hilo de fondo,
# para evitar el bug conocido de abrir la cámara en un hilo secundario.

# Control remoto por Telegram: arranca primero (control desde el celular aunque no estés).
iniciar_telegram()

hablado_del_asistente("Iniciando sistema de seguridad...")
print("Iniciando sistema de seguridad...")

# LOGIN: una sola vez, en el hilo principal (cámara).
verificacion = Reconocimiento_Facial()

if verificacion != "Bienvenido Marco":
    hablado_del_asistente("Acceso denegado")
    print("Acceso denegado")
    sys.exit(0)

# Login OK: briefing + arranque de hilos de fondo (todo una sola vez).
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

# ── Qt en el hilo principal ───────────────────────────────────────────────────
# Las funciones que usa la ventana para conversar (event-driven, sin cambios):
interfaz._funcion_texto_externa = Procesar_Peticion
interfaz._funcion_voz_externa = Voz

app = QApplication.instance()
if not app:
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)   # no se cierra al ocultar la ventana

ventana = SlideHUD()
ventana.modo_persistente = True                 # cerrar = ocultar (no destruir)
_evento_oculto = threading.Event()
ventana.al_ocultar = _evento_oculto.set         # avisa al cerebro cuando se oculta
# La ventana arranca OCULTA: AIDEN vive en la bandeja hasta la palabra clave.

# ── Icono en la bandeja del sistema ──────────────────────────────────────────
_ruta_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AIDEN.ico")
tray = QSystemTrayIcon()
if os.path.exists(_ruta_ico):
    tray.setIcon(QIcon(_ruta_ico))
tray.setToolTip("AIDEN — asistente activo")
_menu = QMenu()
_act_mostrar = QAction("Mostrar AIDEN")
_act_mostrar.triggered.connect(lambda *_: ventana.pedir_mostrar.emit())
_act_salir = QAction("Salir")
_act_salir.triggered.connect(lambda *_: app.quit())
_menu.addAction(_act_mostrar)
_menu.addAction(_act_salir)
tray.setContextMenu(_menu)
# Clic en el icono de la bandeja -> muestra AIDEN (cualquier tipo de clic).
tray.activated.connect(lambda *_: ventana.pedir_mostrar.emit())
tray.show()
try:
    tray.showMessage("AIDEN", "En línea, señor. Diga la palabra clave cuando me necesite.")
except Exception:
    pass

# ── Cerebro de REPOSO en hilo de fondo (solo micrófono) ──────────────────────
def bucle_reposo():
    while True:
        Activado, _Texto = Reconocimiento_de_habla()   # REPOSO: escucha la palabra clave
        if not Activado:
            continue                                    # no detectada -> sigue esperando (no se apaga)
        # ACTIVO: pide mostrar la ventana (en el hilo principal) y espera a que se oculte.
        _evento_oculto.clear()
        ventana.pedir_mostrar.emit()
        _evento_oculto.wait()                           # la ventana se oculta tras 60s o al cerrarla
        # vuelve arriba a REPOSO

threading.Thread(target=bucle_reposo, daemon=True).start()

# Qt corre para siempre aquí (esto es lo "always-on"); se sale solo con "Salir" del tray.
sys.exit(app.exec())