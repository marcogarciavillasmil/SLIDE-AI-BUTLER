# SINTONÍA EMOCIONAL: lee el ESTADO de Marco (de señales que YA tenemos) y produce una guía corta de
# TONO para el cerebro. NO es una herramienta y NO cambia QUÉ hace AIDEN — cambia CÓMO te habla, para
# que se sienta un compañero que te entiende. Heurística barata (sin LLM); corre en cada turno.
#
# Filosofía: la continuidad COGNITIVA (memoria) hizo que AIDEN supiera qué pasa; la SINTONÍA es su
# gemelo EMOCIONAL: que responda distinto según cómo estás. Se inyecta en el prompt como una guía de
# tono, así la MISMA mente responde con calidez/brevedad/energía según el momento.

import datetime

_TILDES = str.maketrans("áéíóúü", "aeiouu")


def _norm(t):
    return str(t or "").translate(_TILDES).lower()


# Léxicos (sin tildes, como compara _norm). Señales fuertes y poco ambiguas.
_FRUSTRACION = (
    "no funciona", "no sirve", "no entiendo", "no me sale", "no puedo", "no jala",
    "odio", "harto", "cansado", "cansada", "estresad", "frustrad", "agobiad",
    "mierda", "carajo", "rabia", "fastidio", "putas", "no doy mas", "estoy mal",
)
_LOGRO = (
    "lo logre", "por fin", "funciono", "termine", "lo hice", "consegui", "aprobe",
    "gane ", "exito", "genial", "increible", "buenisimo", "lo cumpli", "lo termine",
    "que alegria", "estoy feliz", "vamos!", "eso!",
)


def lectura_de_estado(consulta=""):
    """Devuelve una guía de TONO para inyectar en el prompt, o "" si no hay señal clara."""
    c = _norm(consulta)
    h = datetime.datetime.now().hour
    candidatas = []   # (prioridad, guia)

    # 1) Las PALABRAS de Marco ahora (la señal más real y prioritaria).
    if any(p in c for p in _FRUSTRACION):
        candidatas.append((0, "Marco suena frustrado o agobiado. Sé cálido, paciente y MUY directo; "
                              "nada de bromas ni rodeos; ayúdalo a destrabarse y baja la tensión."))
    elif any(p in c for p in _LOGRO):
        candidatas.append((0, "Marco acaba de lograr algo. Celébralo con energía y orgullo genuino, "
                              "breve; comparte su alegría antes de seguir."))

    # 2) Situación (estado del mundo).
    try:
        from Nucleo_Slide.Estado_Del_Mundo import obtener
        est = obtener()
        if est.get("en_reunion"):
            candidatas.append((1, "Marco está en una reunión. Respuestas mínimas, discretas y serias."))
        elif est.get("modo") == "gaming":
            candidatas.append((1, "Marco está jugando. Tono relajado e informal, muy breve, no lo distraigas."))
        evs = est.get("eventos", []) or []
        if any(("cumplida" in _norm(e.get("texto", "")) or "felicidades" in _norm(e.get("texto", "")))
               for e in evs[-4:]):
            candidatas.append((2, "Marco viene de cumplir una meta: reconócelo, está en racha."))
    except Exception:
        pass

    # 3) La hora.
    if 0 <= h < 5:
        candidatas.append((3, "Es de madrugada: Marco quizá esté cansado o trasnochando. Sé suave y "
                              "breve; si encaja, sugiérele descansar sin insistir."))

    if not candidatas:
        return ""
    candidatas.sort(key=lambda x: x[0])   # gana la señal más fuerte (emocional > situacional > hora)
    return "CÓMO TRATAR A MARCO AHORA (ajusta tu TONO, no lo que haces): " + candidatas[0][1]
