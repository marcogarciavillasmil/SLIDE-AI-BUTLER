# Control VISIBLE de la pantalla: AIDEN se mete con la PC y lo VES.
#   - clic: encuentra un botón/elemento por su nombre (UI Automation) y MUEVE EL MOUSE hasta él
#           (despacio, para que se note) y hace clic.
#   - ordenar: acomoda tus ventanas en mosaico (las ves reorganizarse).
#   - enfocar: trae una app al frente.
# Una sola herramienta `interactuar_pc(accion, objetivo)` (estilo anti-bloat del proyecto).
#
# Fiable porque usa UI Automation (uiautomation, ya instalado) para localizar elementos; el mouse
# se mueve con pyautogui para que el movimiento sea VISIBLE.

import re

import win32gui

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except Exception:
    pyautogui = None

try:
    import uiautomation as auto
except Exception:
    auto = None

# Tipos de control que tiene sentido "clicar".
_CLICABLES = ("ButtonControl", "HyperlinkControl", "MenuItemControl", "ListItemControl",
              "TabItemControl", "CheckBoxControl", "RadioButtonControl", "SplitButtonControl",
              "TreeItemControl", "TextControl")


def _co_init():
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass


def _norm(t):
    return (t or "").strip().lower().translate(str.maketrans("áéíóúü", "aeiouu"))


def _clic_en(objetivo, tipo="clic"):
    if auto is None or pyautogui is None:
        return "No tengo el control de pantalla disponible, señor (falta uiautomation o pyautogui)."
    objetivo_n = _norm(objetivo)
    if not objetivo_n:
        return "¿En qué quiere que haga clic, señor?"
    _co_init()
    try:
        ventana = auto.GetForegroundControl()
        if not ventana:
            return "No veo una ventana activa donde hacer clic, señor."
        encontrado = None
        for ctrl, _depth in auto.WalkControl(ventana, maxDepth=22):
            try:
                if ctrl.ControlTypeName in _CLICABLES and objetivo_n in _norm(ctrl.Name):
                    encontrado = ctrl
                    break
            except Exception:
                continue
        if encontrado is None:
            return f"No encontré «{objetivo}» en la ventana activa, señor."
        r = encontrado.BoundingRectangle
        x = getattr(r, "xcenter", lambda: (r.left + r.right) // 2)()
        y = getattr(r, "ycenter", lambda: (r.top + r.bottom) // 2)()
        pyautogui.moveTo(x, y, duration=0.6)   # movimiento VISIBLE del cursor
        if tipo == "doble":
            pyautogui.doubleClick()
        elif tipo == "derecho":
            pyautogui.rightClick()
        else:
            pyautogui.click()
        verbo = {"doble": "doble clic", "derecho": "clic derecho"}.get(tipo, "clic")
        return f"Listo, señor. Hice {verbo} en «{encontrado.Name or objetivo}»."
    except Exception as e:
        return f"No pude hacer el clic, señor: {e}"


def _ventanas_ordenables():
    # Top-level visibles, con título, no minimizadas, que son ventanas de app (no herramientas).
    res = []

    def _cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return
            titulo = win32gui.GetWindowText(hwnd)
            if not titulo or not titulo.strip():
                return
            estilo = win32gui.GetWindowLong(hwnd, -20)   # GWL_EXSTYLE
            if estilo & 0x00000080:                      # WS_EX_TOOLWINDOW -> ignorar
                return
            res.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(_cb, None)
    return res[:4]   # ordenamos hasta 4 (mosaico cómodo)


def _ordenar_ventanas():
    try:
        import win32api
        ancho = win32api.GetSystemMetrics(0)
        alto = win32api.GetSystemMetrics(1) - 48          # deja la barra de tareas
    except Exception:
        ancho, alto = 1920, 1032
    vts = _ventanas_ordenables()
    if not vts:
        return "No hay ventanas que ordenar, señor."
    n = len(vts)
    # 1 -> full; 2 -> lado a lado; 3-4 -> cuadrícula 2x2.
    if n == 1:
        celdas = [(0, 0, ancho, alto)]
    elif n == 2:
        celdas = [(0, 0, ancho // 2, alto), (ancho // 2, 0, ancho // 2, alto)]
    else:
        cw, ch = ancho // 2, alto // 2
        celdas = [(0, 0, cw, ch), (cw, 0, cw, ch), (0, ch, cw, ch), (cw, ch, cw, ch)]
    for hwnd, (x, y, w, h) in zip(vts, celdas):
        try:
            win32gui.ShowWindow(hwnd, 9)                  # SW_RESTORE
            win32gui.MoveWindow(hwnd, x, y, w, h, True)   # se ve reacomodarse
        except Exception:
            pass
    return f"Listo, señor. Ordené {min(n, len(celdas))} ventanas en mosaico."


def _enfocar_app(objetivo):
    objetivo_n = _norm(objetivo)
    if not objetivo_n:
        return "¿Qué ventana quiere que traiga al frente, señor?"
    destino = []

    def _cb(hwnd, _):
        try:
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                if t and objetivo_n in _norm(t):
                    destino.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(_cb, None)
    if not destino:
        return f"No encontré una ventana de «{objetivo}», señor."
    try:
        hwnd = destino[0]
        win32gui.ShowWindow(hwnd, 9)            # SW_RESTORE
        win32gui.SetForegroundWindow(hwnd)
        return f"Al frente, señor: {win32gui.GetWindowText(hwnd)}."
    except Exception as e:
        return f"No pude traerla al frente, señor: {e}"


def _escribir(texto):
    if pyautogui is None:
        return "No tengo control de teclado, señor."
    texto = str(texto or "")
    if not texto:
        return "¿Qué quiere que escriba, señor?"
    try:
        pyautogui.typewrite(texto, interval=0.02)   # escritura VISIBLE donde esté el cursor
        return f"Escrito, señor: {texto[:60]}"
    except Exception as e:
        return f"No pude escribir, señor: {e}"


def _scroll(objetivo):
    if pyautogui is None:
        return "No tengo control de scroll, señor."
    o = _norm(objetivo)
    cantidad = -600 if ("abajo" in o or "baja" in o or "down" in o) else 600
    try:
        pyautogui.scroll(cantidad)
        return "Listo, señor."
    except Exception as e:
        return f"No pude hacer scroll, señor: {e}"


def _cerrar_pestana():
    if pyautogui is None:
        return "No tengo control de teclado, señor."
    try:
        pyautogui.hotkey("ctrl", "w")
        return "Cerré la pestaña, señor."
    except Exception as e:
        return f"No pude cerrar la pestaña, señor: {e}"


def _seleccionar_todo():
    if pyautogui is None:
        return "No tengo control de teclado, señor."
    try:
        pyautogui.hotkey("ctrl", "a")
        return "Seleccioné todo, señor."
    except Exception as e:
        return f"No pude seleccionar, señor: {e}"


def _atajo(combo):
    if pyautogui is None:
        return "No tengo control de teclado, señor."
    teclas = [t.strip().lower() for t in re.split(r"[+\s]+", str(combo or "")) if t.strip()]
    if not teclas:
        return "¿Qué combinación de teclas, señor? (ej. control + s)"
    # normaliza nombres comunes en español
    mapa = {"ctrl": "ctrl", "control": "ctrl", "mayus": "shift", "mayús": "shift", "shift": "shift",
            "alt": "alt", "win": "win", "windows": "win", "tab": "tab", "esc": "esc", "enter": "enter",
            "intro": "enter", "supr": "delete", "borrar": "backspace", "espacio": "space"}
    teclas = [mapa.get(t, t) for t in teclas]
    try:
        pyautogui.hotkey(*teclas)
        return f"Listo, señor. Pulsé {' + '.join(teclas)}."
    except Exception as e:
        return f"No pude ejecutar el atajo, señor: {e}"


def controlar_pantalla(accion, objetivo=""):
    """Control VISIBLE de la PC (mouse/teclado sobre lo que hay en pantalla). accion:
    'clic' / 'doble_clic' / 'clic_derecho' (sobre un botón/elemento por su nombre),
    'ordenar' (mosaico de ventanas), 'enfocar' (trae una app al frente), 'escribir' (teclea texto),
    'scroll' (arriba/abajo), 'cerrar_pestana' (Ctrl+W), 'seleccionar' (Ctrl+A), 'atajo' (combo de teclas)."""
    a = _norm(accion)
    if "doble" in a:
        return _clic_en(objetivo, "doble")
    if "derech" in a or "secundario" in a or "right" in a:
        return _clic_en(objetivo, "derecho")
    if "clic" in a or "click" in a or "presion" in a or "pulsa el boton" in a:
        return _clic_en(objetivo, "clic")
    if "orden" in a or "mosaico" in a or "acomod" in a or "organiz" in a:
        return _ordenar_ventanas()
    if "enfoc" in a or "frente" in a or "cambia a" in a:
        return _enfocar_app(objetivo)
    if "escrib" in a or "teclea" in a or "redacta" in a:
        return _escribir(objetivo)
    if "scroll" in a or "desplaz" in a or "baja" in a or "sube" in a:
        return _scroll(objetivo)
    if "pestan" in a:
        return _cerrar_pestana()
    if "seleccion" in a:
        return _seleccionar_todo()
    if "atajo" in a or "combinacion" in a or "teclas" in a or "presiona" in a:
        return _atajo(objetivo)
    return ("No reconozco esa acción, señor (clic, doble_clic, clic_derecho, ordenar, enfocar, "
            "escribir, scroll, cerrar_pestana, seleccionar, atajo).")
