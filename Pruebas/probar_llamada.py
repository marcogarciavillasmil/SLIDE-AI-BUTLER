# Prueba aislada del vigilante de llamadas (sin arrancar todo AIDEN).
#
# Comprueba las 2 cosas inciertas: (1) que detecte la VENTANA de la llamada, y (2) que encuentre
# y pulse el botón "Accept". Imprime TODOS los botones de la ventana, así si "Accept" tiene otro
# nombre en tu idioma lo vemos y lo ajusto.
#
# CÓMO USARLO:
#   1. Terminal en la carpeta del proyecto (SLIDE-AI-BUTLER).
#   2. Ejecuta:  Asistente_Slide_311\Scripts\python.exe Pruebas\probar_llamada.py
#   3. Cuando diga "ESPERANDO una llamada...", pídele a alguien que te LLAME por WhatsApp.
#   4. Mira lo que imprime y NO contestes tú (deja que el script intente aceptarla).
#   5. Ctrl+C para salir.
#
# OJO: este script SÍ intentará ACEPTAR la llamada de verdad (para probar el botón). NO habla el
# mensaje por el cable (eso lo hace AIDEN completo); aquí solo verificamos detectar + aceptar.

import os
import sys
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import uiautomation as auto
from Funciones_Slide.Comunicacion.Vigilante_Llamadas import (
    _ventanas_llamada, aceptar_ventana,
)

GRACIA_PRUEBA = 6   # en la prueba esperamos menos que en producción


def _listar_botones(hwnd):
    print("    Botones que veo en esa ventana:")
    try:
        ventana = auto.ControlFromHandle(hwnd)
        if not ventana:
            print("    (no pude leer el contenido de la ventana)")
            return
        encontrados = 0
        for ctrl, _depth in auto.WalkControl(ventana, maxDepth=12):
            if ctrl.ControlTypeName == "ButtonControl":
                print(f"      - boton: {ctrl.Name!r}")
                encontrados += 1
        if not encontrados:
            print("    (no encontré botones legibles)")
    except Exception as e:
        print(f"    (error leyendo botones: {e})")


def main():
    print("=" * 70)
    print("ESPERANDO una llamada... (Ctrl+C para salir)")
    print("Hazte una llamada por WhatsApp y NO contestes tú; deja que el script lo intente.")
    print("=" * 70)
    ya_vistas = set()
    try:
        while True:
            for hwnd, app in _ventanas_llamada().items():
                if hwnd in ya_vistas:
                    continue
                ya_vistas.add(hwnd)
                print(f"\n[DETECTADA] llamada de: {app or '(app desconocida)'}  (hwnd={hwnd})")
                _listar_botones(hwnd)
                print(f"    Esperando {GRACIA_PRUEBA}s y luego intento ACEPTAR...")
                time.sleep(GRACIA_PRUEBA)
                ok = aceptar_ventana(hwnd)
                if ok:
                    print("    ✓ PULSÉ el botón de aceptar. ¿Se contestó la llamada?")
                else:
                    print("    ✗ NO encontré/pulsé el botón (¿ya la contestaste? ¿otro nombre?).")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListo, fin de la prueba.")


if __name__ == "__main__":
    main()
