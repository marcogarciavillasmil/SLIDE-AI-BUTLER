# NÚCLEO DE CONCIENCIA COMPARTIDA (estado del mundo).
#
# El salto hacia "Jarvis": una SOLA mente que TODAS las partes de AIDEN (cerebro de voz, cerebro
# remoto, conciencia ambiental, vigilantes, presencia) LEEN y ESCRIBEN. Convierte a AIDEN de varios
# scripts reactivos sueltos en un agente con CONTINUIDAD: sabe qué pasa AHORA, qué pasó hace un rato,
# en qué anda Marco, su estado, y qué METAS persigue. Es la base de la proactividad con propósito.
#
# Es un módulo HOJA: solo usa la stdlib, así CUALQUIER parte lo importa sin riesgo de import circular.
# Persiste en estado_del_mundo.json (GITIGNORED, privado). Thread-safe (RLock).

import json
import os
import threading
import time
from datetime import datetime

_RUTA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "estado_del_mundo.json"
)
_lock = threading.RLock()
MAX_EVENTOS = 40          # cuántos eventos recientes se conservan en el hilo de conciencia

_estado = {
    "foco_actual": "",        # app/ventana donde está Marco
    "marco_presente": True,   # ¿está frente al PC?
    "en_reunion": False,
    "modo": "normal",         # normal | gaming | manos_libres | ...
    "ultima_interaccion": 0,  # timestamp del último intercambio (voz/texto)
    "eventos": [],            # hilo de conciencia: [{t, hora, texto, origen}]
    "metas": [],              # objetivos que AIDEN persigue (Parte 2): [{texto, creada, estado}]
}


def _cargar():
    global _estado
    try:
        if os.path.exists(_RUTA):
            with open(_RUTA, encoding="utf-8") as f:
                guardado = json.load(f)
            if isinstance(guardado, dict):
                _estado.update(guardado)
    except Exception:
        pass


def _guardar():
    try:
        with open(_RUTA, "w", encoding="utf-8") as f:
            json.dump(_estado, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


_cargar()


# ── Escritura (cualquier parte de AIDEN) ──────────────────────────────────────
def actualizar(**campos):
    # Actualiza campos del estado: actualizar(foco_actual="Word", en_reunion=True, ...)
    with _lock:
        _estado.update(campos)
        _guardar()


def registrar_evento(texto, origen="sistema"):
    # Añade al HILO de conciencia lo que acaba de pasar (lo ve toda la mente).
    texto = str(texto or "").strip()
    if not texto:
        return
    with _lock:
        ev = _estado.get("eventos", [])
        if ev and ev[-1].get("texto") == texto:   # dedup consecutivo
            return
        ev.append({
            "t": time.time(), "hora": datetime.now().strftime("%H:%M"),
            "texto": texto[:200], "origen": origen,
        })
        _estado["eventos"] = ev[-MAX_EVENTOS:]
        _guardar()


def marcar_interaccion():
    with _lock:
        _estado["ultima_interaccion"] = time.time()
        _guardar()


# ── Metas (base de la Parte 2: perseguir objetivos en el tiempo) ──────────────
def agregar_meta(texto):
    with _lock:
        _estado.setdefault("metas", []).append(
            {"texto": str(texto or "")[:200], "creada": time.time(), "estado": "abierta"}
        )
        _guardar()


def cerrar_meta(subcadena):
    sub = str(subcadena or "").lower()
    with _lock:
        for m in _estado.get("metas", []):
            if sub and sub in m.get("texto", "").lower():
                m["estado"] = "hecha"
        _guardar()


def metas_activas():
    with _lock:
        return [m for m in _estado.get("metas", []) if m.get("estado") != "hecha"]


def anotar_avance(subcadena, nota=""):
    # Registra un avance en la meta que coincida. Devuelve el texto de la meta o "".
    sub = str(subcadena or "").lower()
    with _lock:
        for m in _estado.get("metas", []):
            if m.get("estado") != "hecha" and sub and sub in m.get("texto", "").lower():
                m.setdefault("avances", []).append({"t": time.time(), "nota": str(nota or "")[:200]})
                m["avances"] = m["avances"][-10:]
                m["ultimo_seguimiento"] = time.time()
                _guardar()
                return m.get("texto", "")
        return ""


def meta_para_seguimiento(min_horas=22):
    # La meta activa MÁS olvidada (cuyo último seguimiento supere min_horas). None si ninguna toca.
    ahora = time.time()
    with _lock:
        cands = [m for m in _estado.get("metas", [])
                 if m.get("estado") != "hecha"
                 and ahora - m.get("ultimo_seguimiento", m.get("creada", 0)) >= min_horas * 3600]
        if not cands:
            return None
        cands.sort(key=lambda m: m.get("ultimo_seguimiento", m.get("creada", 0)))
        return json.loads(json.dumps(cands[0]))


def marcar_seguimiento(subcadena):
    sub = str(subcadena or "").lower()
    with _lock:
        for m in _estado.get("metas", []):
            if sub and sub in m.get("texto", "").lower():
                m["ultimo_seguimiento"] = time.time()
        _guardar()


# ── Lectura ───────────────────────────────────────────────────────────────────
def obtener():
    with _lock:
        return json.loads(json.dumps(_estado))   # copia profunda barata


def resumen_texto(n_eventos=8):
    # Texto compacto del estado + últimos eventos, para inyectar en prompts (toda la mente lo ve).
    with _lock:
        lineas = []
        if _estado.get("foco_actual"):
            lineas.append(f"Foco actual de Marco: {_estado['foco_actual']}")
        est = []
        if not _estado.get("marco_presente", True):
            est.append("ausente del PC")
        if _estado.get("en_reunion"):
            est.append("en una reunión")
        if _estado.get("modo") and _estado["modo"] != "normal":
            est.append(f"modo {_estado['modo']}")
        if est:
            lineas.append("Estado: " + ", ".join(est))
        metas = [m for m in _estado.get("metas", []) if m.get("estado") != "hecha"]
        if metas:
            lineas.append("Metas activas: " + " | ".join(m.get("texto", "") for m in metas[:5]))
        evs = _estado.get("eventos", [])[-n_eventos:]
        if evs:
            lineas.append("Lo que ha pasado recientemente:")
            for e in evs:
                lineas.append(f"  [{e.get('hora', '')}] {e.get('texto', '')}")
        return "\n".join(lineas).strip()
