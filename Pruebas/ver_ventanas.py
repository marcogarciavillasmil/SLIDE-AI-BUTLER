# Diagnóstico 2: ¿qué VENTANA aparece cuando me llaman? (WhatsApp no usa toast, usa ventana)
#
# CÓMO USARLO:
#   1. Terminal en la carpeta del proyecto (SLIDE-AI-BUTLER).
#   2. Ejecuta:  Asistente_Slide_311\Scripts\python.exe Pruebas\ver_ventanas.py
#   3. Cuando diga "ESCUCHANDO ventanas...", pídele a alguien que te LLAME (WhatsApp/Discord).
#   4. Mira lo que imprime con "[+] VENTANA NUEVA": ahí estará la ventana de la llamada,
#      con su TÍTULO y su CLASE. Cópiame esa línea y con eso construyo la detección.
#   5. Ctrl+C para salir.
#
# Imprime SOLO las ventanas que aparecen/cambian mientras corre, para que la de la llamada
# salte a la vista entre el ruido.

import os
import sys
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

import win32gui


def _ventanas_visibles():
    # {hwnd: (titulo, clase)} de todas las ventanas visibles CON título.
    res = {}

    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        titulo = win32gui.GetWindowText(hwnd)
        if not titulo or not titulo.strip():
            return
        try:
            clase = win32gui.GetClassName(hwnd)
        except Exception:
            clase = "?"
        res[hwnd] = (titulo.strip(), clase)

    win32gui.EnumWindows(_cb, None)
    return res


def main():
    print("=" * 70)
    print("ESCUCHANDO ventanas nuevas... (Ctrl+C para salir)")
    print("Ahora HAZTE UNA LLAMADA (WhatsApp/Discord) y mira las [+] VENTANA NUEVA.")
    print("=" * 70)
    previas = _ventanas_visibles()
    try:
        while True:
            actuales = _ventanas_visibles()
            for hwnd, (titulo, clase) in actuales.items():
                if hwnd not in previas:
                    print(f"[+] VENTANA NUEVA   titulo={titulo!r}   clase={clase!r}")
            for hwnd in previas:
                if hwnd not in actuales:
                    t, c = previas[hwnd]
                    print(f"[-] se cerro        titulo={t!r}   clase={c!r}")
            previas = actuales
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListo, fin del diagnostico.")


if __name__ == "__main__":
    main()
