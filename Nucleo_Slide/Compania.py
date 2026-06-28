# COMPAÑÍA: la re-entrada RELACIONAL de AIDEN. Un compañero no te saluda en frío — RETOMA el hilo de
# lo que estaban haciendo. Aquí viven los momentos en que AIDEN "vuelve a ti":
#   - saludo_de_reanudacion(): al arrancar, un saludo cálido que continúa vuestra historia
#     (última conversación + metas activas + cuánto tiempo pasó). [Idea #2]
#
# Imports PEREZOSOS del LLM/estado para no crear ciclos. Fallbacks robustos: si algo falla, saluda
# normal — JAMÁS rompe el arranque de AIDEN.

import time

from Nucleo_Slide.Memoria_Episodica import _cargar as _cargar_episodios

_FALLBACK = "Bienvenido de vuelta, señor. ¿En qué andamos hoy?"


def _gap_humano(ts):
    # Traduce el tiempo desde la última interacción a algo natural.
    if not ts:
        return ""
    seg = time.time() - ts
    if seg < 2 * 3600:
        return "hace un rato"
    if seg < 8 * 3600:
        return "hace unas horas"
    if seg < 40 * 3600:
        return "desde ayer"
    return f"hace {int(seg // 86400)} días"


def saludo_de_reanudacion():
    """Un saludo de bienvenida que RETOMA el hilo (última charla + metas + tiempo). Nunca crashea."""
    try:
        eps = _cargar_episodios() or []
        from Nucleo_Slide.Estado_Del_Mundo import metas_activas, obtener
        metas = [m.get("texto", "") for m in metas_activas()][:2]
        ult = (obtener() or {}).get("ultima_interaccion", 0)

        if not eps and not metas:
            return _FALLBACK   # primera vez / sin historia: saludo simple

        ultimos = eps[-2:]
        contexto = "\n".join(
            f'Marco: "{e.get("usuario","")[:100]}" -> tú: "{e.get("aiden","")[:80]}"'
            for e in ultimos
        )
        gap = _gap_humano(ult)

        from Nucleo_Slide.Cerebro import client, MODELO
        prompt = (
            "Eres AIDEN saludando a Marco (trátalo de 'señor') cuando vuelve, como un compañero "
            "cercano que RETOMA EL HILO, no como un saludo en frío.\n"
            + (f"Última vez que hablaron: {gap}.\n" if gap else "")
            + (f"Lo último que hicieron:\n{contexto}\n" if contexto else "")
            + (f"Metas activas de Marco: {'; '.join(metas)}.\n" if metas else "")
            + "Dale UN saludo cálido y BREVE (1-2 frases) que retome lo de antes con naturalidad e "
            "invite a seguir. Como un amigo que continúa la conversación; NO listes datos, NO suenes "
            "a robot, NO seas meloso de más."
        )
        r = client.chat.completions.create(
            model=MODELO, messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=120,
        )
        t = (r.choices[0].message.content or "").strip()
        return t or _FALLBACK
    except Exception:
        return _FALLBACK
