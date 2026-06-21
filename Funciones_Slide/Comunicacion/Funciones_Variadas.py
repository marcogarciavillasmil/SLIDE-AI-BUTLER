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
def Auto_Modificacion(nombre_habilidad, codigo_python):
    try:
        compile(codigo_python, '<string>', 'exec')
    except SyntaxError as e:
        print(f"Sintaxis invalida: {e}")
        return f"Error de sintaxis: {e}. No guardé el código, corrígelo e inténtalo de nuevo."

    try:
        # Escribimos en el MISMO archivo que luego recargamos (su ruta real).
        ruta = Auto_Programacion.__file__
        with open(ruta, "a", encoding="utf-8") as auto_progra:
            auto_progra.write(f"\n\n# --- Habilidad: {nombre_habilidad} ---\n")
            auto_progra.write(codigo_python + "\n")
        # El reload va FUERA del with, ya con el archivo cerrado y guardado.
        importlib.reload(Auto_Programacion)
        print("Habilidad creada exitosamente")
        return f"Señor, programé la habilidad: {nombre_habilidad}"
    except Exception as e:
        print(f"ERROR al cargar el nuevo código: {e}")
        return f"El código tiene un error de lógica: {e}, genera una nueva versión."


