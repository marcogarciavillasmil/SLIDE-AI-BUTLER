# Modo reunión automático: AIDEN detecta que estás en una LLAMADA/REUNIÓN y silencia las
# distracciones solo (pausa música, silencia notificaciones de Windows, calla sus avisos
# proactivos para no hablar encima de ti). Al terminar, restaura. Comportamiento de fondo.
#
# CÓMO detecta (señal fiable y agnóstica de app): mira en el registro de Windows qué apps están
# USANDO EL MICRÓFONO ahora mismo (CapabilityAccessManager). Funciona con Zoom, Teams, Meet
# (navegador), Discord, etc. Excluye a AIDEN/python (su wake-word tiene el mic siempre abierto).
#
# Diseño ANTI-MOLESTIA:
#   1. Actúa SILENCIOSO (no habla durante la reunión); un solo aviso corto al entrar/salir.
#   2. Restaura TODO al terminar.
#   3. Se PAUSA en modo gaming.

import threading
import time
import winreg

# ── Parámetros ajustables ─────────────────────────────────────────────────────
INTERVALO = 5     # cada cuántos seg revisa el micrófono

_MIC_BASE = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone"

_pausado = False
_en_reunion = False


def pausar_vigilante_reunion(pausar=True):
    # Silencia el vigilante (lo usa el modo gaming).
    global _pausado
    _pausado = bool(pausar)


def _scan_clave(path, apps):
    # Recorre las apps bajo 'path' y añade a 'apps' las que tienen el mic EN USO (Stop==0).
    try:
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
    except Exception:
        return
    try:
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(clave, i)
                i += 1
            except OSError:
                break
            if sub == "NonPackaged":
                continue
            try:
                sk = winreg.OpenKey(clave, sub)
                stop, _ = winreg.QueryValueEx(sk, "LastUsedTimeStop")
                winreg.CloseKey(sk)
                if stop == 0:                 # 0 = el mic está EN USO ahora mismo
                    apps.add(sub.lower())
            except Exception:
                pass
    finally:
        winreg.CloseKey(clave)


def _otra_app_usa_mic():
    # True si ALGUNA app (que no sea AIDEN/python) está usando el micrófono ahora.
    apps = set()
    _scan_clave(_MIC_BASE, apps)
    _scan_clave(_MIC_BASE + r"\NonPackaged", apps)
    return any(("python" not in a and "aiden" not in a) for a in apps)


def _entrar_reunion(hablar):
    # Silencia distracciones (todo con import perezoso para evitar ciclos de import).
    try:
        from Funciones_Slide.Sistema.Funciones_Sistema import control_musica
        control_musica("pausa")                       # pausa la música/medios
    except Exception:
        pass
    for ruta, fn in (
        ("Funciones_Slide.Sistema.Modos", "_notificaciones_windows"),
    ):
        try:
            mod = __import__(ruta, fromlist=[fn])
            getattr(mod, fn)(False)                    # apaga notificaciones de Windows
        except Exception:
            pass
    _pausar_avisos(True)
    try:
        hablar("Detecté una reunión, señor. Activo modo silencioso.")
    except Exception:
        pass
    try:
        from Nucleo_Slide.Estado_Del_Mundo import actualizar, registrar_evento
        actualizar(en_reunion=True)
        registrar_evento("Marco entró a una reunión; silencié las distracciones.", "reunion")
    except Exception:
        pass


def _salir_reunion(hablar):
    for ruta, fn in (("Funciones_Slide.Sistema.Modos", "_notificaciones_windows"),):
        try:
            mod = __import__(ruta, fromlist=[fn])
            getattr(mod, fn)(True)                     # reactiva notificaciones
        except Exception:
            pass
    _pausar_avisos(False)
    try:
        from Funciones_Slide.Sistema.Funciones_Sistema import control_musica
        control_musica("play")                         # reanuda la música
    except Exception:
        pass
    try:
        hablar("Terminó la reunión, señor. Restauré todo.")
    except Exception:
        pass
    try:
        from Nucleo_Slide.Estado_Del_Mundo import actualizar, registrar_evento
        actualizar(en_reunion=False)
        registrar_evento("Terminó la reunión; restauré todo.", "reunion")
    except Exception:
        pass


def _pausar_avisos(pausar):
    # Pausa/reanuda los demás comportamientos proactivos para no hablar durante la reunión.
    for ruta, fn in (
        ("Funciones_Slide.Productividad.Anticipacion", "pausar_anticipacion"),
        ("Funciones_Slide.Sistema.Presencia", "pausar_presencia"),
        ("Funciones_Slide.Productividad.Alertas_Mercado", "pausar_alertas"),
        ("Funciones_Slide.Comunicacion.Vigilante_Llamadas", "pausar_vigilante_llamadas"),
        ("Funciones_Slide.Sistema.Vigilante_Pantalla", "pausar_vigilante_pantalla"),
        ("Funciones_Slide.Sistema.Vigilante_Portapapeles", "pausar_vigilante_portapapeles"),
    ):
        try:
            mod = __import__(ruta, fromlist=[fn])
            getattr(mod, fn)(pausar)
        except Exception:
            pass


def _revisar(hablar):
    global _en_reunion
    if _pausado:
        return
    ahora_en_reunion = _otra_app_usa_mic()
    if ahora_en_reunion and not _en_reunion:
        _en_reunion = True
        _entrar_reunion(hablar)
    elif not ahora_en_reunion and _en_reunion:
        _en_reunion = False
        _salir_reunion(hablar)


def iniciar_vigilante_reunion(hablar):
    # Arranca el detector de reuniones en segundo plano.
    def _bucle():
        time.sleep(30)                 # deja pasar el arranque/briefing
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()
