# MEMORIA EPISÓDICA: AIDEN recuerda las CONVERSACIONES pasadas con Marco (no solo datos
# sueltos como Memoria.py, sino "qué nos dijimos y cuándo"). Así puede traer a colación
# cosas de antes ("la otra vez me dijiste...", "ayer hablamos de...").
#
# Cómo funciona, sin nada pesado (cero embeddings, cero base de datos vectorial):
#   - Cada turno se guarda como un EPISODIO {fecha, hora, usuario, aiden, claves}.
#   - Para recordar, se buscan episodios cuyas PALABRAS CLAVE se cruzan con lo que Marco
#     dice ahora (más reciente gana). Los relevantes se inyectan en el prompt del cerebro.
#   - También hay una herramienta (recordar_conversacion) para preguntar a propósito
#     "¿de qué hablamos ayer?" / "¿te acuerdas cuando...?".

import json
import os
from datetime import datetime, date, timedelta

# Archivo donde viven las conversaciones (raíz del proyecto). Es PRIVADO -> va en .gitignore.
_RUTA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memoria_episodica.json"
)

_MAX_EPISODIOS = 400     # tope para que no crezca sin control
_MAX_USUARIO = 300       # recorta lo que dijo Marco (evita guardar parrafadas)
_MAX_AIDEN = 250         # recorta la respuesta de AIDEN

# Palabras vacías (4+ letras) que NO sirven para buscar (sin tildes, como se guardan las claves).
_VACIAS = {
    "como", "para", "pero", "sobre", "entre", "cuando", "donde", "quien", "cual", "porque",
    "tambien", "esto", "esta", "este", "eso", "esa", "ese", "esos", "esas", "estos", "estas",
    "senor", "aiden", "ahora", "hola", "gracias", "favor", "puedes", "puede", "podrias",
    "quiero", "dime", "dame", "hacer", "tienes", "tengo", "estoy", "estan", "todo", "todos",
    "toda", "todas", "algo", "nada", "cosa", "cosas", "bien", "bueno", "buenas", "buenos",
    "vale", "okay", "oye", "hace", "hizo", "seria", "sera", "muy", "mas", "asi", "que",
}

_TILDES = str.maketrans("áéíóúüÁÉÍÓÚÜñÑ", "aeiouuAEIOUUnN")


def _normalizar(texto):
    return str(texto or "").translate(_TILDES).lower()


def _claves(texto):
    # Saca el conjunto de palabras significativas (4+ letras, sin tildes, sin vacías).
    limpio = "".join(c if c.isalnum() else " " for c in _normalizar(texto))
    return {p for p in limpio.split() if len(p) >= 4 and p not in _VACIAS}


def _cargar():
    if not os.path.exists(_RUTA):
        return []
    try:
        with open(_RUTA, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _guardar(datos):
    try:
        with open(_RUTA, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def registrar_episodio(usuario, aiden, origen="voz"):
    # Guarda un intercambio (lo que dijo Marco -> lo que respondió AIDEN). Nunca crashea
    # el cerebro: cualquier fallo se traga en silencio.
    try:
        usuario = str(usuario or "").strip()
        aiden = str(aiden or "").strip()
        if not usuario or not aiden:
            return

        # No guardar los prompts internos del vigilante de errores de sintaxis (ruido).
        if _normalizar(usuario).startswith("hay un syntaxerror"):
            return

        datos = _cargar()

        # Dedup: si el último episodio fue lo mismo que dijo Marco, no lo repitas
        # (p. ej. "repite" / "hazlo otra vez").
        if datos and datos[-1].get("usuario", "").strip().lower() == usuario.lower():
            return

        ahora = datetime.now()
        datos.append({
            "fecha": ahora.strftime("%d/%m/%Y"),
            "hora": ahora.strftime("%H:%M"),
            "usuario": usuario[:_MAX_USUARIO],
            "aiden": aiden[:_MAX_AIDEN],
            "origen": origen,
            "claves": sorted(_claves(usuario + " " + aiden)),
        })
        datos = datos[-_MAX_EPISODIOS:]
        _guardar(datos)
    except Exception:
        pass


def _formato(ep):
    fh = f"{ep.get('fecha', '')} {ep.get('hora', '')}".strip()
    return f'- [{fh}] Marco: "{ep.get("usuario", "")}" -> tú: "{ep.get("aiden", "")}"'


def recordar_relevantes(consulta, n=3):
    # Devuelve (como texto para el prompt) los episodios pasados más relevantes a lo que
    # Marco dice AHORA. Si no hay nada que cruce, devuelve "" (no inyecta ruido).
    try:
        claves_q = _claves(consulta)
        if not claves_q:
            return ""
        datos = _cargar()
        if not datos:
            return ""

        puntuados = []
        for i, ep in enumerate(datos):
            solapan = len(claves_q & set(ep.get("claves", [])))
            if solapan >= 1:
                puntuados.append((solapan, i, ep))   # i = recencia (mayor = más nuevo)
        if not puntuados:
            return ""

        puntuados.sort(key=lambda x: (x[0], x[1]), reverse=True)
        elegidos = [ep for _, _, ep in puntuados[:n]]
        # Ordenarlos cronológicamente para que se lean naturales.
        elegidos.reverse()

        lineas = [
            "CONVERSACIONES PASADAS RELEVANTES (ya hablaste esto con Marco; menciónalo con "
            "naturalidad SOLO si viene al caso, nunca a la fuerza):"
        ]
        lineas += [_formato(ep) for ep in elegidos]
        return "\n".join(lineas)
    except Exception:
        return ""


def recordar_conversacion(tema="", dias=None):
    # HERRAMIENTA del LLM: recall a propósito. "¿De qué hablamos ayer?", "¿te acuerdas
    # cuando hablamos de X?". Si hay 'tema' busca por palabra clave; si no, trae lo más
    # reciente. 'dias' opcional limita a los últimos N días.
    try:
        datos = _cargar()
        if not datos:
            return "Todavía no tengo conversaciones guardadas, señor."

        # Filtro por fecha (últimos 'dias' días) si se pide.
        if dias:
            try:
                limite = date.today() - timedelta(days=int(dias))
                filtrados = []
                for ep in datos:
                    try:
                        f = datetime.strptime(ep.get("fecha", ""), "%d/%m/%Y").date()
                        if f >= limite:
                            filtrados.append(ep)
                    except ValueError:
                        continue
                datos = filtrados
            except (ValueError, TypeError):
                pass

        if not datos:
            return "No encuentro conversaciones en ese rango de fechas, señor."

        tema = str(tema or "").strip()
        if tema:
            claves_t = _claves(tema)
            if claves_t:
                coincidencias = [
                    ep for ep in datos if claves_t & set(ep.get("claves", []))
                ]
            else:
                # tema demasiado corto/genérico: busca el texto crudo
                t = _normalizar(tema)
                coincidencias = [
                    ep for ep in datos
                    if t in _normalizar(ep.get("usuario", "") + " " + ep.get("aiden", ""))
                ]
            if not coincidencias:
                return f"No encuentro que hayamos hablado de '{tema}', señor."
            elegidos = coincidencias[-6:]
        else:
            elegidos = datos[-6:]   # los más recientes

        cabecera = (f"Esto es lo que encontré sobre '{tema}':" if tema
                    else "Nuestras conversaciones más recientes:")
        return cabecera + "\n" + "\n".join(_formato(ep) for ep in elegidos)
    except Exception as e:
        return f"No pude consultar el historial de conversaciones, señor: {e}"
