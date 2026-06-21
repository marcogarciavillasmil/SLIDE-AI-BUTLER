# Resumen de videos de YouTube por su transcripcion (subtitulos), sin API key.
# Baja la transcripcion y la resume con el LLM. Sirve para "resume este video".

import re


def _id_video(url_o_id):
    s = str(url_o_id).strip()
    # si ya es un ID (11 caracteres tipicos), devuelvelo
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else None


def resumir_youtube(url):
    """Resume un video de YouTube a partir de su transcripción (subtítulos).
    Recibe el enlace del video o su ID."""
    from youtube_transcript_api import YouTubeTranscriptApi

    vid = _id_video(url)
    if not vid:
        return "No reconocí el enlace del video, señor. Pásame la URL de YouTube."
    try:
        api = YouTubeTranscriptApi()
        datos = api.fetch(vid, languages=["es", "en"])
        texto = " ".join(s.text for s in datos)
    except Exception as e:
        return f"No pude obtener la transcripción del video, señor (puede no tener subtítulos): {e}"

    if not texto.strip():
        return "El video no tiene transcripción disponible, señor."

    texto = texto[:12000]  # recorta para no gastar demasiados tokens
    try:
        from openai import OpenAI
        from secretos import OPENROUTER_API_KEY
        cliente = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        r = cliente.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{
                "role": "user",
                "content": "Eres AIDEN, asistente de Marco. Resume de qué trata este video de "
                           "YouTube en pocas líneas, con los puntos clave:\n\n" + texto,
            }],
            max_tokens=400,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Bajé la transcripción pero no pude resumirla, señor: {e}"