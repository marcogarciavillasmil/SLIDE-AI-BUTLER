# Modo experto: enruta preguntas GENUINAMENTE DIFÍCILES a un modelo más potente
# (gemini-2.5-pro) y devuelve la respuesta. El cerebro normal (flash) maneja todo lo
# demás rápido; esto solo se llama en lo difícil, así que el costo por consulta no importa.

from openai import OpenAI
from secretos import OPENROUTER_API_KEY

MODELO_EXPERTO = "google/gemini-2.5-pro"

_cliente = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


def consultar_experto(pregunta):
    """Resuelve una pregunta difícil con un modelo más potente y devuelve la respuesta."""
    pregunta = str(pregunta).strip()
    if not pregunta:
        return "¿Qué quiere que analice a fondo, señor?"
    try:
        r = _cliente.chat.completions.create(
            model=MODELO_EXPERTO,
            messages=[{
                "role": "user",
                "content": "Eres un experto riguroso. Responde en español de forma clara, correcta y bien "
                           "razonada. Si es un cálculo o un problema, resuélvelo paso a paso y da el "
                           "resultado final:\n\n" + pregunta,
            }],
            max_tokens=1200,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude consultar al experto, señor: {e}"
