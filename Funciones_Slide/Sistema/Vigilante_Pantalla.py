# Centinela de pantalla: AIDEN MONITOREA tus ventanas y SALTA SOLO cuando algo se rompe —
# una app se CONGELA ("No responde") o aparece un ERROR/crash. Te avisa y ofrece ayuda, el
# clásico momento Jarvis de "Señor, detecto un problema". Comportamiento de fondo (como Presencia),
# NO una tool. Cero costo de API: detecta por el TÍTULO/clase de las ventanas (win32gui).
#
# Diseño ANTI-MOLESTIA:
#   1. Solo dispara con eventos REALES (congelada / error), no con uso normal.
#   2. Dedup por ventana + cooldown (no repite el mismo aviso).
#   3. Se PAUSA en modo gaming.
#   4. Solo avisa y OFRECE; no cierra nada por su cuenta (tú decides: "cierra X").
#
# Opcional (LEER_PANTALLA=True): al detectar un error, usa la VISIÓN (analizar_pantalla) para
# decirte QUÉ error es. Apagado por defecto (cuesta una llamada de visión).

import threading
import time

import win32gui

# ── Parámetros ajustables ─────────────────────────────────────────────────────
INTERVALO = 5          # cada cuántos seg revisa las ventanas
COOLDOWN = 120         # seg para no repetir el aviso de la misma ventana
LEER_PANTALLA = False  # si True, al detectar un error mira la pantalla (visión) para decir qué es

# Una ventana CONGELADA: Windows le añade este sufijo al título.
_CONGELADA = ("(no responde)", "(not responding)")
# Pistas de que una ventana es un ERROR/crash (en el título, minúsculas sin tildes).
_ERROR = (
    "ha dejado de funcionar", "stopped working", "application error", "se ha producido un error",
    "runtime error", "unhandled exception", "fatal error", "ha fallado", "error de aplicacion",
    "crash", "se cerro inesperadamente", "dejo de funcionar",
)

_pausado = False
_avisadas = {}         # (tipo, hwnd) -> timestamp del último aviso (cooldown/dedup)


def pausar_vigilante_pantalla(pausar=True):
    # Silencia el centinela (lo usa el modo gaming).
    global _pausado
    _pausado = bool(pausar)


def _norm(t):
    t = (t or "").strip().lower()
    return t.translate(str.maketrans("áéíóúü", "aeiouu"))


def _evento_mundo(texto):
    # Registra en la conciencia compartida (para que toda la mente de AIDEN se entere).
    try:
        from Nucleo_Slide.Estado_Del_Mundo import registrar_evento
        registrar_evento(texto, "pantalla")
    except Exception:
        pass


def _eventos_pantalla():
    # Devuelve [((tipo, hwnd), titulo_app, frase), ...] de ventanas con problema visibles.
    eventos = []

    def _cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            titulo = win32gui.GetWindowText(hwnd)
            if not titulo or not titulo.strip():
                return
            tl = _norm(titulo)
            if any(f in tl for f in _CONGELADA):
                # Quita el sufijo "(No responde)" para nombrar la app.
                app = titulo
                for marca in ("(No responde)", "(Not Responding)", "(no responde)"):
                    app = app.replace(marca, "")
                app = app.strip(" -") or "una aplicación"
                eventos.append((("congelada", hwnd), app,
                                f"Señor, parece que «{app}» se congeló. ¿Quiere que la cierre?"))
            elif any(k in tl for k in _ERROR):
                try:
                    clase = win32gui.GetClassName(hwnd)
                except Exception:
                    clase = ""
                # Diálogos estándar de Windows son "#32770"; igual aceptamos otros si el título grita error.
                eventos.append((("error", hwnd), titulo,
                                f"Señor, detecto un error en pantalla: «{titulo}». ¿Quiere que lo revise?"))
        except Exception:
            pass

    win32gui.EnumWindows(_cb, None)
    return eventos


def _revisar(hablar):
    if _pausado:
        return
    ahora = time.time()
    vistos = set()
    for clave, _app, frase in _eventos_pantalla():
        vistos.add(clave)
        if ahora - _avisadas.get(clave, 0) < COOLDOWN:
            continue
        _avisadas[clave] = ahora
        # Si es un error y está activado, mira la pantalla para decir QUÉ es (visión).
        if clave[0] == "error" and LEER_PANTALLA:
            try:
                from Funciones_Slide.Info.Vision import analizar_pantalla
                detalle = str(analizar_pantalla("Resume en una frase el error que se ve en pantalla."))
                hablar(f"Señor, detecto un error en pantalla. {detalle}")
                _evento_mundo(frase)
                continue
            except Exception:
                pass
        hablar(frase)
        _evento_mundo(frase)
    # Olvida las ventanas que ya se cerraron (para que un próximo problema vuelva a avisar).
    for clave in [c for c in _avisadas if c not in vistos]:
        del _avisadas[clave]


def iniciar_vigilante_pantalla(hablar):
    # Arranca el centinela de pantalla en segundo plano.
    def _bucle():
        time.sleep(25)                 # deja pasar el arranque/briefing
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()
