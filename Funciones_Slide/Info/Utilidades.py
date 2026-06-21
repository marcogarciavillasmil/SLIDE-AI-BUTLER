# Utilidades de AIDEN: calculadora exacta, conversor de moneda, traductor y definiciones.
# Los LLM fallan en aritmetica; estas tools dan resultados deterministas y reales.

import ast
import math
import operator


# ── CALCULADORA SEGURA (sin eval peligroso) ───────────────────────────────────
_OPERADORES = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_FUNCIONES = {
    "sqrt": math.sqrt, "raiz": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log10": math.log10, "exp": math.exp,
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
    "factorial": math.factorial,
}
_CONSTANTES = {"pi": math.pi, "e": math.e}


def _evaluar(nodo):
    if isinstance(nodo, ast.Constant):
        if isinstance(nodo.value, (int, float)):
            return nodo.value
        raise ValueError("valor no numérico")
    if isinstance(nodo, ast.BinOp):
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.left), _evaluar(nodo.right))
    if isinstance(nodo, ast.UnaryOp):
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    if isinstance(nodo, ast.Name):
        if nodo.id in _CONSTANTES:
            return _CONSTANTES[nodo.id]
        raise ValueError(f"nombre no permitido: {nodo.id}")
    if isinstance(nodo, ast.Call):
        if not isinstance(nodo.func, ast.Name) or nodo.func.id not in _FUNCIONES:
            raise ValueError("función no permitida")
        args = [_evaluar(a) for a in nodo.args]
        return _FUNCIONES[nodo.func.id](*args)
    raise ValueError("expresión no permitida")


def calculadora(expresion):
    """Resuelve una operación matemática EXACTA (suma, resta, potencias, raíces,
    trigonometría, etc.). Úsala siempre que Marco pida una cuenta o cálculo."""
    expr = str(expresion).strip().lower()
    # normaliza palabras comunes a símbolos
    reemplazos = {"x": "*", "÷": "/", "por": "*", "entre": "/", "más": "+",
                  "mas": "+", "menos": "-", "elevado a": "**", "al cuadrado": "**2",
                  "^": "**", ",": "."}
    for k, v in reemplazos.items():
        expr = expr.replace(k, v)
    try:
        arbol = ast.parse(expr, mode="eval")
        resultado = _evaluar(arbol.body)
        if isinstance(resultado, float) and resultado.is_integer():
            resultado = int(resultado)
        return f"El resultado es {resultado}, señor."
    except Exception:
        return "No pude resolver esa operación, señor. Dámela más simple (ej. '15% de 200' como '200*0.15')."


# ── CONVERSOR DE MONEDA (open.er-api.com, sin API key) ─────────────────────────
def convertir_moneda(cantidad, desde, hacia):
    """Convierte dinero entre monedas con la tasa de cambio actual (ej. 100 USD a COP)."""
    import requests
    try:
        cant = float(str(cantidad).replace(",", "."))
    except (ValueError, TypeError):
        return "Dame una cantidad numérica, señor."
    desde = str(desde).strip().upper()[:3]
    hacia = str(hacia).strip().upper()[:3]
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{desde}", timeout=10)
        datos = r.json()
        if datos.get("result") != "success":
            return f"No reconocí la moneda '{desde}', señor."
        tasa = datos["rates"].get(hacia)
        if tasa is None:
            return f"No reconocí la moneda '{hacia}', señor."
        convertido = cant * tasa
        return f"{cant:,.2f} {desde} son {convertido:,.2f} {hacia}, señor."
    except Exception as e:
        return f"No pude consultar la tasa de cambio, señor: {e}"


# ── TRADUCTOR (via el LLM ya configurado) ──────────────────────────────────────
def traducir(texto, idioma="inglés"):
    """Traduce un texto al idioma indicado (por defecto inglés)."""
    from openai import OpenAI
    from secretos import OPENROUTER_API_KEY
    cliente = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
    texto = str(texto).strip()
    if not texto:
        return "No me diste texto para traducir, señor."
    try:
        r = cliente.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{
                "role": "user",
                "content": f"Traduce este texto al {idioma}. Devuelve SOLO la traducción, "
                           f"sin comillas ni explicaciones:\n\n{texto}",
            }],
            max_tokens=500,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude traducir, señor: {e}"


# ── DEFINICIONES / WIKIPEDIA (REST API en español, sin key) ────────────────────
def definir(termino):
    """Da una definición o explicación breve de un término o concepto (vía Wikipedia)."""
    import requests
    termino = str(termino).strip()
    if not termino:
        return "¿Qué quieres que defina, señor?"
    try:
        url = "https://es.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(termino)
        r = requests.get(url, timeout=10, headers={"User-Agent": "AIDEN/1.0"})
        if r.status_code == 200:
            extracto = (r.json().get("extract") or "").strip()
            if extracto:
                return extracto
        return f"No encontré una definición clara de '{termino}', señor. ¿Busco en internet?"
    except Exception as e:
        return f"No pude buscar la definición, señor: {e}"