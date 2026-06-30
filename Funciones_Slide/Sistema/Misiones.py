# MISIONES AUTÓNOMAS: el "Jarvis que HACE cosas y se asegura de que funcionen". A diferencia de
# crear_proyecto (que solo construye y avisa), una MISIÓN hace el ciclo completo de un agente:
#   1. CONSTRUYE delegando a Claude Code (headless, en sandbox).
#   2. VERIFICA que de verdad corre (lo ejecuta y mira si falla).
#   3. Si falla, se AUTO-CORRIGE una vez (le pasa el error a Claude Code) y re-verifica.
#   4. REPORTA por voz si quedó funcionando o no, y deja rastro en la conciencia compartida.
#
# Corre en SEGUNDO PLANO (es lento) y avisa al terminar. Reusa la invocación de Programador.py.

import os
import subprocess
import threading

from Funciones_Slide.Sistema.Programador import (
    _CLAUDE, _carpeta_proyecto, _resolver_carpeta, TIMEOUT_CLAUDE, TIMEOUT_EJECUCION,
)
from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
import sys


def _evento(texto):
    try:
        from Nucleo_Slide.Estado_Del_Mundo import registrar_evento
        registrar_evento(texto, "misiones")
    except Exception:
        pass


def _claude(carpeta, prompt):
    # Lanza Claude Code (headless, bypass) en la carpeta. Devuelve (ok, salida).
    try:
        r = subprocess.run(
            [_CLAUDE, "-p", prompt, "--permission-mode", "bypassPermissions"],
            cwd=carpeta, capture_output=True, text=True,
            timeout=TIMEOUT_CLAUDE, encoding="utf-8", errors="replace",
        )
        return True, (r.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return False, "se agotó el tiempo"
    except Exception as e:
        return False, str(e)


def _punto_de_entrada(carpeta):
    for cand in ("main.py", "app.py", "run.py", "__main__.py"):
        if os.path.exists(os.path.join(carpeta, cand)):
            return os.path.join(carpeta, cand)
    pys = [f for f in os.listdir(carpeta) if f.endswith(".py")] if os.path.isdir(carpeta) else []
    return os.path.join(carpeta, pys[0]) if pys else None


def _verificar(carpeta):
    # Corre el punto de entrada y devuelve (ok, salida_o_error). ok=True si returncode 0.
    objetivo = _punto_de_entrada(carpeta)
    if not objetivo:
        return False, "no encontré un archivo de Python para ejecutar"
    try:
        r = subprocess.run(
            [sys.executable, objetivo], cwd=carpeta, capture_output=True, text=True,
            timeout=TIMEOUT_EJECUCION, encoding="utf-8", errors="replace",
        )
        if r.returncode == 0:
            return True, (r.stdout or "").strip()
        return False, (r.stderr or r.stdout or "").strip()[-900:]
    except subprocess.TimeoutExpired:
        return False, "el programa tardó demasiado (¿bucle o espera de entrada?)"
    except Exception as e:
        return False, str(e)


def ejecutar_mision(objetivo, nombre=""):
    """MISIÓN autónoma: AIDEN construye lo pedido, VERIFICA que funciona, se autocorrige si falla y
    reporta. Para ÓRDENES GRANDES tipo 'hazme un programa que...'. Distinto de crear_proyecto en que
    aquí AIDEN se asegura de que de verdad CORRA."""
    objetivo = str(objetivo or "").strip()
    if not objetivo:
        return "¿Cuál es la misión, señor?"
    if not _CLAUDE or not os.path.exists(_CLAUDE):
        return "No encuentro Claude Code en el sistema, señor; no puedo emprender la misión."

    carpeta = _carpeta_proyecto(nombre or objetivo)
    nombre_c = os.path.basename(carpeta)

    def _trabajo():
        _evento(f"Misión '{nombre_c}': planificando y construyendo...")
        prompt_build = (
            "Eres el ejecutor de AIDEN. Construye en ESTA carpeta, COMPLETO y FUNCIONAL, lo siguiente. "
            "Deja un punto de entrada claro (main.py) que se pueda correr sin argumentos y SIN esperar "
            "input del usuario (para autoverificación). Al final resume en 2-3 líneas qué hiciste.\n\n"
            "MISIÓN: " + objetivo
        )
        ok_c, _ = _claude(carpeta, prompt_build)
        if not ok_c:
            hablado_del_asistente(f"Señor, no pude construir la misión '{nombre_c}'.")
            _evento(f"Misión '{nombre_c}': falló al construir.")
            return

        _evento(f"Misión '{nombre_c}': verificando que funcione...")
        ok, salida = _verificar(carpeta)

        if not ok:
            _evento(f"Misión '{nombre_c}': falló la verificación, corrigiendo...")
            prompt_fix = (
                "El programa que construiste en esta carpeta FALLÓ al ejecutarse. Corrige el error y "
                "asegúrate de que main.py corra sin fallos ni esperar input. Error:\n" + str(salida)
            )
            _claude(carpeta, prompt_fix)
            ok, salida = _verificar(carpeta)

        if ok:
            extracto = (salida or "")[-300:]
            hablado_del_asistente(
                f"Misión cumplida, señor: '{nombre_c}' quedó funcionando. {extracto}".strip()
            )
            _evento(f"Misión '{nombre_c}': CUMPLIDA y verificada.")
        else:
            hablado_del_asistente(
                f"Señor, construí '{nombre_c}' pero no logré que pasara la verificación; le dejé el "
                "código para que lo revisemos."
            )
            _evento(f"Misión '{nombre_c}': construida pero NO pasó la verificación.")

    threading.Thread(target=_trabajo, daemon=True).start()
    return (f"Misión aceptada, señor: '{nombre_c}'. La construyo, la pruebo y le reporto cuando esté "
            "lista.")
