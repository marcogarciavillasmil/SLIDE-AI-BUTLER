# AIDEN — Bugs resueltos (fuente para la wiki)

> Documento-fuente para el segundo cerebro: cada bug con su **causa raíz** y su **arreglo**.
> Útil para crear páginas de "bug/lección" en la wiki y para no repetir errores.
> Las rutas reflejan la reorganización en subpaquetes (junio 2026).

---

## A. Bugs de lógica / crashes

### A1 — `cerrar_aplicacion` se rendía antes de tiempo
- **Archivo**: `Funciones_Slide/Sistema/Funciones_Sistema.py`
- **Causa raíz**: el `except` tenía un `return` DENTRO del bucle que recorre procesos. Si un
  proceso ajeno (de Windows) negaba el acceso, la función se rendía ANTES de llegar a la app.
- **Arreglo**: `return` → `continue` (saltar ese proceso y seguir). Ahora cierra TODAS las
  ventanas del proceso y decide el mensaje solo al final.

### A2 — `monitor_de_tareas` mataba el hilo de tareas
- **Archivo**: `Funciones_Slide/Productividad/Tareas_Hilos_Comandos.py`
- **Causa raíz**: typo `ident=4` (lo correcto es `indent=4`) → `json.dump` lanzaba error y
  mataba el hilo cada vez que se completaba una tarea. Además, si `tareas.json` no existía,
  `open(...)` reventaba al arrancar.
- **Arreglo**: `ident`→`indent`; si no existe el archivo, espera 30s y reintenta (no crashea);
  el aviso de voz se sacó del bloque que escribe el archivo.

### A3 — `limpiar_historial` crasheaba siempre
- **Archivo**: `Funciones_Slide/Sistema/Comandos_Asistente.py`
- **Causa raíz**: el mismo typo `ident=4`.
- **Arreglo**: `ident`→`indent`, protección si no existe el archivo, y ahora devuelve confirmación.

### A4 — `.lower()` sobre `None` (centinela)
- **Archivo**: `Nucleo_Slide/Cerebro.py`
- **Causa raíz**: `escuchador_de_usuario()` puede devolver `None` (silencio); hacer
  `None.lower()` revienta.
- **Arreglo**: `(escuchador_de_usuario() or "").lower()`.

### A5 — `Cara = None` → IndexError en el login facial
- **Archivo**: `Funciones_Slide/Sistema/Comandos_Asistente.py`
- **Causa raíz**: al mover el archivo a `Funciones_Slide/Sistema/`, el path de
  `Imagenes/Marco.jpg` quedó con un `dirname` de menos → `cv2.imread` devolvía `None` →
  `face_recognition.face_locations(None)[0]` crasheaba.
- **Arreglo**: 3 niveles de `dirname` (Sistema → Funciones_Slide → raíz del proyecto).

### A6 — "Acceso denegado" tardío
- **Archivo**: `Main.py`
- **Causa raíz**: `Reconocimiento_de_habla()` corría ANTES del `if` de verificación → un extraño
  que fallaba el login dejaba a AIDEN escuchando para siempre sin negar el acceso.
- **Arreglo**: mover la espera de palabra clave DENTRO del bloque "Bienvenido Marco".
  (`Main_AlwaysOn.py` ya lo hacía bien: niega y `sys.exit(0)`.)

---

### A7 — Whisper alucinaba comandos sobre el silencio (Amara.org)
- **Archivo**: `Voz_Slide/Transcriptor.py` + `Voz_Slide/VAD.py`
- **Síntoma**: sin que Marco dijera nada, AIDEN "oía" frases y actuaba (p. ej. se puso a buscar
  en Google *"Subtítulos por la comunidad de Amara.org"*; también salía *"¡Suscríbete!"*).
- **Causa raíz**: Whisper se entrenó con millones de subtítulos de YouTube, donde frases como
  "Subtítulos por la comunidad de Amara.org" o "¡Suscríbete!" aparecen muchísimo. Ante
  **silencio o ruido** (no audio vacío, sino casi-silencio), el modelo "rellena" con esas frases
  fantasma en vez de devolver vacío. El cerebro las tomaba como un comando real.
  - `escuchador_de_usuario` (conversación continua) transcribía SIN ningún filtro de voz.
  - En `VAD.py`, tras despertar (`asistente_despierto=True`) se devolvía CUALQUIER texto de la
    ventana de 25s, incluido el alucinado.
- **Arreglo (2 capas)**:
  1. `vad_filter=True` + `condition_on_previous_text=False` en las dos llamadas a `transcribe`
     (el Silero VAD interno de faster-whisper descarta el audio sin voz real ANTES de transcribir).
  2. Guardia `es_alucinacion(texto)` (en `Transcriptor.py`, importada también en `VAD.py`):
     lista negra de frases fantasma conocidas; si la transcripción es solo eso, se descarta
     (`escuchador_de_usuario` devuelve `None`; el wake-loop hace `continue`). Log `🛇 Alucinacion descartada`.

---

## B. Bugs del LLM / function-calling

### B1 — `MALFORMED_FUNCTION_CALL` (el grande)
- **Archivo**: `Nucleo_Slide/Cerebro.py`
- **Causa raíz**: con muchas tools y temperatura alta, `gemini-2.5-flash-lite` devolvía
  `finish_reason='error'` intermitente (~50%, medido 3/6): generaba una llamada a función
  malformada y abortaba → respuesta vacía que caía en "Hecho, señor".
- **Dato clave**: el error SOLO ocurre al generar una LLAMADA a herramienta, nunca al escribir texto.
- **Arreglo (de raíz)**: cambiar el cerebro a `gemini-2.5-flash` (0 errores medidos).
- **Arreglo (robustez)**: escalada de temperatura — 1er intento a `0.7` (chispa); si malforma,
  reintenta a `0` (`MAX_REINTENTOS=5`). Si persiste, mensaje claro en vez de un falso "Hecho, señor".

### B2 — Telegram solo respondía "Hecho, señor"
- **Causa raíz**: era el mismo B1 (MALFORMED dejaba la respuesta vacía).
- **Arreglo**: el cambio de modelo + se reforzó el prompt (tratar preguntas como órdenes,
  regla anti-silencio).

### B3 — Crash al imprimir emojis (UnicodeEncodeError)
- **Archivo**: `Nucleo_Slide/Cerebro.py`
- **Causa raíz**: la consola de Windows (cp1252) crasheaba al imprimir el emoji del clima 🌤️.
- **Arreglo**: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` al inicio.

---

## C. Bugs de concurrencia / recursos

### C1 — OOM (`mkl_malloc failed`) por DOS instancias
- **Causa raíz**: corrían DOS AIDEN a la vez (el auto-arranque lanzaba el viejo `Main.py` y
  Marco abría `Main_AlwaysOn.py` con F5) → se duplicaban los modelos → sin memoria.
- **Arreglo**: candado de instancia única (bind a `127.0.0.1:50607`); la 2ª copia se cierra.
  `AIDEN.bat` ahora lanza solo `Main_AlwaysOn.py`.

### C2 — Kokoro se descargaba ANTES de hablar la confirmación (modo gaming)
- **Archivo**: `Funciones_Slide/Sistema/Modos.py`
- **Causa raíz**: al activar gaming, descargar Kokoro de inmediato impedía decir "modo gaming
  activado" (lo recargaba para hablar).
- **Arreglo**: Whisper de voz se descarga de una; Kokoro se descarga en un hilo que espera
  `_lock_audio` (después de hablar la confirmación).

### C3 — Re-login en always-on
- **Archivo**: `Main_AlwaysOn.py`
- **Causa raíz**: el loop original re-ejecutaba el login/palabra clave cada vez que se cerraba la ventana.
- **Arreglo**: estructura `while True: escucha palabra clave → muestra ventana → espera a que se
  oculte (Event) → repite`. Login facial una sola vez.

---

## D. Bugs de la reorganización (subpaquetes)

### D1 — 46 imports rotos
- **Causa raíz**: al mover los módulos a subpaquetes (`Comunicacion/`, `Sistema/`, `Info/`,
  `Productividad/`), todos los `from Funciones_Slide.X import ...` quedaron mal.
- **Arreglo**: script de migración (regex) que reescribió los 46 imports; verificado: 0 imports
  viejos, todo compila.

### D2 — `import whisper` muerto + paquete `whisper` ajeno
- **Archivo**: `Voz_Slide/Transcriptor.py` + `requirements.txt`
- **Causa raíz**: `import whisper` (y `import sys`) sin usar; y en el venv había DOS paquetes
  `whisper` que chocan: `openai-whisper` (sin usar; el código usa `faster-whisper`) y
  `whisper==1.1.10` (¡el de Graphite, una DB de series de tiempo, basura ajena!).
- **Arreglo**: quitados los imports muertos y el paquete Graphite de `requirements.txt`.

---

## E. Proactividad / robustez

### E1 — La anticipación marcaba el día aunque fallara wttr.in
- **Archivo**: `Funciones_Slide/Productividad/Anticipacion.py`
- **Causa raíz**: si el clima fallaba (error transitorio), igual marcaba el aviso como "ya dado hoy".
- **Arreglo**: `_avisos_clima()` devuelve `None` en fallo transitorio (no marca, reintenta) vs `[]`
  (sí marca, no hay nada que avisar).

### E2 — Telegram arrancaba DESPUÉS del login
- **Causa raíz**: `iniciar_telegram()` se llamaba tras el login facial → inútil para control remoto
  cuando Marco no está.
- **Arreglo**: moverlo ANTES del login (su seguridad es independiente: chat_id).

---

## F. Seguridad / git

### F1 — El venv casi se sube a GitHub
- **Causa raíz**: `Asistente_Slide_311/` (el venv, cientos de MB) no estaba en `.gitignore`
  (estaba `Asistente/`, nombre viejo) → un `git add .` lo habría subido.
- **Arreglo**: añadido `Asistente_Slide_311/` al `.gitignore` antes del push.

### F2 — 🔴 API key en el historial (PENDIENTE, acción de Marco)
- **Causa raíz**: la `OPENROUTER_API_KEY` quedó en commits viejos del repo público.
- **Estado**: NO resuelto. Hay que **rotar la key** (generar nueva, revocar vieja) y considerar
  hacer el repo privado / limpiar el historial. `secretos.py` ya está en `.gitignore`.

---

## Lecciones transversales (para la wiki)
- Un typo en un parámetro (`ident` vs `indent`) puede matar un hilo en silencio.
- `return` dentro de un bucle lo corta: cuidado dónde va.
- Asume siempre que una función puede devolver `None` y protégete (`or ""`).
- Verifica que un archivo exista antes de abrirlo; verifica los paths tras mover archivos.
- Con muchas tools, vigila el `MALFORMED_FUNCTION_CALL`: el error vive en las llamadas, no en el texto.
- Una sola instancia: candado de socket para no duplicar procesos pesados.
- Whisper sobre silencio NO devuelve vacío: alucina frases de su entrenamiento (subtítulos de
  YouTube). Filtra con VAD antes de transcribir y ten una lista negra de frases fantasma.
