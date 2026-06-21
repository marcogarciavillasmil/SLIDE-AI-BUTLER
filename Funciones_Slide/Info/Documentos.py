import os
from openai import OpenAI
from secretos import OPENROUTER_API_KEY

_cliente = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

_CARPETAS = [
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Documents"),
    os.path.join(os.path.expanduser("~"), "Desktop"),
]


def _buscar_archivo(nombre):
    nombre = nombre.lower().strip()
    if os.path.exists(nombre):           # por si dan la ruta completa
        return nombre
    for carpeta in _CARPETAS:
        if not os.path.isdir(carpeta):
            continue
        for f in os.listdir(carpeta):
            if nombre in f.lower() and f.lower().endswith((".pdf", ".txt")):
                return os.path.join(carpeta, f)
    return None


def _extraer_texto(ruta):
    if ruta.lower().endswith(".pdf"):
        from pypdf import PdfReader
        lector = PdfReader(ruta)
        return "\n".join((p.extract_text() or "") for p in lector.pages)
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def resumir_documento(nombre_archivo):
    ruta = _buscar_archivo(str(nombre_archivo))
    if not ruta:
        return f"No encontré el documento '{nombre_archivo}' en Descargas, Documentos ni Escritorio, señor."
    try:
        texto = _extraer_texto(ruta)[:8000]   # recorta para no gastar demasiados tokens
    except Exception as e:
        return f"No pude leer el documento, señor: {e}"
    if not texto.strip():
        return "El documento parece vacío o es una imagen sin texto, señor."
    try:
        r = _cliente.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{
                "role": "user",
                "content": f"Eres AIDEN, asistente de Marco. Resume este documento de forma clara y "
                           f"breve (lo importante, en pocas líneas):\n\n{texto}",
            }],
            max_tokens=400,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude resumir el documento, señor: {e}"


def resumir(fuente):
    # Resume lo que le des: si es un enlace de YouTube -> resume el video; si no, lo trata
    # como un archivo (PDF/texto) y lo resume.
    f = str(fuente or "").strip()
    if not f:
        return "¿Qué quiere que resuma, señor? Dígame el nombre del archivo o el enlace."
    low = f.lower()
    if "youtube.com" in low or "youtu.be" in low or "watch?v=" in low:
        from Funciones_Slide.Info.Youtube import resumir_youtube
        return resumir_youtube(f)
    return resumir_documento(f)
