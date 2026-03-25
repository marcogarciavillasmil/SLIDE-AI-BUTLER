import os 
import webbrowser
import pyautogui
import time

contactos = {
    "TITO": "573213547181",
    "MAMA": "573106991593",
    "JOSHUA": "573115194605",
    "PIXEL": "573113689898",
    "BREINER": "573223644002",
    "KARL": "573124268607",
    "JULIAN": "573192320594",
    "HERMANA": "573113890459",
    "WALDO": "573003258008",
    "TAILTWO": "573025596995",
    "ALONSO": "573223087219",
    "LUNA": "573133398274",
    "CAMILO": "573229524240"
}

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
        
        #time.sleep(4)




