# AIDEN — Arquitectura a fondo (fuente para la wiki)

> Documento-fuente para el segundo cerebro. Describe CÓMO está construido AIDEN por dentro:
> los dos cerebros, el loop multi-herramienta, el streaming con barge-in, la escalada de
> temperatura, el modelo de dos niveles, las tres memorias, la capa de voz, el always-on y
> los comportamientos de fondo. Inmutable: refleja el estado a junio 2026 (43 herramientas).

---

## 1. Vista general

AIDEN es un asistente de voz tipo Jarvis. El flujo de alto nivel:

```
[Palabra clave por mic] → VAD.py
        ↓ (transcribe lo que dijiste)
[Cerebro de voz] proceso_de_ia()  ←→  herramientas (43 tools)
        ↓ (responde frase por frase, hablando mientras piensa)
[Voz Kokoro] hablado_del_asistente() → altavoz
        ↺ barge-in: si hablas encima, AIDEN se calla y te escucha
```

En paralelo corre un **segundo cerebro** (texto, sin voz) para Telegram, y varios
**hilos de fondo** que dan proactividad (anticipación, presencia, alertas, etc.).

Las piezas viven en paquetes:
- `Nucleo_Slide/` — el cerebro (Cerebro.py, configuracion_del_agente.py, Memoria.py, Memoria_Episodica.py).
- `Voz_Slide/` — voz (VAD.py wake word, Transcriptor.py STT, Herramientas_del_asistente.py TTS).
- `Interfaz/` — GUI (esfera HUD en PySide6 + HTML/WebChannel).
- `Funciones_Slide/` — las herramientas, en 4 subpaquetes (Comunicacion, Sistema, Info, Productividad).
- `Main.py` (fallback) / `Main_AlwaysOn.py` (real, lo lanza AIDEN.bat).

---

## 2. Los DOS cerebros

Misma lógica (mismo LLM, mismas tools, mismo loop multi-herramienta), pero dos entradas distintas:

### 2.1 `proceso_de_ia(texto)` — cerebro de VOZ (Nucleo_Slide/Cerebro.py)
- **Streaming**: pide la respuesta en `stream=True` y va HABLANDO frase por frase conforme
  llega el texto (no espera la respuesta completa → se siente rápido).
- **Barge-in**: si lo interrumpes hablando, deja de procesar (ver §4).
- Usa la lista `memoria` como contexto de la conversación.
- Marca `ultima_interrumpida` (bandera global) para que Main escuche de inmediato sin repetir palabra clave.

### 2.2 `procesar_remoto(texto)` — cerebro de TEXTO (Telegram)
- **NO streaming**: usa el helper `_crear_chat()` (una sola respuesta) y devuelve texto.
- Tiene su PROPIA memoria `_memoria_remota` y un candado `_lock_remoto` (para no chocar con la voz).
- Lo usa `Funciones_Slide/Comunicacion/Telegram_Control.py`.

### 2.3 Lo que comparten
- `INSTRUCCIONES` — el system prompt (identidad, personalidad/humor, reglas de ejecución, modos).
- `_instrucciones_completas(consulta)` — arma el prompt final cada turno: INSTRUCCIONES + **fecha/hora actual** + **memoria permanente** + **conversaciones pasadas relevantes** (memoria episódica).
- `_ejecutar_tool_call(nombre, args)` — ejecuta una herramienta de forma segura (parsea JSON, busca en `tools_map`, captura errores).
- `tools` / `tools_map` (configuracion_del_agente.py) — las 43 herramientas (esquema + función).

---

## 3. El loop MULTI-HERRAMIENTA (el corazón)

Un "turno" no es una sola llamada al LLM: es un **bucle de hasta `MAX_RONDAS=5` rondas**.
En cada ronda el modelo puede pedir herramientas; se ejecutan, se le devuelven los resultados,
y vuelve a decidir (puede encadenar otra herramienta o ya responder). Pseudocódigo:

```
para ronda en 1..5:
    respuesta = LLM(prompt + memoria + tools)
    si la respuesta pide herramientas:
        guarda el mensaje 'assistant' con los tool_calls
        ejecuta cada herramienta → guarda cada resultado como mensaje 'tool'
        continúa (otra ronda: el modelo usa los resultados)
    si no:
        es la respuesta final de texto → termina
```

Esto permite tareas de varios pasos en un solo turno (ej. *buscar un dato y luego actuar con él*).
En la voz, los `tool_calls` llegan **troceados** por el streaming y se reensamblan por índice
(`tool_calls_dict`).

---

## 4. Streaming + BARGE-IN (solo en voz)

Lo que hace que AIDEN se sienta vivo:

- **Hablar mientras piensa**: conforme el texto llega en el stream, se parte por frases
  (`regex (?<=[.!?])\s+`) y cada frase completa se manda a `decir()` → se habla ya, sin
  esperar el final.
- **Barge-in (interrumpir)**: mientras AIDEN habla, un **hilo vigía** (`_escuchar_interrupcion`
  en Herramientas_del_asistente.py) escucha el micrófono. Si detecta voz sostenida (volumen >
  umbral durante ~220ms), activa un `threading.Event` → AIDEN **corta el audio de golpe**
  (`sound.stop()`) y marca que fue interrumpido.
- `decir(t)`: si ya hubo interrupción, no habla; si `hablado_del_asistente(t)` devuelve True
  (interrumpido), prende `ultima_interrumpida`.
- Main lee `cerebro.ultima_interrumpida` y, si es True, escucha al usuario **sin pedir la
  palabra clave** (conversación fluida).
- `_lock_audio` serializa el audio: nunca suenan dos cosas a la vez.

---

## 5. La ESCALADA DE TEMPERATURA (clave de confiabilidad + personalidad)

Problema histórico: con muchas herramientas, Gemini a veces devuelve `finish_reason='error'`
(**MALFORMED_FUNCTION_CALL**): genera una llamada a función malformada y aborta → respuesta vacía.

Dato clave: ese error **solo ocurre al generar una LLAMADA a herramienta, nunca al escribir
texto** — y el humor de AIDEN vive en el texto. Por eso NO se baja la temperatura a 0 en general
(eso mataría la chispa, que es sagrada). Solución:

- **1er intento a `TEMPERATURA = 0.7`** → conserva personalidad y humor.
- Si malforma, **reintenta a `TEMPERATURA_SEGURA = 0`** (confiable), hasta `MAX_REINTENTOS = 5`.
- Así: respuestas con chispa + llamadas a herramienta confiables. Si persiste, da un mensaje
  claro en vez de un falso "Hecho, señor".

Está implementado en `_crear_chat()` (remoto) y en el bucle de stream de `proceso_de_ia()` (voz).
Arreglo de raíz adicional: el cerebro pasó de `gemini-2.5-flash-lite` (malformaba ~50%) a
`gemini-2.5-flash` (0 errores medidos, casi igual de rápido).

---

## 6. Modelo de DOS NIVELES (velocidad vs. profundidad)

- **Cerebro principal**: `MODELO = google/gemini-2.5-flash`. Rápido y confiable → ideal para voz
  (latencia > IQ para un asistente; un Jarvis lento no se siente Jarvis).
- **Cerebro experto**: `MODELO_EXPERTO = google/gemini-2.5-pro`, invocado SOLO para lo
  genuinamente difícil, vía dos herramientas:
  - `consultar_experto(pregunta)` (Info/Experto.py) — razonamiento profundo, mates/lógica, multi-paso.
  - `explicar_error(error)` (Info/Codigo.py) — depurar un error/traceback (lee el portapapeles).
- El prompt le dice que **avise con una frase corta antes** de llamar al experto (es lento) y que
  **relate el resultado conciso**. Decisión consciente: NO subir el cerebro principal a un modelo
  pesado (la latencia importa más que el IQ extra en el 95% de los casos).

---

## 7. Las TRES memorias

AIDEN tiene tres tipos de memoria, que se combinan:

1. **Contexto corto (la conversación actual)** — la lista `memoria` (voz) / `_memoria_remota`
   (Telegram). Son los mensajes que se mandan al LLM. Se recorta a los últimos ~20 con
   `_recortar_memoria()` (y quita mensajes huérfanos para no romper la API).
2. **Permanente (datos sobre Marco)** — `Nucleo_Slide/Memoria.py` → `memoria.json`, entradas
   `{texto, fecha, categoria}`. Herramientas `recordar` / `olvidar`. Se inyecta cada turno con
   `obtener_memoria_texto()`.
3. **Episódica (conversaciones pasadas)** — `Nucleo_Slide/Memoria_Episodica.py` →
   `memoria_episodica.json`. Cada turno se guarda `{fecha, hora, usuario, aiden, claves}`.
   - *Recall pasivo*: `recordar_relevantes(consulta)` cruza palabras clave con lo que dices ahora
     y lo inyecta al prompt (si no cruza nada, no inyecta ruido).
   - *Recall activo*: herramienta `recordar_conversacion(tema, dias)` para "¿de qué hablamos ayer?".
   - Sin embeddings ni base de datos vectorial: solo solapamiento de palabras clave + recencia.

Las tres se ensamblan en `_instrucciones_completas(consulta)` junto con la **fecha/hora actual**
(recalculada cada turno por `_fecha_hora_actual()`, en español, sin depender del locale).

---

## 8. La capa de VOZ

- **Wake word** (`Voz_Slide/VAD.py`): Silero VAD da la probabilidad de "hay voz" por chunk
  (512 muestras @16kHz). Mientras hay voz, acumula audio; al callar, transcribe con un Whisper
  **`medium` en CPU** (`modelo_rapido`) y revisa si aparece una palabra clave
  (DESPIERTA, SLIDE, OYE, AIDEN, …). **Clave**: este Whisper está en CPU, así que descargar los
  modelos CUDA (modo gaming) NO mata la palabra clave.
- **STT de la petición** (`Voz_Slide/Transcriptor.py`): `escuchador_de_usuario()` graba con
  SpeechRecognition y transcribe con Whisper **`small` en CUDA** (int8_float16). Carga perezosa
  (`_asegurar_modelo`) para poder descargarlo/recargarlo.
- **TTS** (`Voz_Slide/Herramientas_del_asistente.py`): Kokoro (es, Kokoro-82M, CUDA, cudnn=False).
  La voz es una **mezcla** de dos voces (`em_santa` 45% + `jf_alpha` 55%). Habla frase por frase
  (genera la siguiente mientras suena la actual) y empuja el nivel (RMS) a la esfera de la GUI
  para que se anime con la voz.

---

## 9. ALWAYS-ON (Main_AlwaysOn.py — el modo real)

Arquitectura para que AIDEN viva 24/7:

- **Candado de instancia única**: bind a socket `127.0.0.1:50607` al inicio. Si ya hay un AIDEN
  corriendo, la 2ª copia se cierra (evita OOM por duplicación).
- **Hilo principal = Qt corriendo siempre** (`app.exec()`), con la ventana SlideHUD persistente
  (oculta al inicio) + **icono en bandeja** (QSystemTrayIcon: "Mostrar AIDEN" / "Salir").
- **Hilo de fondo = `bucle_reposo`**: solo escucha la palabra clave; al detectarla emite
  `ventana.pedir_mostrar` y espera `_evento_oculto` (threading.Event).
- La ventana **se oculta sola tras 60s** → avisa por `al_ocultar` → el cerebro vuelve a REPOSO.
- El **login facial** se hace en el hilo principal (evita el bug de cámara entre hilos).
- `iniciar_telegram()` arranca **antes** del login (control remoto aunque no estés).
- Tras el login se lanzan los hilos de fondo: alertas de mercado, guardián de descanso,
  anticipación y **presencia**.

`Main.py` queda como fallback (misma idea sin bandeja/persistencia).

---

## 10. Comportamientos de FONDO (hilos, NO herramientas)

Decisión de diseño: la proactividad son **comportamientos** (hilos daemon), no tools — así no
gastan el cupo de function-calling ni dependen de que el modelo decida llamarlos.

- **Anticipación** (`Productividad/Anticipacion.py`): 8 avisos proactivos (clima mañanero,
  trasnochada, notas pendientes, disco lleno, GPU caliente, RAM alta, internet caído, apertura de
  mercado). Anti-molestia: máx 1/día por tipo, en franjas sensatas. Revisa cada 20 min.
- **Presencia** (`Sistema/Presencia.py`): cada 25s mira por la cámara y te saluda al LLEGAR (te
  reconoce por tu cara). 6 candados anti-molestia (ver fuente de presencia).
- **Alertas de mercado**, **guardián de descanso** (anti-maratón), **Telegram** (polling),
  **centinela de código** (watchdog: detecta SyntaxError en tus .py y se ofrece a ayudar).

Todos se **pausan en modo gaming**.

---

## 11. VRAM / Modo gaming (`Sistema/Modos.py`)

La RTX 5050 solo tiene 8GB. `modo_gaming` libera VRAM descargando los modelos CUDA:
- Whisper de voz: se descarga de una.
- Kokoro: se descarga DESPUÉS de hablar la confirmación (un hilo espera `_lock_audio`, para no
  recargarlo al decir "modo gaming activado").
- Recargan perezosamente cuando se usan, o al desactivar gaming.
- También silencia notificaciones de Windows y pausa los hilos de fondo.
- El wake word sigue vivo (su Whisper está en CPU).

---

## 12. Flujo de un turno completo (de punta a punta, en voz)

1. Dices la palabra clave → `VAD.py` la detecta y devuelve el texto.
2. Main llama `proceso_de_ia(texto)`.
3. Se arma el prompt: instrucciones + fecha/hora + memoria permanente + conversaciones relevantes.
4. El LLM responde en streaming; cada frase se va HABLANDO (Kokoro) mientras llega.
5. Si pide herramientas → se ejecutan, se le devuelven los resultados, y sigue (hasta 5 rondas).
6. Si malforma una llamada → reintenta a temperatura 0.
7. Mientras habla, un hilo vigía el mic → si interrumpes, corta y Main te vuelve a escuchar.
8. Al terminar: recorta la memoria de contexto y **guarda el intercambio en la memoria episódica**.

---

## 13. Archivos clave (mapa rápido)

| Archivo | Rol |
|---|---|
| `Nucleo_Slide/Cerebro.py` | Los dos cerebros, prompt, loop multi-tool, escalada de temperatura, fecha/hora |
| `Nucleo_Slide/configuracion_del_agente.py` | Las 43 herramientas (esquema `tools` + `tools_map`) |
| `Nucleo_Slide/Memoria.py` | Memoria permanente (datos de Marco) |
| `Nucleo_Slide/Memoria_Episodica.py` | Memoria episódica (conversaciones) |
| `Voz_Slide/VAD.py` | Palabra clave (Silero + Whisper medium CPU) |
| `Voz_Slide/Transcriptor.py` | STT de la petición (Whisper small CUDA) |
| `Voz_Slide/Herramientas_del_asistente.py` | TTS Kokoro + barge-in + animación de la esfera |
| `Main_AlwaysOn.py` | Arranque real (Qt + bandeja + reposo + hilos de fondo) |
| `Funciones_Slide/` | Las herramientas, en 4 subpaquetes |

---

### Conceptos para crear como páginas en la wiki (entidades/conceptos/decisiones)
- Conceptos: *loop multi-herramienta*, *streaming + barge-in*, *escalada de temperatura*,
  *modelo de dos niveles*, *las tres memorias*, *diseño anti-molestia*, *liberación de VRAM*.
- Decisiones: *flash vs flash-lite*, *no subir el cerebro a un modelo pesado*,
  *proactividad como comportamientos y no como tools*, *login facial en el hilo principal*.
- Entidades: cada archivo de la tabla §13 + cada una de las 43 herramientas.
