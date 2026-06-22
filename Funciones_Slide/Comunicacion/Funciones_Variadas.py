import os 
import webbrowser
import pyautogui
import time
import importlib
from Nucleo_Slide import Auto_Programacion
import ast
import threading
import queue

from secretos import CONTACTOS as contactos   # los telefonos viven en secretos.py (fuera de git)

def Enviar_mensaje_Whatsapp(nombre_contacto,mensaje):
    nombre_limpio= nombre_contacto.strip().upper()

    if nombre_limpio in contactos:
        numero = contactos[nombre_limpio]
        mensaje= mensaje.replace(" ","%20")
        App = f"whatsapp://send?phone={numero}&text={mensaje}"

        os.startfile(App)

        time.sleep(4)

        pyautogui.press("enter")
        return "Mensaje enviado correctamente señor"
    else:
        return "Contacto no econtrado/registrado"
    
def colgar():
    pyautogui.moveTo(1000,600)
    pyautogui.click()
    pyautogui.press("tab",presses=7,interval=0.1)
    pyautogui.press("enter")
    return "Llamada finalizada, señor"

    
def llamada_whatsapp(nombre_contacto):
    nombre_limpio = nombre_contacto.strip().upper()

    if nombre_limpio in contactos:
        numero = contactos[nombre_limpio]
        App = f"whatsapp://send?phone={numero}"
        os.startfile(App)

        time.sleep(3)

        pyautogui.press("tab",presses=10,interval=0.1)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.moveTo(1550,160)
        pyautogui.click()
        return f"Llamando a {nombre_contacto}, señor"
    else:
        return "Ese contacto no está registrado, señor"
def Auto_Modificacion(nombre_habilidad, instruccion):
    # Hace que AIDEN APRENDA una habilidad nueva para SI MISMO usando Claude Code: le pide
    # escribir la funcion en Nucleo_Slide/Auto_Programacion.py y la recarga en vivo. Corre en
    # SEGUNDO PLANO (es lento) y avisa por voz al terminar. (Antes el LLM escribia el codigo a
    # mano; ahora lo escribe Claude Code, mucho mas confiable.) Para un PROYECTO/app aparte:
    # crear_proyecto.
    import shutil
    import subprocess

    nombre_habilidad = str(nombre_habilidad or "").strip()
    instruccion = str(instruccion or "").strip()
    if not nombre_habilidad or not instruccion:
        return "Necesito el nombre de la habilidad y que debe hacer, senor."

    claude = shutil.which("claude") or os.path.join(
        os.path.expanduser("~"), ".local", "bin", "claude.exe"
    )
    if not claude or not os.path.exists(claude):
        return "No encuentro Claude Code, senor; no puedo programar la habilidad."

    ruta_archivo = os.path.abspath(Auto_Programacion.__file__)
    repo = os.path.dirname(os.path.dirname(ruta_archivo))   # raiz del repo

    def _trabajo():
        from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
        try:
            prompt = (
                "Eres el programador de AIDEN. AGREGA UNA sola funcion de Python llamada exactamente "
                "'" + nombre_habilidad + "' al FINAL del archivo Nucleo_Slide/Auto_Programacion.py. "
                "Debe hacer: " + instruccion + ". REGLAS ESTRICTAS: no modifiques NINGUN otro archivo "
                "ni el codigo existente; SOLO agrega la funcion nueva al final de ese archivo; "
                "autocontenida y funcional (imports dentro de la funcion si hace falta); que DEVUELVA "
                "un texto de resultado; no la ejecutes. Responde corto."
            )
            subprocess.run(
                [claude, "-p", prompt, "--permission-mode", "bypassPermissions"],
                cwd=repo, capture_output=True, text=True, timeout=600,
                encoding="utf-8", errors="replace",
            )
            # Validar sintaxis ANTES de recargar (que un mal cambio no rompa a AIDEN).
            with open(ruta_archivo, encoding="utf-8") as f:
                codigo = f.read()
            try:
                compile(codigo, ruta_archivo, "exec")
            except SyntaxError:
                hablado_del_asistente(
                    "Senor, la habilidad " + nombre_habilidad + " quedo con un error de sintaxis; no la active."
                )
                return
            importlib.reload(Auto_Programacion)
            hablado_del_asistente("Senor, habilidad adquirida: " + nombre_habilidad + ".")
        except subprocess.TimeoutExpired:
            hablado_del_asistente("Senor, programar " + nombre_habilidad + " tardo demasiado y lo detuve.")
        except Exception as e:
            hablado_del_asistente("Senor, no pude programar " + nombre_habilidad + ": " + str(e))

    threading.Thread(target=_trabajo, daemon=True).start()
    return ("Programando la habilidad '" + nombre_habilidad + "' con Claude Code, senor. "
            "Le aviso en cuanto la tenga lista.")


