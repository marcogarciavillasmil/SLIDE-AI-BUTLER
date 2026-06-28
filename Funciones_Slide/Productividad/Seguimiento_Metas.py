# SEGUIMIENTO ACTIVO DE METAS (el "te acompaña" de Jarvis): AIDEN no solo recuerda tus metas, las
# PERSIGUE. Una vez al día (máx), si no estás ocupado, te busca para UNA meta: revisa el avance,
# sugiere el siguiente paso o te da un empujón. Comportamiento de fondo (como Presencia).
#
# Diseño ANTI-MOLESTIA (clave): MÁXIMO 1 seguimiento por día en total; cada meta como mucho 1 vez
# cada ~22h; solo en franja 10-21h; se calla si estás en reunión, gaming o ausente. El mensaje lo
# redacta el LLM con la meta + sus avances + tu perfil, para que sea útil y natural, no robótico.

import threading
import time
from datetime import datetime

INTERVALO = 30 * 60          # cada cuánto revisa si toca un seguimiento
MIN_HORAS_META = 22          # no seguir la misma meta más de ~1 vez/día
HORA_INICIO, HORA_FIN = 10, 21

_pausado = False
_ultimo_dia = ""             # fecha del último seguimiento (tope: 1 por día en total)


def pausar_seguimiento_metas(pausar=True):
    global _pausado
    _pausado = bool(pausar)


def _generar_seguimiento(meta):
    # Redacta UN mensaje corto, cálido y útil sobre la meta (check-in / siguiente paso / empujón).
    try:
        from Nucleo_Slide.Cerebro import client, MODELO
        from Nucleo_Slide.Perfil_Marco import perfil_texto
        avances = meta.get("avances", []) or []
        avtxt = "; ".join(a.get("nota", "") for a in avances[-3:] if a.get("nota")) or \
            "aún no hay avances registrados"
        perfil = (perfil_texto() or "")[:300]
        prompt = (
            "Eres AIDEN, acompañando a Marco (trátalo de 'señor') en sus metas como un Jarvis "
            "cercano. Su META: \"" + meta.get("texto", "") + "\". Avances recientes: " + avtxt + ". "
            + ("Perfil de Marco: " + perfil + ". " if perfil else "")
            + "Dale UN mensaje corto (una sola frase), cálido y ÚTIL: o un check-in concreto, o una "
            "sugerencia del SIGUIENTE PASO accionable, o un empujón motivador. Natural, sin sonar a "
            "robot, sin repetir lo obvio."
        )
        r = client.chat.completions.create(
            model=MODELO, messages=[{"role": "user", "content": prompt}],
            temperature=0.6, max_tokens=120,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception:
        return ""


def _revisar(hablar):
    global _ultimo_dia
    if _pausado:
        return
    if not (HORA_INICIO <= datetime.now().hour < HORA_FIN):
        return
    hoy = datetime.now().strftime("%Y-%m-%d")
    if _ultimo_dia == hoy:                       # ya hubo un seguimiento hoy
        return
    try:
        from Nucleo_Slide.Estado_Del_Mundo import (
            obtener, meta_para_seguimiento, marcar_seguimiento, registrar_evento,
        )
    except Exception:
        return
    est = obtener()
    if est.get("en_reunion") or est.get("modo") == "gaming" or not est.get("marco_presente", True):
        return                                   # no molestar
    meta = meta_para_seguimiento(MIN_HORAS_META)
    if not meta:
        return
    frase = _generar_seguimiento(meta)
    if not frase:
        return
    _ultimo_dia = hoy
    marcar_seguimiento(meta.get("texto", ""))
    hablar(frase)
    try:
        registrar_evento(f"Seguimiento de meta «{meta.get('texto','')}»: {frase}", "metas")
    except Exception:
        pass


def iniciar_seguimiento_metas(hablar):
    # Arranca el acompañamiento de metas en segundo plano.
    def _bucle():
        time.sleep(300)                          # deja pasar el arranque/briefing
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()
