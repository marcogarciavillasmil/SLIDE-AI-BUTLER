import time
import threading
from datetime import date

import yfinance as yf
from Funciones_Slide.Info.Finanzas import _WATCHLIST

try:
    from secretos import PORTAFOLIO
except ImportError:
    PORTAFOLIO = {}

# --- Configuracion (cambia estos numeros si quieres) ---
INTERVALO_MIN = 30      # cada cuantos minutos revisa el mercado
UMBRAL_PCT    = 4.0     # movimiento diario (en %) que dispara un aviso

# --- Estado interno (anti-repeticion) ---
_objetivos     = {}     # symbol -> precio objetivo de analistas (se cachea una vez)
_alertado_mov  = {}     # symbol -> fecha en que ya avisamos su movimiento de hoy
_alertado_obj  = set()  # symbols que ya avisamos que llegaron a su objetivo
_pausado       = False  # el modo gaming pausa los avisos para no interrumpir


def pausar_alertas(estado):
    global _pausado
    _pausado = bool(estado)


def _simbolos():
    return sorted(set(list(PORTAFOLIO.keys()) + list(_WATCHLIST)))


def _cargar_objetivos(simbolos):
    for s in simbolos:
        try:
            apt = yf.Ticker(s).analyst_price_targets
            if apt and apt.get("mean"):
                _objetivos[s] = apt["mean"]
        except Exception:
            pass


def _cambio_pct(simbolo):
    # (precio_actual, cambio_pct_hoy) con datos rapidos. None si no hay datos.
    try:
        fi = yf.Ticker(simbolo).fast_info
        precio = fi.get("lastPrice")
        prev = fi.get("previousClose")
        if precio is None or not prev:
            return None, None
        return precio, (precio - prev) / prev * 100.0
    except Exception:
        return None, None


def _revisar(hablar, primera):
    hoy = date.today()
    for s in _simbolos():
        precio, pct = _cambio_pct(s)
        if precio is None:
            continue

        # 1) Movimiento fuerte del dia
        if pct is not None and abs(pct) >= UMBRAL_PCT and _alertado_mov.get(s) != hoy:
            _alertado_mov[s] = hoy          # marca: no repetir hoy
            if not primera:                  # en el baseline solo registramos, no hablamos
                verbo = "subió" if pct >= 0 else "bajó"
                hablar(f"Señor, {s} {verbo} {abs(pct):.1f}% hoy.")

        # 2) Llego al precio objetivo de los analistas
        obj = _objetivos.get(s)
        if obj and precio >= obj and s not in _alertado_obj:
            _alertado_obj.add(s)
            if not primera:
                hablar(f"Señor, {s} alcanzó su precio objetivo de {obj:.0f} dólares, ahora está en {precio:.2f}.")


def _bucle(hablar):
    _cargar_objetivos(_simbolos())
    _revisar(hablar, primera=True)          # baseline: estado actual sin avisar
    while True:
        time.sleep(INTERVALO_MIN * 60)
        if _pausado:          # modo gaming: no interrumpir
            continue
        try:
            _revisar(hablar, primera=False)
        except Exception:
            pass


def iniciar_alertas(hablar):
    if not _simbolos():
        return
    threading.Thread(target=_bucle, args=(hablar,), daemon=True).start()
