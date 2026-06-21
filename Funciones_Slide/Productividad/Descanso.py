import time
import threading
import ctypes


class _LASTINPUT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def _idle_segundos():
    # Cuántos segundos lleva el usuario SIN tocar teclado/mouse.
    info = _LASTINPUT()
    info.cbSize = ctypes.sizeof(info)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0


def _bucle(hablar):
    activo_continuo = 0.0
    INTERVALO = 60          # revisa cada minuto
    LIMITE = 2 * 3600       # avisa tras 2 horas de actividad continua
    while True:
        time.sleep(INTERVALO)
        try:
            if _idle_segundos() < 300:        # activo (menos de 5 min quieto)
                activo_continuo += INTERVALO
                if activo_continuo >= LIMITE:
                    hablar("Señor, lleva un buen rato sin parar. Le recomiendo descansar la vista unos minutos.")
                    activo_continuo = 0.0
            else:
                activo_continuo = 0.0          # tomó un descanso -> reinicia el conteo
        except Exception:
            pass


def iniciar_guardian_descanso(hablar):
    threading.Thread(target=_bucle, args=(hablar,), daemon=True).start()
