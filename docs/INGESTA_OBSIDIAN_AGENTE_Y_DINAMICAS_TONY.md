# AIDEN — Implementos GRANDES + dinámicas Jarvis↔Tony (FUENTE para ingesta en el segundo cerebro)

> **Para el Claude Code de Obsidian (ingesta):** documento-FUENTE autocontenido. Va DESPUÉS de las
> fuentes *Núcleo Jarvis* y *Presencia Continua*. Procésalo igual: crea/actualiza páginas de ENTIDAD
> (módulos/tools), de CONCEPTO y de DECISIÓN, y enlázalas con [[wikilinks]]. "Para la wiki" al final de
> cada sección. Estado: junio 2026, 50 herramientas. Enlaza con *Núcleo Jarvis*, *Presencia Continua*,
> *AIDEN Constructor*.

## El porqué
Tras el núcleo (mente) y la presencia continua (feel), Marco pidió DOS cosas: (A) **implementos
GRANDES**, no arreglos pequeños; y (B) mejoras al estilo de **cómo Jarvis interactuaba con Tony Stark**.
Resultado: AIDEN ahora se VE en pantalla, HACE cosas y se asegura de que funcionen, recuerda por
significado, y se mete en tu trabajo/vida como un verdadero Jarvis.

Cubre 7 cambios, en 2 partes:
- PARTE A — Implementos grandes: 1) Overlay de presencia, 2) Misiones autónomas, 3) Memoria RAG.
- PARTE B — Dinámicas Jarvis-Tony: 4) Co-ingeniero, 5) Consejero leal, 6) "Me tomé la libertad de…",
  7) Investiga y reporta.

Todo lo PROACTIVO pasa por el **Vocero** (presupuesto global anti-loro; ver *Núcleo Jarvis §5*) y se
calla en reunión/gaming/ausente.

---

# PARTE A — Implementos grandes

## 1. Overlay de Presencia — `Interfaz/Overlay.py`
Hace VISIBLE el núcleo (resolvía la queja "no se nota en pantalla"). Ventana PySide6 (tkinter está
prohibido) siempre-encima, semi-transparente y CLICK-THROUGH (`Qt.WindowTransparentForInput`, no roba
el mouse), en una esquina. Muestra EN VIVO (refresco 3s): foco actual, estado de Marco, metas activas,
últimos eventos y la reflexión del momento — leyendo `Estado_Del_Mundo` + `Reflexion`. `crear_overlay()`
se llama DENTRO del hilo Qt en `Main_AlwaysOn.py` (tras crear la QApplication), guardado para no romper
la app. (No está en Main.py porque ahí Qt vive dentro de ejecutar_slide.)

### Para la wiki
- Página de entidad **`Overlay.py`**; enlazar a *Estado_Del_Mundo*, *Reflexion*, *SlideHUD*.
- Página de decisión: **"hacer visible el núcleo (overlay click-through)"**.

## 2. Misiones autónomas — `Funciones_Slide/Sistema/Misiones.py` + tool `ejecutar_mision` (#48)
El "Jarvis que HACE y se asegura de que funcione". Ciclo de agente: CONSTRUYE (Claude Code headless,
sandbox) → VERIFICA ejecutándolo → si falla, le pasa el error a Claude Code para CORREGIR (1 reintento)
→ re-verifica → REPORTA por voz; deja eventos en la conciencia (visibles en el overlay). El **verify→fix
loop** es la mejora clave sobre `crear_proyecto` (que solo construye). Segundo plano. Prohibida en la
conciencia autónoma (solo bajo orden). Reusa `_CLAUDE`/`_carpeta_proyecto`/timeouts de *Programador.py*.

### Para la wiki
- Página de entidad: tool **`ejecutar_mision`** / `Misiones.py`; enlazar a *AIDEN Constructor* /
  *crear_proyecto* (diferencia: misión VERIFICA y autocorrige).
- Página de decisión: **"verify→fix loop: agencia confiable"**.

## 3. Memoria RAG — `Nucleo_Slide/Memoria_RAG.py` + tool `recordar_a_fondo` (#49)
Búsqueda SEMÁNTICA (por significado, no palabras) sobre todo el historial. Embeddings con
`sentence-transformers` (modelo `paraphrase-multilingual-MiniLM-L12-v2`, en CPU para no pelear VRAM con
Whisper/Kokoro). `iniciar_rag()` indexa en 2do plano y re-indexa cada 30min; `buscar()` hace coseno.
`recordar_relevantes_semantico()` queda listo para, si se quiere, reemplazar la recall por palabra clave
en el prompt. DEP NUEVA: sentence-transformers (el modelo se baja 1 vez, ~120MB). Probado: "mi trabajo
de la universidad" encontró "la tesis" (0.53) SIN compartir palabras.

### Para la wiki
- Página de entidad: tool **`recordar_a_fondo`** / `Memoria_RAG.py`; enlazar a *memoria episódica*
  (diferencia: significado vs palabra clave) y *las tres memorias*.
- Página de concepto: **"búsqueda semántica (embeddings) vs por palabra clave"**.

---

# PARTE B — Dinámicas Jarvis↔Tony

## 4. Co-ingeniero — `Funciones_Slide/Sistema/Co_Ingeniero.py`
La escena del taller: Jarvis se metía a ayudar al VER a Tony peleando, sin que se lo pidiera. AIDEN
vigila la ventana activa; si llevas mucho rato (`UMBRAL_ATASCO`=12min) en la MISMA Y hay SEÑAL DE LUCHA
(un error de pantalla reciente en el hilo de conciencia, o frustración en lo último que dijiste vía
`Sintonia._FRUSTRACION`), te ofrece ayuda con una frase de taller (LLM), vía Vocero + cooldown. Clave
anti-molestia: leer/ver algo un buen rato NO dispara; hace falta evidencia de lucha.

### Para la wiki
- Página de entidad **`Co_Ingeniero.py`**; enlazar a *Vigilante_Pantalla* (errores), *Sintonia*
  (frustración), *Vocero*, *analizar_pantalla* (la ayuda al aceptar).
- Página de concepto: **"ayudar al ver la lucha, no al pedirlo (el taller)"**.

## 5. Consejero leal — sección en INSTRUCCIONES (`Nucleo_Slide/Cerebro.py`)
Jarvis no era un "sí, señor". AIDEN ahora tiene CRITERIO: discrepa con respeto ante imprudencias y
propone mejor, cuida el bienestar de Marco aunque no lo pida (sobre-exigencia, trasnochadas, metas
descuidadas) usando perfil+reflexión+estado, pero la decisión final es de Marco. Espina dorsal con
lealtad, no terquedad ni sermón. Es un cambio de PROMPT (sin infra nueva), pervasivo en toda interacción.

### Para la wiki
- Página de concepto/decisión: **"consejero leal: criterio, no complacencia"**; enlazar a *personalidad/
  humor* y a *perfil*/*reflexión* (de dónde saca el criterio).

## 6. "Me tomé la libertad de…" — `Funciones_Slide/Sistema/Preparacion.py`
Jarvis preparaba lo que Tony iba a necesitar. Al abrir una app de TRABAJO (`_APPS_TRABAJO`: Code/Word/
Obsidian/…) teniendo metas activas, el LLM JUZGA si alguna meta encaja con lo que vas a hacer; si sí,
te ofrece tener a mano tu contexto ("me tomé la libertad de repasar… quedó en…"); si NINGUNA encaja con
claridad, responde NADA y calla — así nunca fuerza una meta irrelevante (probado: Word+tesis→ofrece;
Photoshop+tesis→NADA). Vía Vocero + cooldown 3h.

### Para la wiki
- Página de entidad **`Preparacion.py`**; enlazar a *metas* y *Vocero*.
- Página de decisión: **"anticipar preparando, con el LLM juzgando relevancia (no forzar)"**.

## 7. Investiga y reporta — `Funciones_Slide/Info/Investigacion.py` + tool `investigar` (#50)
El "Señor, completé el análisis". Multi-paso: descompone el tema en sub-preguntas (flash) → busca cada
una (`buscar_en_internet`) → SINTETIZA un informe (Pro/gemini-2.5-pro) → lo reporta por voz y lo GUARDA
como nota (`tomar_nota`). Segundo plano. Distinta de `buscar_en_internet` (una búsqueda) y
`consultar_experto` (razona sin buscar). Prohibida en la conciencia autónoma.

### Para la wiki
- Página de entidad: tool **`investigar`** / `Investigacion.py`; enlazar a *buscar_en_internet*,
  *consultar_experto*, *modelo de dos niveles*.

---

## Resumen para el índice del segundo cerebro
Esta tanda hizo a AIDEN un agente Jarvis completo: se VE (overlay), HACE y verifica (misiones),
recuerda por significado (RAG), se mete a ayudarte al verte atascado (co-ingeniero), te aconseja con
criterio (consejero leal), se adelanta preparando tu contexto ("me tomé la libertad de…") e investiga
a fondo y te reporta. Todo lo proactivo coordinado por el Vocero (anti-loro) y silenciado en
reunión/gaming/ausente. 50 herramientas. DEP nueva: sentence-transformers. Probado por lógica/LLM;
falta probar EN VIVO (overlay renderizando, una misión real, los watchers de ventana disparándose).
Crear página índice **"AIDEN como agente Jarvis"** que enlace estas 7 + el núcleo + la presencia continua.
