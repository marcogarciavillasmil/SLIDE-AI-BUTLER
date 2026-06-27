# AIDEN — Mejoras de voz, llamadas y escalado (FUENTE para ingesta en el segundo cerebro)

> **Para el Claude Code de Obsidian (ingesta):** este es un documento-FUENTE autocontenido con las
> mejoras hechas a AIDEN DESPUÉS del documento *AIDEN Constructor*. Procésalo como las otras fuentes
> del segundo cerebro: crea/actualiza páginas de ENTIDAD (módulos, herramientas), de CONCEPTO y de
> DECISIÓN, y enlázalas. Al final de cada sección dejo sugerencias de "Para la wiki". Estado: junio
> 2026, 46 herramientas. Complementa: *Arquitectura*, *Herramientas*, *Bugs resueltos*, *Decisiones*,
> *AIDEN Constructor*.

Cubre 10 mejoras:
1. Filtro anti-alucinaciones de Whisper (Bug A7).
2. Modo manos libres (sesión de mic abierto).
3. Comandos de voz de ventana ampliados (descansa / quédate).
4. Vigilante de llamadas entrantes (auto-contesta como contestadora).
5. Escalado automático Flash → Pro (fallback de inteligencia).
6. Centinela de pantalla (avisa de apps congeladas / errores).
7. Portapapeles inteligente (reacciona a lo que copias).
8. Modo reunión automático (silencia distracciones en llamadas).
9. CONCIENCIA AMBIENTAL (el cerebro percibe el PC y decide solo; proactivo).
10. Control VISIBLE de la pantalla (`controlar_pantalla`: clic/teclado/ventanas).
11. Pruebas de ruteo del LLM (verificación de que entiende las órdenes).

---

## 1. Filtro anti-alucinaciones de Whisper (Bug A7)

**Síntoma real:** sin que Marco dijera nada, AIDEN "oía" frases y actuaba (p. ej. se puso a buscar
en Google *"Subtítulos por la comunidad de Amara.org"*; también salía *"¡Suscríbete!"*).

**Causa raíz:** Whisper se entrenó con millones de subtítulos de YouTube. Ante **silencio o ruido**
(casi-silencio, no audio vacío) "rellena" con esas frases fantasma en vez de devolver vacío. El
cerebro las tomaba como comandos.

**Arreglo (defensa en capas), en `Voz_Slide/Transcriptor.py` + `Voz_Slide/VAD.py`:**
1. `vad_filter=True` + `condition_on_previous_text=False` + `no_speech_threshold=0.6` +
   `log_prob_threshold=-1.0` en las dos llamadas a `transcribe` (el Silero VAD interno de
   faster-whisper descarta el audio sin voz ANTES de transcribir).
2. **Filtro por CONFIANZA del modelo** (`_texto_confiable`): por cada segmento, Whisper reporta su
   seguridad; se descarta el segmento si `no_speech_prob > 0.6` y `avg_logprob < -0.5` (silencio
   disfrazado), o `avg_logprob < -1.0` (confianza pésima), o `compression_ratio > 2.4` (texto en
   bucle tipo "gracias gracias gracias"). Umbrales conservadores para no cortar voz real.
3. **Lista negra** (`es_alucinacion`): ~35 frases/tokens fantasma (amara.org, subtitulamos.tv,
   "gracias por ver", "nos vemos en el próximo", equivalentes en inglés "thank you"/"you"/"thanks",
   "[Música]", "[Aplausos]", URLs…) + descarte de basura de 1-2 caracteres, **con lista blanca**
   (`_VALIDAS_CORTAS`: si/no/ya/ok/va) para no matar respuestas cortas legítimas. Log
   `🛇 Alucinacion descartada`.

**Lección transversal:** Whisper sobre silencio NO devuelve vacío: alucina frases de su
entrenamiento. Filtra con VAD antes de transcribir + ten una lista negra + filtra por confianza.

### Para la wiki
- Página de bug/lección: **"A7 — Whisper alucina sobre el silencio"** (enlazar a *capa de voz* y a
  *manos libres*, que amplifica el riesgo).
- Página de concepto: **"confianza de transcripción (no_speech_prob / avg_logprob / compression_ratio)"**.

---

## 2. Modo manos libres (sesión de mic abierto)

**Qué es:** una SESIÓN en la que hablas sin clic ni palabra clave y AIDEN responde turno tras turno.
Se activa y desactiva por voz (NO es un "siempre encendido"), para no responderle a la tele todo el día.

**Cómo se usa:**
- Entrar: "modo manos libres" / "escúchame" / "modo conversación".
- Salir: "descansa" (sale y oculta) / "modo normal" / "deja de escuchar".
- Auto-salida por silencio: tras ~5 min sin hablar (`MAX_SILENCIOS_MANOS_LIBRES=15` turnos ×
  `ESPERA_MANOS_LIBRES=20s`) sale solo y avisa.

**Dónde vive:** globales `_manos_libres` y `_silencios_manos_libres` en `Main.py` y
`Main_AlwaysOn.py`; la lógica está en el bucle de seguimiento de `Procesar_Peticion` (un `while`
interno que escucha y NO re-procesa el comando viejo). Atajos SIN LLM (coste $0).

**Decisión (Marco eligió esto sobre 3 opciones):** sesión acotada + auto-salida, NO mic permanente.
Tradeoff aceptado: mientras está activo, si la tele/otra persona habla con voz clara, AIDEN puede
contestar. El filtro anti-alucinaciones (§1) amortigua el ruido de fondo.

### Para la wiki
- Página de concepto: **"Control por voz / experiencia Jarvis"** (junto con §3).
- Página de decisión: **"manos libres como sesión, no como mic permanente"** (las 3 opciones
  evaluadas: sesión / solo-alargar-seguimiento / siempre-encendido-con-filtro).

---

## 3. Comandos de voz de ventana ampliados (descansa / quédate)

Antes los comandos eran demasiado restrictivos (exigían frases exactas como "ya descansa"). Ahora
usan **raíces sueltas**: `"descansa"` ya engancha *descansa / descansar / ya descansa / puedes
descansar / ve a descansar*. Atajos SIN LLM en `Procesar_Peticion`.

- **Esconder/descansar:** descansa, descansar, ocúltate, escóndete, duerme, a dormir, puedes irte,
  retírate → oculta la ventana y vuelve a REPOSO.
- **Quedarse:** quédate, mantente, no te ocultes, no te vayas, no te escondas → la fija.
- Interfaz (`Interfaz_En_Python.py`): timeout de inactividad subió de 60s a 120s; señales Qt
  thread-safe `pedir_fijar(bool)` y `pedir_ocultar`.

### Para la wiki
- Actualizar la página de concepto "Control por voz" con la tabla de comandos y el truco de raíces.

---

## 4. Vigilante de llamadas entrantes (auto-contesta como contestadora)

**Comportamiento de fondo** (como Presencia/Anticipación), en `Funciones_Slide/Comunicacion/Vigilante_Llamadas.py`.
Arranca tras el login (hilo daemon).

**Descubrimiento clave (probado en vivo):** WhatsApp **NO genera un toast de Windows** para las
llamadas → abre una VENTANA propia titulada **"Voice call" / "Video call"**. Por eso NO se detecta
por la base de notificaciones (`wpndatabase.db`), sino vigilando las VENTANAS.

**Cómo funciona:**
- Cada 2s enumera ventanas (`win32gui`); si aparece una con título de llamada, identifica la app por
  su proceso (`psutil`: WhatsApp.exe → WhatsApp, Discord.exe → Discord, etc.) y AVISA por voz.
- Si no reaccionas en `GRACIA=10s`, ATIENDE como contestadora con **UI Automation** (`uiautomation`,
  dependencia NUEVA; WhatsApp es WinUI/XAML y win32 puro no llega): pulsa **"Accept"** (patrón
  Invoke), dice un mensaje fijo al contacto por el cable **VB-CABLE**, y **cuelga** ("End call").
- Si TÚ la tomas/rechazas en esos 10s, el botón Accept ya no está → AIDEN **no interviene** (no habla
  encima de tu llamada).
- Mensaje personalizable: `MENSAJE_LLAMADA_AUSENTE` en `secretos.py` (hay uno por defecto).
- Manual: atajo SIN LLM **"contesta y dile X"** en `Procesar_Peticion` (gated en que haya una
  llamada sonando); extrae el mensaje tras "dile/diciendo/di que…".
- Se PAUSA en modo gaming.

**Cambio en la tool `contestar_llamada`** (`Comunicacion/Llamadas.py`): antes solo HABLABA por el
cable; ahora **ACEPTA + habla + CUELGA**, con guardia anti-intromisión. Schema y `PROTOCOLO DE
LLAMADAS` del prompt actualizados (ya NO pregunta "a quién"; él mismo acepta la llamada que suena).

**Diseño anti-molestia:** solo ventanas de llamada (por título), dedup por hwnd, cooldown por app,
no interviene si tú la tomas, pausa en gaming.

**Scripts de diagnóstico** (`Pruebas/`): `ver_notificaciones.py` (confirmó que el toast viene vacío),
`ver_ventanas.py` (descubrió el título "Voice call"), `probar_llamada.py` (prueba aislada: detecta +
lista botones + intenta aceptar).

**Pendiente real:** probar en vivo que el botón "Accept"/"End call" se pulse en el WhatsApp de Marco;
si el nombre difiere por idioma, ajustar `_BOTONES_ACEPTAR` / `_BOTONES_COLGAR`.

### Para la wiki
- Página de entidad: **`Vigilante_Llamadas.py`** (comportamiento de fondo); enlazar a *Presencia*,
  *contestar_llamada*, *VB-CABLE*.
- Página de decisión: **"detección por VENTANA, no por toast"** (WhatsApp no emite toast de llamada).
- Actualizar la página de la tool *contestar_llamada*: ahora acepta + habla + cuelga.

---

## 5. Escalado automático Flash → Pro (fallback de inteligencia)

**Idea (de Marco):** que el CÓDIGO (no Flash) escale a un modelo más potente cuando Flash flaquea.
Distinto de `consultar_experto` (que lo decide Flash como herramienta); aquí lo fuerza el código.

**Implementación en `Nucleo_Slide/Cerebro.py`:**
- `_escalar_a_pro(consulta, contexto)`: manda TODO el historial a **Pro (gemini-2.5-pro)** en un
  disparo y devuelve la respuesta final. Reusa el cliente OpenRouter; modelo de `Experto.MODELO_EXPERTO`.
- Antes de escalar, por voz dice: *"Un segundo, señor, estoy consultando un análisis más profundo"*.
- Flags: `ESCALADO_AUTO` y `AUTOEVALUACION` (apagables).

**4 disparadores:**
1. **Una herramienta FALLA** (excepción) → `_es_error_tool` lo detecta y escala.
2. **MALFORMED** tras los reintentos → escala en vez del mensaje genérico.
3. **Titubeo** → `_respuesta_insegura` (lista curada: "no estoy seguro", "no tengo información"…,
   evitando falsos positivos como "no se preocupe").
4. **Autoevaluación** → `_flash_inseguro`: Flash se autocalifica 1-5; ≤2 escala.

**Restricción de STREAMING (decisión clave):** la voz habla mientras genera (frase por frase). Por eso:
| Disparador | Voz (streaming) | Telegram (texto) |
|---|---|---|
| Error de herramienta | sí (antes de hablar la respuesta) | sí |
| MALFORMED | sí (antes de hablar) | sí |
| Titubeo | sí (como CONTINUACIÓN: "…un segundo, lo confirmo a fondo. [Pro]") | sí |
| Autoevaluación | NO (la respuesta ya se habló + 1 llamada extra por turno mata la fluidez) | sí |

O sea: en VOZ se usan error + MALFORMED + titubeo; la **autoevaluación completa corre en Telegram**
(no hay streaming, es limpia). Costo/latencia extra solo cuando Flash flaquea.

### Para la wiki
- Página de concepto: **"escalado de inteligencia Flash → Pro"** (enlazar con *modelo de dos
  niveles* y con *consultar_experto*: uno lo decide el LLM, el otro lo fuerza el código).
- Página de decisión: **"por qué la autoevaluación va en Telegram y no en voz (streaming)"**.

---

## 6. Centinela de pantalla (Jarvis reactivo: salta cuando algo se rompe)

**Comportamiento de fondo** en `Funciones_Slide/Sistema/Vigilante_Pantalla.py`. Arranca tras el
login (hilo daemon). MONITOREA las ventanas y AVISA solo ante eventos reales. Cero costo de API
(detecta por título/clase de ventana con `win32gui`).

**Dispara con:**
- App **CONGELADA**: Windows añade "(No responde)" / "(Not Responding)" al título → ofrece cerrarla.
- **ERROR/crash** en pantalla: título con pistas ("ha dejado de funcionar", "Application Error",
  "stopped working", "runtime error", "unhandled exception", "crash"…) → ofrece revisarlo.

**Anti-molestia:** solo eventos reales (no uso normal), dedup por ventana + cooldown 120s, se pausa
en gaming, NO cierra nada por su cuenta (Marco decide: "cierra X" → `cerrar_aplicacion`).

**Toque de VISIÓN opcional** (`LEER_PANTALLA=True`, apagado por defecto): al detectar un error usa
`analizar_pantalla` (visión) para decir QUÉ error es, no solo que hay uno. Cuesta una llamada de visión.

Parte de la línea "Jarvis reactivo": AIDEN nota el problema antes de que Marco lo reporte. Hermano
del *Vigilante de llamadas* (§4): ambos son monitores de ventanas de fondo.

### Para la wiki
- Página de entidad: **`Vigilante_Pantalla.py`** (comportamiento de fondo); enlazar a *Vigilante de
  llamadas* (mismo patrón de monitoreo de ventanas) y a *analizar_pantalla*.
- Página de concepto: **"Jarvis reactivo / monitoreo proactivo"** (familia: presencia, anticipación,
  vigilante de llamadas, centinela de pantalla).

---

## 7. Portapapeles inteligente (Jarvis reactivo: reacciona a lo que copias)

**Comportamiento de fondo** en `Funciones_Slide/Sistema/Vigilante_Portapapeles.py`. Vigila el
portapapeles (`pyperclip`) cada 2s y, ante un patrón INEQUÍVOCO, OFRECE ayuda por voz:
- **Error/traceback** copiado → *"Veo que copió un error, ¿se lo explico?"* (Marco: "sí" → `explicar_error`).
- **Link de YouTube** → *"¿Le resumo ese video?"* (→ `resumir`).

**Anti-molestia:** heurística ESTRICTA (`_es_error` exige traceback o error+multilínea+pistas de
código; el texto normal se ignora), dedup del mismo contenido, cooldown 60s, ignora lo que ya estaba
copiado al arrancar, se pausa en gaming. Solo OFRECE (no actúa).

### Para la wiki
- Página de entidad: **`Vigilante_Portapapeles.py`**; enlazar a *explicar_error*, *resumir*.

---

## 8. Modo reunión automático (Jarvis reactivo: silencia distracciones en llamadas)

**Comportamiento de fondo** en `Funciones_Slide/Sistema/Vigilante_Reunion.py`. Detecta que estás en
una reunión/llamada por una señal FIABLE y agnóstica de app: **qué apps usan el MICRÓFONO ahora**
(registro de Windows, `CapabilityAccessManager\ConsentStore\microphone`, `LastUsedTimeStop==0`).
Funciona con Zoom/Teams/Meet(navegador)/Discord. Excluye a AIDEN/python (su wake-word tiene el mic
siempre abierto).

**Al entrar a la reunión:** pausa la música (`control_musica`), silencia las notificaciones de
Windows (`Modos._notificaciones_windows`) y **calla los avisos proactivos** (anticipación, presencia,
alertas, vigilante de llamadas/pantalla/portapapeles) para no hablar encima. Un solo aviso corto.
**Al terminar:** restaura todo. Se pausa en gaming.

### Para la wiki
- Página de entidad: **`Vigilante_Reunion.py`**; enlazar a *modo gaming* (comparte el silenciar
  notis) y a la familia *Jarvis reactivo*.
- Página de concepto: **"detección de reunión por micrófono en uso"** (señal agnóstica de app).

---

## 9. CONCIENCIA AMBIENTAL (la pieza central: el cerebro decide, no reglas)

**Idea de Marco:** que AIDEN reciba CONTEXTO de la PC todo el tiempo y, en base a eso, ÉL decida qué
hacer — un Jarvis que percibe y actúa, no vigilantes con reglas fijas.

**Módulo:** `Nucleo_Slide/Conciencia_Ambiental.py`. Bucle de fondo de **percepción → decisión →
acción**. Es **PROACTIVO por contexto**: mira barato cada `CHEQUEO=60s` y "piensa" (gasta LLM) cuando
el contexto CAMBIA (cambiaste de app/ventana, vía `_firma_contexto`) o cuando pasó `INTERVALO_MAX=12min`,
con topes anti-spam: `MIN_ENTRE_PENSAMIENTOS=3min` entre pensamientos y `MAX_POR_HORA=10`. Cada ciclo:
1. **Percepción** — `_foto_del_pc()` arma una foto en TEXTO (barata, sin visión): fecha/hora,
   ventana activa, ventanas abiertas, estado del sistema (`estado_sistema`), notificaciones de la
   última hora, inicio del portapapeles, y si estás en reunión.
2. **Decisión** — pasa la foto a Flash con un prompt que exige RESTRICCIÓN: "por defecto NADA; actúa
   solo si hay algo claramente útil y no molesto; no te repitas; si no, responde NADA". Recibe las
   últimas 6 cosas que hizo (deque `_recientes`) para no repetirse.
3. **Acción** — es **autónomo**: puede ejecutar herramientas. Si responde "NADA" o vacío, se calla.

**Autonomía (Marco eligió "totalmente autónomo") con barandas:** tiene PROHIBIDAS 14 herramientas
irreversibles/externas (`_PROHIBIDAS`: Enviar_mensaje_Whatsapp, llamada_whatsapp, contestar_llamada,
controlar_energia, cerrar_aplicacion, Salir, Auto_Modificacion, crear/ejecutar_proyecto, dictar,
control_ventana, Abrir_Videos_Youtube, modo_gaming, colgar). Quedan 31 tools seguras/reversibles
(avisar, notas, recordatorios, volumen/música, clima, noticias, búsqueda, protocolos, finanzas…).

**Anti-molestia / costo:** PROACTIVO por contexto pero con topes — `MIN_ENTRE_PENSAMIENTOS=3min`,
`MAX_POR_HORA=10`, prompt "default NADA", no se repite, se PAUSA en gaming y reuniones.

**AUTO-MEJORA (Jarvis, segura):** el prompt incluye una regla de auto-mejora — si AIDEN nota que le
FALTA una capacidad o que algo se repite, lo PROPONE por voz ("podría crear una habilidad para X,
¿la construyo?") y puede anotarlo con `tomar_nota`. NUNCA se auto-modifica solo: `Auto_Modificacion`
está en la denylist autónoma; la construcción real solo ocurre cuando Marco la aprueba (bajo orden).
Decisión: self-modification autónoma sin supervisión = riesgo de auto-romperse; por eso es propose-then-confirm.

**Relación con los vigilantes (§4, §6, §7, §8):** los vigilantes siguen manejando EVENTOS
instantáneos (una llamada que suena, una app que se congela); la Conciencia hace el RAZONAMIENTO
holístico y periódico sobre el estado global. Coexisten: eventos en tiempo real + reflexión de fondo.

**Import circular evitado:** `configuracion → Modos → Conciencia → configuracion` se rompió haciendo
PEREZOSOS (dentro de funciones) los imports de `configuracion`/`Cerebro`/`Herramientas` en Conciencia.

**Pendiente:** probar EN VIVO la calidad de las decisiones (que sea útil y no cansón); calibrar
`INTERVALO`, el prompt de restricción y `_PROHIBIDAS` según cómo se comporte.

### Para la wiki
- Página de entidad: **`Conciencia_Ambiental.py`** (bucle percepción→decisión→acción).
- Página de concepto: **"Jarvis reactivo vs proactivo"** — vigilantes (eventos/reglas) vs conciencia
  (razonamiento del LLM sobre el contexto). Enlazar con *modelo de dos niveles* y *escalado a Pro*.
- Página de decisión: **"autonomía con denylist"** (por qué hay acciones prohibidas aunque sea autónomo).

---

## 10. Control VISIBLE de la pantalla (AIDEN se mete con la PC y lo ves)

**Tool nueva** `controlar_pantalla(accion, objetivo)` en `Funciones_Slide/Sistema/Control_Pantalla.py`
(tools 45 → 46). Marco quería VER a AIDEN interactuando con la PC, no solo oírlo. Acciones:
- **clic**: encuentra un botón/elemento por su NOMBRE con UI Automation (`uiautomation`), MUEVE el
  mouse hasta él con `pyautogui` (despacio, `duration=0.6`, para que el movimiento se NOTE) y hace clic.
- **ordenar**: acomoda hasta 4 ventanas de app en mosaico (`win32gui.MoveWindow`); se ven reacomodarse.
- **enfocar**: trae una app al frente por su nombre (`SetForegroundWindow`).
- **escribir**: teclea un texto visiblemente donde esté el cursor (`pyautogui.typewrite`).
- **scroll**: desplaza arriba/abajo (`pyautogui.scroll`).
- **doble_clic / clic_derecho**: variantes del clic sobre un elemento por su nombre.
- **cerrar_pestana** (Ctrl+W), **seleccionar** (Ctrl+A), **atajo** (combo de teclas, ej. "control + s").

**Anti-confusión (descripción afinada):** `controlar_pantalla` es para INTERACCIÓN VISIBLE con lo que YA
está en pantalla (mouse/teclado sobre elementos). NO confundir con: `Abrir_Apps` (abrir app nueva),
`control_ventana` (minimizar/maximizar/cerrar la VENTANA entera), `dictar` (pegar texto largo de
golpe), `analizar_pantalla` (leer/ver la pantalla con visión). La descripción de la tool lista
explícitamente estos "NO uses esto para…".

Disparada por voz ("dale clic a Guardar", "ordena mis ventanas", "trae Chrome al frente",
"escribe …", "baja", "cierra la pestaña", "presiona control + s"). 
**Seguridad:** está en la denylist de la Conciencia Ambiental (no mueve el mouse de forma autónoma;
solo bajo orden de Marco). Fiable porque localiza elementos por UI Automation, no por coordenadas a ciegas.

**Pendiente (siguiente capa de "interactivo", trabajo de GUI en Qt):** (a) OVERLAY siempre visible
que muestre en vivo lo que AIDEN ve/piensa; (b) CO-PILOTO que reaccione en pantalla al instante
(al cambiar de app), no cada 12 min. Ambos tocan `Interfaz/Interfaz_En_Python.py` y conviene
probarlos en vivo.

### Para la wiki
- Página de entidad: **`Control_Pantalla.py`** / tool `controlar_pantalla`; enlazar a *Conciencia
  Ambiental* (denylist) y a *computer-use / UI Automation*.

---

## 11. Pruebas de ruteo del LLM (¿entiende bien las órdenes?)

Se verificó que el cerebro (Flash) elige la HERRAMIENTA y los ARGUMENTOS correctos para cada orden,
con un banco de 20 órdenes representativas (incluyendo las propensas a confusión).

- **1ª pasada (temp 0, 1 vez):** 16/20. Reveló 2 bugs reales: el modelo escribía mal `interactuar_pc`
  → `interactar_pc` (habría fallado en runtime), y "cierra la pestaña" se iba a `control_ventana`.
- **Arreglos:** (a) RENOMBRAR la tool `interactuar_pc` → **`controlar_pantalla`** (la familia
  `control_*` el modelo la escribe siempre bien; "interactuar" se le trababa). (b) Afinar la
  descripción de `control_ventana` ("para una PESTAÑA usa controlar_pantalla").
- **2ª pasada (temp 0.7 = la REAL, 3 repeticiones por orden = 60 llamadas):** **60/60 (100%)**,
  20/20 casos 100% consistentes, **0 nombres de tool alucinados**.

**Lección (para la wiki):** el nombre de una herramienta importa para la fiabilidad — nombres largos
o poco comunes (ej. "interactuar") el LLM los escribe mal y la llamada falla. Preferir nombres de la
familia existente (`control_*`). Y SIEMPRE probar el ruteo a la temperatura REAL y con repeticiones,
no a temp 0 una sola vez (eso solo mide el caso determinista, no la consistencia).

### Para la wiki
- Página de decisión/lección: **"nombrar herramientas para que el LLM no las escriba mal"**.
- Página de método: **"cómo probar el ruteo de function-calling"** (temp real + repeticiones + detectar
  nombres alucinados).

---

## Resumen para el índice del segundo cerebro
- Voz más robusta: ya no actúa sobre alucinaciones de Whisper (§1).
- Voz más cómoda: modo manos libres + comandos naturales (§2, §3).
- Proactividad: avisa/contesta llamadas (§4), centinela de pantalla (§6), portapapeles (§7), modo
  reunión (§8) y la **conciencia ambiental** que percibe el PC y decide sola (§9, proactiva + auto-mejora).
- Inteligencia con red de seguridad: escala a Pro cuando Flash flaquea (§5).
- Interacción VISIBLE: `controlar_pantalla` mueve mouse/teclado y ordena ventanas (§10).
- Ruteo del LLM verificado: 60/60 a temperatura real (§11).
- Dependencia nueva: `uiautomation`. Verificado por compilación + lógica + ruteo del LLM; falta prueba
  EN VIVO de los botones de llamada y de que el clic caiga en el elemento correcto en cada app.
