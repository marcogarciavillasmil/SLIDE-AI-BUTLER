from Funciones_Slide.Sistema.Modos import _notificaciones_windows
from Funciones_Slide.Productividad.Alertas_Mercado import pausar_alertas
from Funciones_Slide.Sistema.Control_PC import ajustar_brillo
from Funciones_Slide.Sistema.Funciones_Sistema import subir_volumen, silenciar


def activar_protocolo(nombre):
    n = str(nombre).strip().lower()

    if "cine" in n or "pelicula" in n or "película" in n:
        _notificaciones_windows(False)
        pausar_alertas(True)
        ajustar_brillo("bajar")
        try:
            subir_volumen(0.2)
        except Exception:
            pass
        return ("Protocolo cine activado, señor. Bajé el brillo, subí el volumen y silencié las "
                "interrupciones. Que disfrute.")

    if "noche" in n or "dormir" in n:
        _notificaciones_windows(False)
        pausar_alertas(True)
        try:
            silenciar()
        except Exception:
            pass
        return "Buenas noches, señor. Silencié todo y dejé el equipo en calma. Que descanse."

    if "concentr" in n or "estudio" in n or "enfoque" in n or "trabajo" in n:
        _notificaciones_windows(False)
        pausar_alertas(True)
        return ("Protocolo de concentración activado, señor. Sin notificaciones ni interrupciones. "
                "A darle con todo.")

    if "normal" in n or "desactivar" in n or "fin" in n or "terminar" in n:
        _notificaciones_windows(True)
        pausar_alertas(False)
        return "Protocolos desactivados, señor. Todo vuelve a la normalidad."

    return "No conozco ese protocolo, señor. Tengo: cine, buenas noches, concentración, o normal."
