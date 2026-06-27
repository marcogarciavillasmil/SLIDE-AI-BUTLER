# Vigilante de llamadas entrantes: AIDEN detecta cuando te llaman al PC, te AVISA por voz, y si
# no reaccionas en unos segundos ATIENDE la llamada solo (acepta -> dice un mensaje fijo -> cuelga),
# como una contestadora. Es un COMPORTAMIENTO de fondo (como Presencia/Anticipacion), no una tool.
#
# CÓMO detecta (descubierto probando en vivo): WhatsApp NO genera un toast de Windows para las
# llamadas; abre una VENTANA propia titulada "Voice call" / "Video call". Vigilamos las VENTANAS
# visibles. La app se identifica por el proceso dueño (WhatsApp.exe, Discord.exe, etc.).
#
# CÓMO atiende: con UI Automation (WhatsApp es WinUI/XAML, win32 puro no llega) pulsa "Accept" para
# aceptar y "End call" para colgar. El hablar el mensaje por el cable (VB-CABLE) lo orquesta
# contestar_llamada en Llamadas.py (que usa estas primitivas).
#
# Diseño ANTI-MOLESTIA: solo ventanas de LLAMADA (por título); dedup por hwnd; cooldown por app;
# si TÚ la tomas/rechazas en los segundos de gracia, AIDEN NO interviene; se PAUSA en modo gaming.

import threading
import time

import win32gui
import win32process

try:
    import psutil
except Exception:
    psutil = None

try:
    import uiautomation as auto
except Exception:
    auto = None

# Mensaje fijo que AIDEN le dice al contacto al auto-contestar (personalizable en secretos.py).
try:
    from secretos import MENSAJE_LLAMADA_AUSENTE as _MENSAJE_FIJO
except Exception:
    _MENSAJE_FIJO = ("Hola, soy el asistente de Marco. En este momento está ocupado y no puede "
                     "atender la llamada; le devolverá la llamada más tarde.")

# ── Parámetros ajustables ─────────────────────────────────────────────────────
INTERVALO = 2            # cada cuántos seg revisa las ventanas
COOLDOWN = 30           # seg para no repetir el aviso de la misma app
GRACIA = 10             # seg tras avisar antes de auto-contestar (si sigue sonando)

# Títulos que delatan una VENTANA de llamada entrante (minúsculas, sin tildes).
_TITULOS_LLAMADA = (
    "voice call", "video call", "incoming call", "incoming voice", "incoming video",
    "llamada de voz", "llamada de video", "videollamada", "llamada entrante",
    "te esta llamando",
)
# Nombres posibles de los botones según el idioma de la app.
_BOTONES_ACEPTAR = ("Accept", "Aceptar", "Answer", "Contestar", "Responder", "Atender")
_BOTONES_COLGAR = ("End call", "Hang up", "Hang Up", "Decline", "Colgar", "Finalizar",
                   "Finalizar llamada", "Terminar", "Leave call", "Rechazar")

_pausado = False
_primera_vez = {}        # hwnd -> timestamp en que se vio por primera vez (ya avisada)
_auto_hechas = set()     # hwnds que ya se intentaron auto-contestar
_ultimo_aviso = {}       # app -> timestamp del último aviso (cooldown)


def pausar_vigilante_llamadas(pausar=True):
    # Silencia el vigilante (lo usa el modo gaming).
    global _pausado
    _pausado = bool(pausar)


def _norm(t):
    t = (t or "").strip().lower()
    return t.translate(str.maketrans("áéíóúü", "aeiouu"))


def _app_de_ventana(hwnd):
    # Nombre bonito de la app dueña de la ventana, via su proceso.
    if psutil is None:
        return ""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid).name().lower()
    except Exception:
        return ""
    for clave, bonito in (("whatsapp", "WhatsApp"), ("discord", "Discord"),
                          ("teams", "Teams"), ("zoom", "Zoom"),
                          ("telegram", "Telegram"), ("skype", "Skype")):
        if clave in proc:
            return bonito
    return ""


def _ventanas_llamada():
    # {hwnd: app} de las ventanas visibles cuyo título parece una llamada entrante.
    res = {}

    def _cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            titulo = _norm(win32gui.GetWindowText(hwnd))
            if titulo and any(p in titulo for p in _TITULOS_LLAMADA):
                res[hwnd] = _app_de_ventana(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(_cb, None)
    return res


def _co_init():
    # COM para UI Automation en el hilo que llame (idempotente).
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass


def _pulsar_boton(ventana, nombres):
    # Busca un botón por cualquiera de esos nombres y lo activa (Invoke; si no, Click). True si pudo.
    for nombre in nombres:
        try:
            btn = ventana.ButtonControl(Name=nombre)
            if btn.Exists(maxSearchSeconds=0.4):
                try:
                    btn.GetInvokePattern().Invoke()   # más fiable que un clic físico
                except Exception:
                    btn.Click(simulateMove=False)
                return True
        except Exception:
            continue
    return False


def aceptar_ventana(hwnd):
    # Pulsa "Accept" en esa ventana de llamada. True solo si el botón existía (= seguía sonando).
    if auto is None:
        return False
    _co_init()
    try:
        ventana = auto.ControlFromHandle(hwnd)
        return bool(ventana) and _pulsar_boton(ventana, _BOTONES_ACEPTAR)
    except Exception:
        return False


def colgar_ventana(hwnd):
    # Pulsa "End call" en esa ventana de llamada. True si pudo colgar.
    if auto is None:
        return False
    _co_init()
    try:
        ventana = auto.ControlFromHandle(hwnd)
        return bool(ventana) and _pulsar_boton(ventana, _BOTONES_COLGAR)
    except Exception:
        return False


def hay_llamada_activa():
    # True si hay una ventana de llamada entrante visible ahora mismo.
    return bool(_ventanas_llamada())


def mensaje_de_orden(texto):
    # De una orden como "contesta y dile que estoy ocupado", saca el mensaje para el contacto.
    # Si no hay un mensaje explícito, devuelve "" (contestar_llamada usará el de por defecto).
    t = (texto or "").lower()
    for marca in ("dile que ", "dile ", "digale que ", "dígale que ", "di que ",
                  "diga que ", "diciendo ", "que le digas ", "responde que "):
        if marca in t:
            return texto[t.index(marca) + len(marca):].strip()
    return ""


def _frase_aviso(app):
    por_app = f" por {app}" if app else ""
    if auto is None:                       # sin UI Automation no puedo aceptar: solo aviso
        return f"Señor, tiene una llamada entrante{por_app}."
    return (f"Señor, tiene una llamada entrante{por_app}. "
            "Si no me dice nada, la contestaré en unos segundos.")


def _revisar(hablar):
    global _primera_vez, _auto_hechas
    if _pausado:
        return
    actuales = _ventanas_llamada()
    ahora = time.time()

    for hwnd, app in actuales.items():
        if hwnd not in _primera_vez:
            # Primera vez que veo esta llamada: AVISO (con cooldown por app).
            _primera_vez[hwnd] = ahora
            if ahora - _ultimo_aviso.get(app, 0) >= COOLDOWN:
                _ultimo_aviso[app] = ahora
                hablar(_frase_aviso(app))
                try:
                    from Nucleo_Slide.Estado_Del_Mundo import registrar_evento
                    registrar_evento(f"Llamada entrante{(' por ' + app) if app else ''}.", "llamadas")
                except Exception:
                    pass
            continue
        if hwnd in _auto_hechas or auto is None:
            continue
        # Ya avisada y pasó la gracia: auto-atender (acepta -> mensaje -> cuelga), en un hilo
        # para no bloquear la vigilancia. Si ya la tomaste tú, contestar_llamada no intervendrá.
        if ahora - _primera_vez[hwnd] >= GRACIA:
            _auto_hechas.add(hwnd)

            def _atender():
                try:
                    from Funciones_Slide.Comunicacion.Llamadas import contestar_llamada
                    contestar_llamada(_MENSAJE_FIJO)
                except Exception:
                    pass

            threading.Thread(target=_atender, daemon=True).start()

    # Olvida las ventanas que ya se cerraron (para que una próxima llamada vuelva a avisar).
    vivas = set(actuales)
    _primera_vez = {h: t for h, t in _primera_vez.items() if h in vivas}
    _auto_hechas = {h for h in _auto_hechas if h in vivas}


def iniciar_vigilante_llamadas(hablar):
    # Arranca el vigilante de llamadas en segundo plano.
    def _bucle():
        _co_init()                     # COM para UI Automation en este hilo
        time.sleep(20)                 # deja pasar el arranque/briefing
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()