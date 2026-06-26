from Voz_Slide.Herramientas_del_asistente import hablar_en_dispositivo

try:
    from secretos import DISPOSITIVO_LLAMADA
except ImportError:
    DISPOSITIVO_LLAMADA = None


def contestar_llamada(mensaje, colgar_al_terminar=True):
    # Flujo de contestadora: 1) ACEPTA la llamada que está sonando (pulsa "Accept"),
    # 2) le DICE el mensaje al contacto por el cable de audio (VB-CABLE), 3) CUELGA.
    # Si tú ya la tomaste/terminó, NO interviene (no habla encima de tu llamada).
    import time
    mensaje = str(mensaje).strip()
    if not mensaje:
        mensaje = "Marco está ocupado en este momento, le devolverá la llamada más tarde."

    hwnd = 0
    try:
        from Funciones_Slide.Comunicacion.Vigilante_Llamadas import (
            _ventanas_llamada, aceptar_ventana, colgar_ventana,
        )
        ventanas = list(_ventanas_llamada())
        if ventanas:
            hwnd = ventanas[0]
            if not aceptar_ventana(hwnd):
                # El botón Accept ya no está: la tomaste tú o la llamada terminó.
                return "La llamada ya no estaba sonando, señor; no intervine."
            time.sleep(1.5)   # deja que la llamada conecte antes de hablar
    except Exception:
        hwnd = 0

    if not DISPOSITIVO_LLAMADA:
        return ("Acepté la llamada, señor, pero el contacto no me escuchará hasta que configure "
                "el cable de audio virtual como micrófono de WhatsApp.")

    hablar_en_dispositivo(mensaje, DISPOSITIVO_LLAMADA)

    if hwnd and colgar_al_terminar:
        try:
            time.sleep(1.0)
            colgar_ventana(hwnd)
        except Exception:
            pass

    if hwnd:
        cola = " y colgué" if colgar_al_terminar else ""
        return f"Listo, señor. Acepté la llamada, le dije al contacto «{mensaje}»{cola}."
    # No había ventana de llamada detectable: igual transmití por el cable.
    return f"Dije el mensaje por el cable, señor: {mensaje}"
