# Anticipación proactiva: AIDEN toma la INICIATIVA y avisa cosas útiles solo cuando
# tienen sentido, SIN que Marco pregunte. Diseño anti-molestia:
#   - Cada tipo de aviso se da MÁXIMO una vez al día.
#   - Solo en franjas horarias sensatas.
#   - Se PAUSA en modo gaming (y se puede pausar a mano).
# No necesita credenciales: usa el pronóstico del clima que ya tiene AIDEN.

import os
import re
import threading
import time
from datetime import datetime, date

import psutil

from Funciones_Slide.Sistema.Funciones_Sistema import pronostico_clima

try:
    from secretos import PORTAFOLIO
except Exception:
    PORTAFOLIO = {}

CIUDAD = "Bogota"
INTERVALO = 20 * 60          # revisa cada 20 minutos
DISCO_LIMITE = 90           # % de disco lleno para avisar
RAM_LIMITE = 90            # % de RAM para avisar
GPU_TEMP_LIMITE = 85        # °C de GPU para avisar
GPU_COOLDOWN = 3600         # s entre avisos de GPU caliente

_RUTA_NOTAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notas.txt"
)

_pausado = False
_ya_avisado = {}             # {tipo: date} para no repetir el mismo aviso el mismo día
_ultimo_aviso_gpu = 0        # timestamp del último aviso de GPU caliente (cooldown)
_internet_caido = False      # estado previo de la conexión (para avisar solo en el cambio)


def pausar_anticipacion(pausar=True):
    # Permite silenciar la anticipación (lo usa el modo gaming).
    global _pausado
    _pausado = bool(pausar)


def _ya_hoy(tipo):
    return _ya_avisado.get(tipo) == date.today()


def _marcar(tipo):
    _ya_avisado[tipo] = date.today()


def _contar_notas():
    try:
        if not os.path.exists(_RUTA_NOTAS):
            return 0
        with open(_RUTA_NOTAS, "r", encoding="utf-8") as f:
            return sum(1 for l in f if l.strip())
    except Exception:
        return 0


def _disco_mas_lleno():
    # Devuelve (porcentaje, unidad) del disco más lleno si supera el límite; si no, None.
    try:
        peor = None
        for p in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(p.mountpoint)
            except Exception:
                continue
            if u.percent >= DISCO_LIMITE and (peor is None or u.percent > peor[0]):
                peor = (u.percent, p.device)
        return peor
    except Exception:
        return None


def _gpu_temperatura():
    try:
        import subprocess
        o = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip().splitlines()
        return int(o[0]) if o else None
    except Exception:
        return None


def _hay_internet():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.connect(("8.8.8.8", 80))
        s.close()
        return True
    except Exception:
        return False


def _avisos_clima():
    # Devuelve la lista de avisos del clima de hoy (lluvia/frío), [] si no hay nada
    # que avisar, o None si no se pudo obtener el pronóstico (error transitorio).
    try:
        info = pronostico_clima(CIUDAD, 1)
        low = info.lower()
        if "máx" not in low and "mín" not in low:
            return None   # sin datos válidos -> que reintente en el próximo ciclo
        avisos = []
        if any(p in low for p in ("lluvia", "llovizna", "tormenta", "chubasco", "rain")):
            avisos.append("se espera lluvia, le sugiero llevar sombrilla")
        m = re.search(r"mín\s*(-?\d+)", low)
        if m and int(m.group(1)) <= 9:
            avisos.append("la mañana está fría, abríguese bien")
        return avisos
    except Exception:
        return None


def _revisar(hablar):
    if _pausado:
        return
    h = datetime.now().hour

    # ── CLIMA DEL DÍA (mañana, 6–11h): lluvia y/o frío. Una vez al día. ───────────
    if 6 <= h < 11 and not _ya_hoy("clima"):
        avisos = _avisos_clima()
        if avisos is not None:          # None = error transitorio -> no marca, reintenta
            _marcar("clima")
            if avisos:
                hablar("Señor, para hoy en Bogotá: " + " y ".join(avisos) + ".")

    # ── TRASNOCHADA (1–4h): empujón a descansar. Una vez al día. ──────────────────
    if 1 <= h < 4 and not _ya_hoy("trasnoche"):
        _marcar("trasnoche")
        hablar("Señor, ya es de madrugada. Le recomiendo descansar; su yo de mañana lo agradecerá.")

    # ── NOTAS PENDIENTES (mañana 8–11h): recordatorio. Una vez al día. ────────────
    if 8 <= h < 11 and not _ya_hoy("notas"):
        _marcar("notas")
        n = _contar_notas()
        if n > 0:
            plural = "s" if n != 1 else ""
            hablar(f"Señor, le recuerdo que tiene {n} nota{plural} pendiente{plural}. ¿Se las leo?")

    # ── DISCO CASI LLENO (9–22h): avisa antes de quedarte sin espacio. 1 vez/día. ─
    if 9 <= h < 22 and not _ya_hoy("disco"):
        _marcar("disco")
        d = _disco_mas_lleno()
        if d:
            hablar(f"Señor, su disco {d[1]} está al {int(d[0])} por ciento. Le sugiero liberar espacio pronto.")

    # ── GPU CALIENTE (seguridad; con enfriamiento de 1h entre avisos). ────────────
    global _ultimo_aviso_gpu
    t = _gpu_temperatura()
    if t is not None and t >= GPU_TEMP_LIMITE and (time.time() - _ultimo_aviso_gpu) > GPU_COOLDOWN:
        _ultimo_aviso_gpu = time.time()
        hablar(f"Señor, la GPU está a {t} grados, bastante caliente. Revise la ventilación o cierre algo pesado.")

    # ── RAM CRÍTICA (9–22h, 1 vez/día cuando supera el límite). ───────────────────
    if 9 <= h < 22 and not _ya_hoy("ram"):
        try:
            pct = psutil.virtual_memory().percent
            if pct >= RAM_LIMITE:
                _marcar("ram")
                hablar(f"Señor, la memoria RAM está al {int(pct)} por ciento. Le sugiero cerrar algunas aplicaciones.")
        except Exception:
            pass

    # ── INTERNET CAÍDO (avisa solo en el cambio: cuando se cae y cuando vuelve). ──
    global _internet_caido
    if not _hay_internet():
        if not _internet_caido:
            _internet_caido = True
            hablar("Señor, parece que se cayó la conexión a internet. Algunas funciones no responderán hasta que vuelva.")
    else:
        if _internet_caido:
            _internet_caido = False
            hablar("Señor, la conexión a internet se restableció.")

    # ── MERCADO ABRE (días hábiles, 8–9h, 1 vez/día; solo si hay portafolio). ─────
    if PORTAFOLIO and datetime.now().weekday() < 5 and 8 <= h < 9 and not _ya_hoy("mercado"):
        _marcar("mercado")
        hablar("Señor, el mercado de Estados Unidos abre en breve. ¿Quiere que le revise sus acciones?")


def iniciar_anticipacion(hablar):
    # Arranca el bucle de anticipación en segundo plano.
    def _bucle():
        time.sleep(60)   # no apenas arranca; deja pasar el briefing inicial
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()
