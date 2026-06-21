# "Explícame este error": Marco copia un error/traceback (o lo tiene en el portapapeles)
# y AIDEN lo explica en cristiano + cómo arreglarlo. Usa el modelo experto (mejor para
# depurar): entender bien un error vale más que la velocidad aquí.

from Funciones_Slide.Info.Experto import _cliente, MODELO_EXPERTO


def explicar_error(error=""):
    """Explica un error de programación (del texto dado o del portapapeles) y cómo arreglarlo."""
    texto = str(error or "").strip()

    # Si no me dictan el error, leo el que esté COPIADO en el portapapeles.
    if not texto:
        try:
            import pyperclip
            texto = (pyperclip.paste() or "").strip()
        except Exception:
            texto = ""

    if not texto:
        return ("No veo ningún error, señor. Copie el mensaje de error o el traceback "
                "y dígame 'explícame este error'.")

    texto = texto[:4000]   # recorta tracebacks gigantes

    try:
        r = _cliente.chat.completions.create(
            model=MODELO_EXPERTO,
            messages=[{
                "role": "user",
                "content": (
                    "Eres un profesor de programación claro y paciente (Marco es principiante). "
                    "Te paso un error o traceback. Explica en español y BREVE: 1) qué significa el "
                    "error en palabras simples, 2) por qué suele ocurrir, 3) cómo arreglarlo, con el "
                    "código corregido si aplica. No te enrolles.\n\nERROR:\n" + texto
                ),
            }],
            max_tokens=900,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude analizar el error, señor: {e}"
