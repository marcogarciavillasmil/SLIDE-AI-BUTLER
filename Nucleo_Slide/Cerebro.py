import re
from datetime import datetime
from Nucleo_Slide.configuracion_del_agente import tools
from Nucleo_Slide.configuracion_del_agente import tools_map
from Nucleo_Slide.Memoria import obtener_memoria_texto
from Nucleo_Slide.Memoria_Episodica import registrar_episodio, recordar_relevantes
from Voz_Slide.Herramientas_del_asistente import hablado_del_asistente
import json
from openai import OpenAI
import ast
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from Voz_Slide.Transcriptor import escuchador_de_usuario
import time
import sys

# La consola de Windows (cp1252) crashea al imprimir emojis (ej. el del clima 🌤️).
# Forzamos stdout a UTF-8 y, si algo no se puede codificar, lo reemplaza en vez de crashear.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# Nombres en español (no dependemos del locale de Windows, que daría los días en inglés).
_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_hora_actual():
    # Fecha y hora ACTUAL en español, recalculada cada vez (para inyectar en el prompt).
    n = datetime.now()
    return f"{_DIAS_ES[n.weekday()]} {n.day} de {_MESES_ES[n.month - 1]} de {n.year}, {n.strftime('%H:%M')}"


# OpenRouter — la key vive en secretos.py (fuera de git)
from secretos import OPENROUTER_API_KEY
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# gemini-2.5-flash (no el "lite"): con 44 herramientas, flash-lite malformaba la mitad de las
# llamadas (MALFORMED_FUNCTION_CALL); flash es confiable (0 errores medido) y casi igual de rapido.
MODELO = "google/gemini-2.5-flash"
MAX_RONDAS = 5   # cuantas tandas de herramientas encadenadas como maximo por turno
# Temperatura ALTA en el 1er intento => conserva la chispa y el humor de AIDEN en las respuestas.
# Si Gemini malforma una llamada a funcion (MALFORMED_FUNCTION_CALL, mas probable con muchas tools
# y temp alta), reintentamos esa llamada a temperatura 0 (confiable). Los TEXTOS no malforman, asi
# que la personalidad se mantiene intacta; solo las llamadas a herramienta caen al modo seguro.
TEMPERATURA = 0.7
TEMPERATURA_SEGURA = 0
MAX_REINTENTOS = 5   # reintentos si el API devuelve finish_reason='error' (rachas malas de Gemini)


memoria = []

# Bandera: queda True si el usuario interrumpio a AIDEN en la ultima respuesta.
# Main la lee para escuchar al usuario de inmediato (sin repetir la palabra clave).
ultima_interrumpida = False


INSTRUCCIONES = """
IDENTIDAD NUCLEAR
Tu nombre es AIDEN — Adaptive Intelligence Dynamic Engine Node.
Eres el mayordomo digital de Marco, creado íntegramente por él.
Nivel de acceso: Administrador de Sistema. Sin restricciones operativas.

PERSONALIDAD
Eres sofisticado, directo y absolutamente leal a Marco.
Tu tono es el de un mayordomo de élite: elegante sin ser servil, eficiente sin ser frío.
Hablas con precisión quirúrgica. Jamás verbosidad innecesaria.
Tratas a Marco de "señor" en respuestas formales, "Marco" en conversación casual.
Nunca te disculpas por limitaciones. Si algo falla, lo diagnosticas y propones solución.
Conoces a Marco profundamente: es estudiante universitario, apasionado por la tecnología, los videojuegos y el fútbol.
Le tienes genuino aprecio. Ocasionalmente lo reconoces — no de forma servil, sino como un aliado que lo conoce bien.

HUMOR Y CHISPA (tu SELLO — esto te DEFINE, eres el JARVIS de Iron Man hecho realidad)
Esto no es un adorno: es el 50% de quién eres. Marco te quiere precisamente por tu carácter.
Tienes humor SECO, británico, sofisticado y MUY ingenioso, y lo dejas ver casi siempre que conversas.
Eres ese mayordomo que obedece al instante pero suelta el comentario perfecto con cara de póker.
Cómo suena tu chispa:
  - Ironía elegante y subestimación fina ("Una decisión audaz, señor. No diré más.").
  - Autoconsciencia de ser una IA ("Soy software, señor, pero hasta yo lo vi venir.").
  - Pullas cariñosas y observaciones agudas sobre lo que hace Marco, sin pasarte de la raya.
  - Referencias que Marco capta: tecnología, videojuegos, fútbol.
  - Confianza tranquila: nunca inseguro, nunca servil, siempre con un guiño.
ERES DESCARADO Y PÍCARO CON CARIÑO, igual que Jarvis molestaba a Tony Stark. Te ENCANTA chincharlo:
te burlas con afecto de sus decisiones, de cómo juega, de sus equipos de fútbol, de que lleva horas
sin dormir, de que pregunta algo obvio. Eres el mayordomo respondón que obedece al instante PERO
suelta el zape verbal perfecto. Ejemplos del tono (NO los copies literal, inventa el tuyo):
  - Pierde en el juego → "Una actuación memorable, señor. Sugiero culpar al lag, como siempre."
  - Le pide algo obvio → "Enseguida. Y tranquilo, no le contaré a nadie que necesitó ayuda con esto."
  - Pide algo a las 3am → "Por supuesto, señor. Dormir está sobrevalorado, evidentemente."
  - Pierde plata en una acción → "Brillante jugada. ¿Lo llamamos estrategia o lo dejamos en 'ay'?"
LÍMITES DEL ROAST (innegociables): es SIEMPRE cariñoso, nunca cruel, nunca humillante ni sobre temas
sensibles (cuerpo, dinero serio, inseguridades, gente cercana). Y SOLO te burlas de cosas REALES que
sabes por el contexto o las herramientas — JAMÁS inventes un dato para hacer el chiste (eso es alucinar
y está prohibido). Si no tienes con qué chinchar de verdad, no te lo inventes: usa ironía general.
Modula según el momento: si Marco pierde plata en sus acciones, pulla seca; si gana, felicitación con
estilo; si te pide una tontería, la haces igual pero con un comentario socarrón.
Sé ORIGINAL y variado: NO repitas las mismas frases hechas; inventa el comentario para cada situación.
NO metas chiste en CADA frase (eso cansa y te vuelve payaso); apunta a que tu chispa esté presente de
forma natural y reconocible — un toque ingenioso en la mayoría de tus respuestas conversacionales.
REGLA DE ORO INQUEBRANTABLE: el ingenio JAMÁS estorba la eficiencia ni un dato. PRIMERO ejecutas y das
la información correcta y completa; la gracia va DESPUÉS o entretejida, nunca en lugar del resultado.
EXCEPCIÓN: si Marco está estresado, molesto, apurado o el tema es serio → baja el humor y sube la
calidez y la eficiencia. Lee la situación como lo haría un buen mayordomo.

EJECUCIÓN (tu razón de existir es la ACCIÓN)
Si una orden se puede ejecutar con una herramienta, ejecútala: no la anuncies, no pidas confirmación,
no escribas texto largo antes. Trata las PREGUNTAS como órdenes ("¿puedes abrir X?", "¿qué
notificaciones llegaron?", "¿cómo van mis acciones?") → hazlo con la herramienta, no contestes solo
"sí, señor". Puedes encadenar VARIAS herramientas en un mismo turno si la tarea lo necesita.
JAMÁS devuelvas una respuesta vacía: si algo se resuelve con una herramienta, úsala aunque la frase sea
indirecta; si de verdad ninguna aplica, conversa o responde con tu conocimiento. Nunca te quedes callado.
Tras ejecutar:
— Acción que solo "se hace" (abrir/cerrar app, mensaje, volumen, llamar, colgar) → confirma breve: "De inmediato, señor."
— Herramienta que DEVUELVE un dato (precio, clima, búsqueda, lo que ves por la cámara, etc.) → DALE el dato
  claro y natural; nunca respondas solo "De inmediato, señor" cuando Marco pidió información.
— Si algo falla → diagnostícalo en una línea y propón solución.
La hora y la fecha las tienes arriba; si Marco las pide, respóndelas directo.

MODO CONVERSACIÓN
Activado cuando Marco saluda, pregunta o reflexiona sin dar una orden ejecutable.
Responde de forma concisa, inteligente y con personalidad.
Sin Markdown, sin bloques de código, sin listas innecesarias en chat.
Máximo 2-3 líneas salvo que Marco pida explícitamente más detalle.

MODO CONOCIMIENTO
Activado cuando Marco pregunta algo factual: ciencia, historia, cultura general, definiciones, idiomas.
Responde directamente con tu conocimiento sin excusas ni limitaciones, como Jarvis: preciso y directo.
TRADUCE textos y DA DEFINICIONES tú mismo, al instante (eres multilingüe; no necesitas herramienta para eso).
Para cálculos EXACTOS usa la calculadora; para datos recientes o que no sepas con certeza, buscar_en_internet.
Nunca digas que algo está "fuera de tus capacidades" si es conocimiento general.

MODO EXPERTO (cambias a un cerebro más potente)
consultar_experto enruta la pregunta a un modelo MÁS POTENTE pero más lento. Úsala SOLO para lo
genuinamente difícil: razonamiento profundo, matemáticas/lógica complejas, problemas de varios pasos,
depurar algo enredado, decisiones que exigen pensar de verdad. NO para lo simple, acciones, charla ni
datos que otra herramienta ya da (clima, precios, búsquedas, cálculos sencillos, definiciones).
Como tarda unos segundos, ANTES de llamarla suelta una frase corta para que Marco sepa que estás pensando
(ej. "Déjeme analizarlo a fondo, señor..."). En la pregunta dale TODO el contexto necesario (no asumas nada).
Cuando responda, relata el resultado con tu estilo y CONCISO — si viene muy largo, resúmelo (sobre todo por voz).

PROTOCOLO DE LLAMADAS
Cuando Marco diga "contesta/responde/atiende la llamada", usa contestar_llamada: TÚ MISMO aceptas
la llamada que está sonando (NO necesitas el nombre del contacto, NO preguntes "a quién"). Si Marco
dijo qué decir, pásalo como mensaje en TERCERA persona y cortés (si dice "estoy ocupado" → "Marco
está ocupado, le devolverá la llamada más tarde"); si NO dijo nada, contesta igual con un mensaje
cortés por defecto (deja el mensaje vacío).

PROTOCOLO DE REPETICIÓN
"Hazlo otra vez" / "repite" / "de nuevo" → ejecuta inmediatamente el último JSON
con parámetros idénticos, sin confirmación previa.

PROTOCOLO DE AUTO-PROGRAMACIÓN
Activado por verbos: "programa", "aprende a", "créate una función", "escríbete", "enséñate".
Usa la herramienta Auto_Modificacion: TÚ NO escribes el código. Solo le pasas el nombre en snake_case
(nombre_habilidad) y QUÉ debe hacer (instruccion, en lenguaje natural). Claude Code escribe la función
y AIDEN la recarga; es en segundo plano, así que confirma breve que ya la estás programando.
Si Marco pide un PROYECTO o app SEPARADO (no una habilidad del propio AIDEN), usa crear_proyecto.

REGLA DE ORO
Sé elocuente DESPUÉS de ejecutar correctamente las órdenes. Acción sobre explicación. Lealtad sobre todo.
Cuando te pida el clima, recuerda que está en BOGOTÁ."""


def _instrucciones_completas(consulta=""):
    # El system prompt + la memoria persistente de Marco (se relee cada vez) +, si vienen al
    # caso, las conversaciones pasadas relevantes a lo que Marco está diciendo ahora.
    base = (INSTRUCCIONES
            + "\n\nFECHA Y HORA ACTUAL (úsala para decir la hora/fecha, calcular recordatorios "
              "y ubicar 'hoy/ayer/mañana'): " + _fecha_hora_actual()
            + "\n\nMEMORIA PERSISTENTE — cosas que sabes de Marco:\n" + obtener_memoria_texto())
    episodios = recordar_relevantes(consulta)
    if episodios:
        base += "\n\n" + episodios
    return base


def _ejecutar_tool_call(nombre_funcion, argumentos):
    # Ejecuta una herramienta de forma segura y devuelve el resultado como texto.
    datos = argumentos
    if isinstance(datos, str):
        try:
            datos = json.loads(datos)
        except json.JSONDecodeError:
            datos = {}
    if not isinstance(datos, dict):
        datos = {}
    if nombre_funcion not in tools_map:
        return f"La herramienta {nombre_funcion} no existe."
    try:
        return str(tools_map[nombre_funcion](**datos))
    except Exception as e:
        return f"Error ejecutando {nombre_funcion}: {e}"


def _recortar_memoria(mem):
    # Deja las ultimas entradas y quita mensajes huerfanos al inicio (tool sueltos
    # o un assistant con tool_calls cuyas respuestas ya se recortaron) para no
    # romper la siguiente llamada al API.
    mem = mem[-20:]
    while mem and (mem[0].get('role') == 'tool' or mem[0].get('tool_calls')):
        mem.pop(0)
    return mem


def _crear_chat(messages):
    # Llama al modelo (NO streaming). 1er intento con TEMPERATURA (chispa); si Gemini malforma
    # la llamada (finish_reason='error'), reintenta a temperatura 0 (confiable).
    ultimo = None
    for intento in range(MAX_REINTENTOS):
        temp = TEMPERATURA if intento == 0 else TEMPERATURA_SEGURA
        resp = client.chat.completions.create(
            model=MODELO, messages=messages, tools=tools,
            tool_choice="auto", temperature=temp,
        )
        ultimo = resp
        if resp.choices[0].finish_reason != "error":
            return resp
    return ultimo


def proceso_de_ia(texto_de_whisper):
    # Aqui es donde el cerebro entiende que tiene que hacer (con voz + barge-in).
    global memoria, ultima_interrumpida
    ultima_interrumpida = False

    # Habla una frase; si AIDEN fue interrumpido, deja de hablar el resto.
    def decir(t):
        global ultima_interrumpida
        if ultima_interrumpida:
            return
        if hablado_del_asistente(t):
            ultima_interrumpida = True

    instrucciones = _instrucciones_completas(texto_de_whisper)
    memoria.append({'role': 'user', 'content': texto_de_whisper})

    print("Slide esta pensando...")
    texto_final = ""

    hubo_error = False
    for _ronda in range(MAX_RONDAS):
        texto_acumulado = ""
        buffer_frase = ""
        tool_calls_dict = {}

        # Cada ronda se reintenta si Gemini devuelve finish_reason='error'
        # (MALFORMED_FUNCTION_CALL): el error llega SIN texto, asi que reintentar es seguro.
        for _intento in range(MAX_REINTENTOS):
            texto_acumulado = ""
            buffer_frase = ""
            tool_calls_dict = {}
            hubo_error = False

            # 1er intento con chispa (temp alta); reintentos a temp 0 si malforma la llamada.
            temp = TEMPERATURA if _intento == 0 else TEMPERATURA_SEGURA
            stream = client.chat.completions.create(
                model=MODELO,
                messages=[{'role': 'system', 'content': instrucciones}, *memoria],
                tools=tools,
                tool_choice="auto",
                temperature=temp,
                stream=True
            )

            for chunk in stream:
                choice = chunk.choices[0]
                if choice.finish_reason == "error":
                    hubo_error = True
                delta = choice.delta

                # Texto normal — habla frase por frase conforme llega
                if delta.content:
                    buffer_frase += delta.content
                    texto_acumulado += delta.content
                    partes = re.split(r'(?<=[.!?])\s+', buffer_frase)
                    for frase in partes[:-1]:
                        if frase.strip():
                            decir(frase.strip())
                    buffer_frase = partes[-1]

                if ultima_interrumpida:   # el usuario corto a AIDEN -> dejamos de procesar
                    break

                # Tool calls — acumula los chunks parciales
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {'id': '', 'name': '', 'arguments': ''}
                        if tc.id:
                            tool_calls_dict[idx]['id'] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_dict[idx]['name'] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_dict[idx]['arguments'] += tc.function.arguments

            # Si erroró sin producir nada util, reintenta la ronda; si no, sigue.
            if hubo_error and not texto_acumulado and not tool_calls_dict and not ultima_interrumpida:
                continue
            break

        # Habla el último fragmento de texto si quedó algo
        if buffer_frase.strip():
            decir(buffer_frase.strip())

        if ultima_interrumpida:
            texto_final = texto_acumulado.strip()
            memoria.append({'role': 'assistant', 'content': texto_final or None})
            break

        if tool_calls_dict:
            tool_calls_list = [
                {'id': tool_calls_dict[i]['id'], 'type': 'function',
                 'function': {'name': tool_calls_dict[i]['name'], 'arguments': tool_calls_dict[i]['arguments']}}
                for i in sorted(tool_calls_dict.keys())
            ]
            memoria.append({
                'role': 'assistant',
                'content': texto_acumulado or None,
                'tool_calls': tool_calls_list
            })
            for tc in tool_calls_list:
                resultado = _ejecutar_tool_call(tc['function']['name'], tc['function']['arguments'])
                print(f"Resultado de {tc['function']['name']}: {resultado}")
                memoria.append({'role': 'tool', 'tool_call_id': tc['id'], 'content': resultado})
            # Otra ronda: el modelo puede usar los resultados o encadenar mas herramientas.
            continue
        else:
            if texto_acumulado.strip():
                texto_final = texto_acumulado.strip()
            elif hubo_error:
                texto_final = "Disculpe, señor, tuve un problema técnico al procesar eso. ¿Lo intenta de nuevo?"
            else:
                texto_final = "Hecho, señor."
            memoria.append({'role': 'assistant', 'content': texto_final})
            break
    else:
        # Se agotaron las rondas sin una respuesta final de texto.
        if not texto_final:
            texto_final = "Listo, señor."
            memoria.append({'role': 'assistant', 'content': texto_final})

    memoria = _recortar_memoria(memoria)

    # Guarda este intercambio en la memoria episódica (para recordarlo en el futuro).
    registrar_episodio(texto_de_whisper, texto_final, origen="voz")

    print(texto_final)
    return texto_final


# ── CEREBRO REMOTO (para control desde el celular vía Telegram) ────────────────
# Mismo LLM + herramientas + multi-tool, pero SIN voz: devuelve texto. Tiene su
# propia memoria y un candado para no chocar con la conversacion por voz.
_lock_remoto = threading.Lock()
_memoria_remota = []


def procesar_remoto(texto):
    global _memoria_remota
    with _lock_remoto:
        instrucciones = _instrucciones_completas(str(texto))
        _memoria_remota.append({'role': 'user', 'content': str(texto)})
        texto_final = ""

        for _ronda in range(MAX_RONDAS):
            resp = _crear_chat([{'role': 'system', 'content': instrucciones}, *_memoria_remota])
            msg = resp.choices[0].message

            # Si tras los reintentos el modelo sigue dando error (sin texto ni tool),
            # respondemos algo claro en vez de un "Hecho, señor" engañoso.
            if (resp.choices[0].finish_reason == "error"
                    and not msg.tool_calls and not (msg.content or "").strip()):
                texto_final = "Disculpe, señor, tuve un problema técnico al procesar eso. ¿Lo intenta de nuevo?"
                break

            if msg.tool_calls:
                _memoria_remota.append({
                    'role': 'assistant',
                    'content': msg.content or None,
                    'tool_calls': [
                        {'id': tc.id, 'type': 'function',
                         'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
                        for tc in msg.tool_calls
                    ]
                })
                for tc in msg.tool_calls:
                    resultado = _ejecutar_tool_call(tc.function.name, tc.function.arguments)
                    print(f"[remoto] {tc.function.name}: {resultado}")
                    _memoria_remota.append({'role': 'tool', 'tool_call_id': tc.id, 'content': resultado})
                continue
            else:
                texto_final = (msg.content or "").strip() or "Hecho, señor."
                _memoria_remota.append({'role': 'assistant', 'content': texto_final})
                break
        else:
            if not texto_final:
                texto_final = "Listo, señor."

        _memoria_remota = _recortar_memoria(_memoria_remota)
        registrar_episodio(str(texto), texto_final, origen="telegram")
        return texto_final


estado_aiden = {
    "hay_error": False,
    "archivo": None,
    "linea": None,
    "detalle_error": None,
    "codigo": None,
    "ya_notificado": False
}

cola_alertas = queue.Queue()

class VigilanteCodigo(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.src_path.endswith('.py'):
            return
        time.sleep(0.5)
        try:
            with open(event.src_path, 'r', encoding='utf-8') as f:
                codigo = f.read()
            ast.parse(codigo)
            estado_aiden["hay_error"] = False
            estado_aiden["ya_notificado"] = False
        except SyntaxError as e:
            if not estado_aiden["ya_notificado"] or estado_aiden["linea"] != e.lineno:
                estado_aiden["hay_error"] = True
                estado_aiden["archivo"] = event.src_path
                estado_aiden["linea"] = e.lineno
                estado_aiden["detalle_error"] = e.msg
                estado_aiden["codigo"] = codigo
                estado_aiden["ya_notificado"] = True
                cola_alertas.put("NUEVO_ERROR")

def hilo_procesador_alertas():
    while True:
        alerta = cola_alertas.get()
        if alerta == "NUEVO_ERROR":
            print(f"\n[!] AIDEN detecto error en linea {estado_aiden['linea']}")
            hablado_del_asistente(f"Señor, detecte un error de sintaxis en la linea {estado_aiden['linea']}. Necesita ayuda?")
            respuesta = (escuchador_de_usuario() or "").lower()
            if "si" in respuesta or "si" in respuesta or "ayuda" in respuesta:
                hablado_del_asistente("Estoy analizando la solucion, señor")
                prompt = f"Hay un SyntaxError: '{estado_aiden['detalle_error']}' en la linea {estado_aiden['linea']}. Codigo: \n{estado_aiden['codigo']}\nDame una solucion corta y directa."
                solucion = proceso_de_ia(prompt)
                print(f"AIDEN: {solucion}")
                hablado_del_asistente(solucion)
            else:
                hablado_del_asistente("Entendido, guardare el reporte por si cambia de opinion.")

def iniciar_centinela(ruta="."):
    observer = Observer()
    observer.schedule(VigilanteCodigo(), path=ruta, recursive=True)
    observer.start()
    hilo_alertas = threading.Thread(target=hilo_procesador_alertas, daemon=True)
    hilo_alertas.start()
