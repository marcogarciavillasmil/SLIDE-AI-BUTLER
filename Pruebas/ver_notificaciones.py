# Diagnóstico: ¿Windows genera un toast cuando me llaman? ¿AIDEN lo detectaría?
#
# CÓMO USARLO:
#   1. Abre una terminal en la carpeta del proyecto (SLIDE-AI-BUTLER).
#   2. Ejecuta:  Asistente_Slide_311\Scripts\python.exe Pruebas\ver_notificaciones.py
#   3. Cuando diga "ESCUCHANDO...", pídele a alguien que te LLAME por WhatsApp/Discord.
#   4. Mira lo que imprime: cada notificación nueva sale con la app, el texto y si AIDEN
#      la marcaría como LLAMADA (>>> LLAMADA DETECTADA) o no (notificación normal).
#   5. Corta con Ctrl+C.
#
# Si tu llamada SALE aquí como ">>> LLAMADA DETECTADA", el vigilante funcionará.
# Si SALE pero como notificación normal, copia el texto y me lo pasas para afinar las pistas.
# Si NO SALE NADA al llamarte, esa app no está mandando toast (revisa que tenga notificaciones
# activadas en Configuración de Windows > Sistema > Notificaciones).

import os
import sys
import time

# Permite importar el proyecto aunque ejecutes el script desde la carpeta Pruebas.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from Funciones_Slide.Comunicacion.Vigilante_Llamadas import (
    _leer_nuevas, _max_arrival_actual, _es_llamada, _app_bonita, _quien_llama,
)


def main():
    umbral = _max_arrival_actual()
    print("=" * 70)
    print("ESCUCHANDO notificaciones nuevas... (Ctrl+C para salir)")
    print("Ahora HAZTE UNA LLAMADA de prueba (WhatsApp/Discord) y mira abajo.")
    print("=" * 70)
    try:
        while True:
            for app_id, texto, arrival in _leer_nuevas(umbral):
                if arrival > umbral:
                    umbral = arrival
                app = _app_bonita(app_id) or app_id or "(app desconocida)"
                es_llamada = _es_llamada(app_id, texto)
                if es_llamada:
                    quien = _quien_llama(texto, _app_bonita(app_id))
                    print(f"\n>>> LLAMADA DETECTADA  [{app}]  contacto: {quien or '(no identificado)'}")
                    print(f"    texto del toast: {texto!r}")
                else:
                    print(f"  notificacion normal  [{app}]  ->  {texto!r}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nListo, fin del diagnostico.")


if __name__ == "__main__":
    main()
