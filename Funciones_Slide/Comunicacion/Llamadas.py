from Voz_Slide.Herramientas_del_asistente import hablar_en_dispositivo

try:
    from secretos import DISPOSITIVO_LLAMADA
except ImportError:
    DISPOSITIVO_LLAMADA = None


def contestar_llamada(mensaje):
    # Habla 'mensaje' hacia el dispositivo de la llamada (cable de audio virtual),
    # para que el contacto escuche a AIDEN. Si no hay cable configurado, lo dice por
    # los parlantes y avisa que falta el setup.
    mensaje = str(mensaje).strip()
    if not mensaje:
        mensaje = "Marco está ocupado en este momento, le devolverá la llamada más tarde."

    hablar_en_dispositivo(mensaje, DISPOSITIVO_LLAMADA)

    if DISPOSITIVO_LLAMADA:
        return f"Listo, señor. Le transmití al contacto: {mensaje}"
    return ("Dije el mensaje, señor, pero el contacto no lo escuchará hasta que configure "
            "el cable de audio virtual como micrófono de WhatsApp.")
