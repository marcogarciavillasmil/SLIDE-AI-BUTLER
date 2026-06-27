# Metas (Parte 2 del núcleo Jarvis): objetivos de ALTO NIVEL que AIDEN sostiene en el tiempo y
# tiene presentes en cada decisión. NO son tareas con hora (eso es guardar_en_json) ni notas
# sueltas (tomar_nota): son las metas que AIDEN debe acompañar. Viven en la conciencia compartida
# (Estado_Del_Mundo), así la conciencia ambiental las ve y puede ayudarte a avanzarlas.

from Nucleo_Slide.Estado_Del_Mundo import agregar_meta, cerrar_meta, metas_activas


def gestionar_metas(accion="listar", meta=""):
    """Gestiona los OBJETIVOS de alto nivel de Marco que AIDEN acompaña en el tiempo.
    accion: 'agregar' (nueva meta), 'cerrar' (marcar una como hecha), 'listar' (ver las activas)."""
    a = str(accion or "").strip().lower()
    meta = str(meta or "").strip()

    if "agreg" in a or "nueva" in a or "pon" in a or "añad" in a or "anad" in a or "crea" in a:
        if not meta:
            return "¿Cuál es la meta, señor?"
        agregar_meta(meta)
        return f"Anotada, señor. Tendré presente su meta: «{meta}». Le ayudaré a avanzarla."

    if "cerr" in a or "termin" in a or "complet" in a or "hech" in a or "logr" in a or "cumpl" in a:
        if not meta:
            return "¿Cuál meta doy por cumplida, señor?"
        cerrar_meta(meta)
        return f"¡Felicidades, señor! Marqué como cumplida la meta relacionada con «{meta}»."

    # listar (default)
    activas = metas_activas()
    if not activas:
        return "No tiene metas activas, señor. Dígame una y la acompaño."
    lista = "; ".join(m.get("texto", "") for m in activas[:8])
    return f"Sus metas activas, señor: {lista}."
