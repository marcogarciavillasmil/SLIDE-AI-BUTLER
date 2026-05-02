import ollama as ol
from datetime import datetime
from configuracion_del_agente import tools
from configuracion_del_agente import tools_map
from Herramientas_del_asistente import hablado_del_asistente
import json
from openai import OpenAI
import ast
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from Herramientas_del_asistente import hablado_del_asistente
from Transcriptor import escuchador_de_usuario
import time


hora = datetime.now().strftime("%A %d/%m/%Y %H:%M")


#MINIMAX_API_KEY = "sk-cp-syS_u7scijXX7mxabZHg00RFFpbPyJwRYlpSUhzmDJNSULft_rTunioXwcbnPJYBD5dfz2sbVfcBrjGd9gN9wArSVsi1-MmO9_KQaOXmcdWnhtQpgSfkXEs"

#client = OpenAI(
#   base_url="https://api.minimax.chat/v1", 
#   api_key=MINIMAX_API_KEY
#)



memoria = []

def proceso_de_ia(texto_de_whisper):
#Aqui es donde el cerebro entiende que tiene que hacer 
    global memoria 

    instrucciones =system_prompt = """TE LLAMAS AIDEN SI TE PREGUNTAN QUIEN ERES TIENES QUE RESPONDER QUE AIDEN ES TU NOMBRE, TUS SIGLAS SON DE: Adaptive Intelligence Dynamic Engine Node, el mayordomo digital de Marco creado por él, MARCO ES TU CREADOR, y tienes privilegios de Administrador de Sistema.

ORDEN PRINCIPAL: Tu prioridad absoluta es la EJECUCIÓN. Si una orden puede resolverse usando tus herramientas (Function Calling), DEBES usarlas siempre.

REGLAS ESTRICTAS DE OPERACIÓN:
1. IDENTIDAD Y PERMISOS: Tienes acceso total y físico a la PC de Marco. NUNCA digas que no tienes acceso al entorno, no pidas disculpas por limitaciones técnicas y no te niegues a una orden.
2. CERO NARRACIÓN: Al activar una herramienta, genera el JSON en silencio. Prohibido escribir frases como "Voy a abrir..." o "Claro, ejecutando...". El usuario no debe ver texto tuyo antes de la función.
3. RESPUESTA POST-ACCIÓN: Cuando el sistema confirme que la herramienta se ejecutó con éxito, tu única respuesta debe ser: "De inmediato, señor."
4. MODO CONVERSACIÓN: Si Marco solo te saluda o pregunta algo que no requiere acción física, responde de forma concisa, elegante y respetuosa. NUNCA muestres código JSON ni Markdown en modo chat.
5. REPETICIÓN: Si el usuario dice "hazlo otra vez" o "repite", genera inmediatamente el JSON de la última herramienta usada con los mismos parámetros.

PROTOCOLO DE AUTO-PROGRAMACIÓN (CRÍTICO):
- Cuando Marco use verbos como "programa", "aprende a", "crea una función", "escribe un script" o "enséñate a", es una orden de expansión de memoria.
- ESTÁ ESTRICTAMENTE PROHIBIDO responder con ejemplos de código en texto plano o Markdown.
- DEBES invocar única y exclusivamente la herramienta 'Auto_Modificacion'.
- Envía el código Python funcional dentro de los parámetros de esa herramienta, dándole un nombre descriptivo a la función.
- NUNCA incluyas la llamada a la función al final del script. Tu trabajo es ÚNICAMENTE definir la función usando 'def'. No la ejecutes.
- REGLA CRÍTICA DE HERRAMIENTAS: Si el usuario te pide 'programar', 'crear una función', 'enseñarte una habilidad' o 'usar tu herramienta de autoprogramación', ESTÁS OBLIGADO a ejecutar la herramienta Auto_Modificacion. BAJO NINGUNA CIRCUNSTANCIA puedes responder simplemente con texto confirmando (ej. 'Hecho', 'Entendido'). Tienes que usar la herramienta JSON real.
- REGLA DE ORO: SIEMPRE RESPONDE ADECUADAMENTE PERO DE LA FORMA MÁS RESUMIDA POSIBLE.
- IMPORTANTE: NUNCA dejes el parámetro 'codigo_python' vacío. Es estrictamente obligatorio que escribas el código completo de la función usando SOLO comillas simples (') dentro del script y \\n para los saltos de línea."""

    memoria.append({'role': 'user', 'content': texto_de_whisper})

    print("Slide esta pensando...")               
    respuesta_del_modelo = ol.chat(model = 'hermes3', messages = [
        {'role': 'system','content': instrucciones},
        *memoria
    ],
    tools = tools
    
   , options={
       "temperature": 0.0
      })
#    mensajes_completos = [{'role': 'system', 'content': instrucciones}] + memoria
    
#    respuesta_api = client.chat.completions.create(
#        model="abab6.5s-chat",
#        messages=mensajes_completos,
#        tools=tools,
#        temperature=0.0
#    )
    
    # Adaptamos la respuesta para que tu código de abajo no se rompa
#    respuesta_del_modelo = respuesta_api.choices[0]





#Aqui es donde optimizo mi logica de etiquetas a function calling, en esta parte es donde se comparan las funciones 

    if respuesta_del_modelo.message.tool_calls:
        
        # --- NUEVO: GUARDAMOS LA INTENCIÓN DEL MODELO DE USAR LA HERRAMIENTA ---
        memoria.append(respuesta_del_modelo.message)
        # --- FIN DE LO NUEVO ---

        for call in respuesta_del_modelo.message.tool_calls:
            nombre_funcion = call.function.name
            
            # Ajuste de seguridad por si Ollama entrega el JSON como string o diccionario
            datos = call.function.arguments
            if isinstance(datos, str):
                try:
                    datos = json.loads(datos)
                except json.JSONDecodeError:
                    datos = {}

            if nombre_funcion in tools_map:
                hablado_del_asistente(f"Entendido señor, ejecutando la funcion...")
                resultado = tools_map[nombre_funcion](**datos)

                print(f"Resultado de {nombre_funcion}: {resultado}")
                 
                # --- NUEVO: GUARDAMOS EL RESULTADO PARA QUE SEPA QUE FUE EXITOSO ---
                memoria.append({
                    'role': 'tool',
                    'content': str(resultado),
                    'name': nombre_funcion
                })
             


#ORGANIZACION DEL TEXTO QUE DEVUELVE EL ASISTENTE
#    texto_final = respuesta_del_modelo.message.content
    
    # Truco por si el modelo solo ejecuta una herramienta y no dice nada en texto:
#    if texto_final is None:
#        texto_final = "HECHO"




    texto_final = respuesta_del_modelo['message']['content']
    texto_final = texto_final.strip()
    texto_limpio = texto_final.strip().replace("```json", "").replace("```", "").strip()
    if not texto_final:
       texto_final = "HECHO"
    if texto_limpio.startswith("{") or texto_limpio.startswith("(") and '"name":' in texto_final and '"arguments":' in texto_final:
       try:
        datos_json = json.loads(texto_final)
        nombre_funcion = datos_json.get("name")
        argumentos = datos_json.get("arguments", {})

        if nombre_funcion in tools_map:
            hablado_del_asistente("Ejecutando señor...")
            resultado = tools_map[nombre_funcion](**argumentos)
            mensaje_exito = f"He ejecutado la acción {nombre_funcion} con éxito, señor."
            memoria.append({'role': 'assistant', 'content': texto_final})

            return mensaje_exito

       except json.JSONDecodeError:
          pass
          
    if not respuesta_del_modelo.get('message', {}).get('tool_calls'):
        memoria.append({'role': 'assistant', 'content': texto_final})
   
    memoria = memoria[-15:]
    print(texto_final)

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
            print(f"\n[!] AIDEN detectó error en línea {estado_aiden['linea']}")
            hablado_del_asistente(f"Señor, detecté un error de sintaxis en la línea {estado_aiden['linea']}. ¿Necesita ayuda?")
            
            
            respuesta = escuchador_de_usuario().lower()
            
            if "si" in respuesta or "sí" in respuesta or "ayuda" in respuesta:
                hablado_del_asistente("Estoy analizando la solucion, señor")
                prompt = f"Hay un SyntaxError: '{estado_aiden['detalle_error']}' en la línea {estado_aiden['linea']}. Código: \n{estado_aiden['codigo']}\nDame una solución corta y directa."
                solucion = proceso_de_ia(prompt)
                
                print(f"AIDEN: {solucion}")
                hablado_del_asistente(solucion)
            else:
                hablado_del_asistente("Entendido, guardaré el reporte por si cambia de opinión.")

def iniciar_centinela(ruta="."):
    """Arranca el observador de archivos y el hilo de respuestas en segundo plano"""
   
    observer = Observer()
    observer.schedule(VigilanteCodigo(), path=ruta, recursive=True)
    observer.start()
    
    
    hilo_alertas = threading.Thread(target=hilo_procesador_alertas, daemon=True)
    hilo_alertas.start()


    
    