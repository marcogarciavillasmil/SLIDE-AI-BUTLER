# AIDEN — PRESENCIA CONTINUA / el "feel" de compañero (FUENTE para ingesta en el segundo cerebro)

> **Para el Claude Code de Obsidian (ingesta):** documento-FUENTE autocontenido. Va DESPUÉS de la
> fuente *Núcleo Jarvis*. Procésalo igual: crea/actualiza páginas de ENTIDAD (módulos), de CONCEPTO
> y de DECISIÓN, y enlázalas con [[wikilinks]]. Al final de cada sección dejo "Para la wiki". Estado:
> junio 2026, 47 herramientas. Enlaza con *Núcleo Jarvis*, *Arquitectura*, *Decisiones*.

## El porqué (la idea madre)
Con el *Núcleo Jarvis* le dimos a AIDEN **continuidad COGNITIVA**: una mente que recuerda, te conoce y
persigue metas. Pero "saber" no es "acompañar". Marco pidió mejoras que NO agreguen habilidades, sino
que mejoren **cómo se SIENTE** — el salto de **mente continua → presencia continua** (relacional/
emocional). Un compañero no se define por lo que sabe, sino por **cómo te trata**. Frase guía:
*"que no solo sepa tu vida, sino que esté contigo en ella — con el tono justo, retomando el hilo,
habiéndote tenido presente."*

Cubre 6 piezas (+ el Vocero, ya documentado en *Núcleo Jarvis §5*):
1. Sintonía emocional (te habla según cómo estás).
2. Reanudación contextual (te recibe retomando el hilo).
3. "Estuve pendiente" (al volver, te trae lo que retuvo).
4. Variedad viva (nunca suena enlatado).
5. Despedida con sentido (te cierra el día reconociéndolo).
6. Reflexión (entiende tu MOMENTO, no solo tus datos) — la capa más profunda.

---

## 1. Sintonía emocional — `Nucleo_Slide/Sintonia.py`

El gemelo EMOCIONAL de la memoria continua: si la memoria hizo que AIDEN supiera *qué pasa*, la
sintonía hace que responda según *cómo estás*. `lectura_de_estado(consulta)` — heurística BARATA
(sin LLM, corre cada turno) — infiere el estado de Marco de señales que YA tenemos y devuelve una
guía de TONO que se inyecta en el prompt del cerebro (`_instrucciones_completas`). NO cambia QUÉ hace
AIDEN, solo CÓMO te habla.

Señales y prioridad: (a) **tus palabras ahora** (frustración / logro = lo más fuerte) → cálido y
directo / celebra; (b) **estado del mundo** (reunión = mínimo; gaming = relajado y breve; meta
recién cumplida = reconócelo); (c) **la hora** (madrugada = suave, breve, cuidarte). Si hay varias,
gana la emocional sobre la situacional sobre la horaria.

### Para la wiki
- Página de entidad: **`Sintonia.py`**; enlazar a *Estado_Del_Mundo*, *perfil*, *capa de voz*.
- Página de concepto: **"sintonía emocional: ajustar el tono, no el qué"** (el gemelo emocional de la
  memoria continua).

---

## 2. Reanudación contextual — `Nucleo_Slide/Compania.py` → `saludo_de_reanudacion()`

Un compañero no te saluda en frío: RETOMA el hilo. Reemplaza el "Bienvenido Marco" genérico (en
`Main.py` y `Main_AlwaysOn.py`) por un saludo cálido que continúa vuestra historia: usa la última
conversación (memoria episódica) + metas activas + cuánto tiempo pasó (traducido a "hace un rato" /
"desde ayer" / "hace N días"), y lo redacta el LLM en 1-2 frases naturales. Fallback robusto: si algo
falla, saluda normal — NUNCA rompe el arranque. Ejemplo real generado: *"¡Bienvenido de nuevo, señor!
Listo para retomar el capítulo 2, ¿o empezamos por otro lado hoy?"*.

### Para la wiki
- Página de entidad: **`Compania.py`** (re-entrada relacional); enlazar a *memoria episódica*, *metas*.
- Página de decisión: **"saludo que retoma el hilo, no en frío"**.

---

## 3. "Estuve pendiente" — `Nucleo_Slide/Compania.py` → `lo_que_retuve(desde_ts)`

Al VOLVER al PC tras una ausencia, AIDEN trae UNA cosa notable que pasó mientras no estabas — se
siente como una presencia que estuvo ahí por ti. Lee el **hilo de conciencia** (eventos de
`Estado_Del_Mundo`) desde que te fuiste y elige por prioridad: **llamadas > errores de pantalla > lo
que el Vocero/conciencia calló por no molestar**. Ignora la charla trivial (voz, presencia); devuelve
"" si nada amerita. Se engancha al **saludo de regreso de Presencia** (que calcula `_inicio_ausencia`
cuando detecta que volviste tras una ausencia real). Trae SOLO una (más sería ruido). Frase tipo:
*"Por cierto, señor, mientras no estaba: llamada entrante por WhatsApp."*

### Para la wiki
- Misma entidad **`Compania.py`** (función `lo_que_retuve`); enlazar a *Vocero* (lo silenciado),
  *Presencia*, *Estado_Del_Mundo*.
- Página de concepto: **"estuve pendiente: traer lo que se retuvo en tu ausencia"**.

---

## 4. Variedad viva — `Nucleo_Slide/Cerebro.py` → `_confirmacion()`

Un compañero nunca repite la misma frase enlatada. Cuando el LLM ejecuta algo pero no escribe texto,
antes salía siempre "Hecho, señor." (robótico). Ahora `_confirmacion()` da una de 12 variantes
("Listo.", "De inmediato, señor.", "Resuelto, señor.", "Enseguida, señor."…). Además el system prompt
(sección EJECUCIÓN) pide confirmar **breve, natural y específico, refiriéndose a lo que hizo** ("listo,
Spotify arriba", "cerrada esa pestaña") y NUNCA repetir la misma frase — para que casi nunca caiga al
fallback. Detalle pequeño, gran impacto en sentirse vivo.

### Para la wiki
- Página de decisión: **"matar las confirmaciones enlatadas (variedad viva)"**; enlazar a *personalidad/humor*.

---

## 5. Despedida con sentido — `Nucleo_Slide/Compania.py` → `despedida_del_dia()`

La CONTRAPARTE de la reanudación: si AIDEN te recibe retomando el hilo, también te DESPIDE
reconociendo tu día. Cierra el arco del día (apertura ↔ cierre). Disparador: frases de fin de día
("buenas noches", "me voy a dormir", "hasta mañana"…) en `Procesar_Peticion` (en ambos Main), DISTINTO
del "descansa"/"ocúltate" que solo oculta la ventana. Usa los episodios de HOY + metas activas y el
LLM redacta 1-2 frases cálidas que reconocen algo concreto del día y desean descanso; además oculta la
ventana. Fallback robusto. Ejemplo real: *"Buenas noches, señor. Hoy avanzó un montón con la tesis,
especialmente con la introducción. Que descanse para seguir con ese capítulo 2."*

### Para la wiki
- Misma entidad **`Compania.py`** (función `despedida_del_dia`); enlazar a *reanudación* (su par) y
  a *metas* / *memoria episódica*.
- Página de concepto: **"el arco del día: apertura (reanudación) ↔ cierre (despedida)"**.

---

## 6. Reflexión — `Nucleo_Slide/Reflexion.py` (entiende tu MOMENTO)

La capa MÁS PROFUNDA de "te conoce", y la más Jarvis. Tres niveles de comprensión de Marco, juntos:
- **Sintonía** → cómo está AHORA MISMO (este turno) — momentáneo.
- **Perfil** → QUIÉN es (intereses, rutinas) — identidad estable.
- **Reflexión** → CÓMO está en su ARCO actual (su momento) — situación que evoluciona. ← esto.

`reflexionar()` corre en ratos tranquilos (auto-regulado: cada ~4h o cada 8 conversaciones nuevas) y,
con los episodios recientes + metas + la reflexión anterior, el LLM destila una LECTURA empática y
honesta de la situación de Marco: cómo ha estado de ánimo, dónde está atascado o en racha, qué le
vendría bien. NO son datos (eso es el perfil): es una *contemplación* de su momento. `reflexion_texto()`
se inyecta en CADA decisión del cerebro → feel pervasivo (que "piensa en ti"), no un momento suelto.
`iniciar_reflexion()` hilo de fondo en ambos Main. `reflexion.json` GITIGNORED.

Ejemplo real generado: *"Marco está en una montaña rusa con su tesis... terminó la introducción pero
se lanza al capítulo 2 con una presión que podría abrumarlo; quizás le vendría bien celebrar sus
logros y darse un respiro."*

### Para la wiki
- Página de entidad: **`Reflexion.py`**; enlazar a *Perfil_Marco* y *Sintonia* (las tres capas).
- Página de concepto clave: **"las tres capas de conocer a Marco: sintonía (ahora) / perfil (quién) /
  reflexión (su momento)"** — distinguir DATOS vs ENTENDIMIENTO.

---

## Resumen para el índice del segundo cerebro
AIDEN pasó de **mente continua** a **presencia continua**: te habla según tu estado (Sintonía),
te recibe retomando el hilo (Reanudación), te trae lo que retuvo en tu ausencia (Estuve pendiente)
y nunca suena enlatado (Variedad viva). Todo se apoya en el núcleo (Estado_Del_Mundo, perfil,
episódica) y respeta el anti-molestia (el Vocero coordina toda la voz proactiva). Probado con el LLM
real; falta probarlo EN VIVO (hilos de fondo con cámara/mic). Crear página índice **"Presencia
continua / feel Jarvis"** que enlace las 4 piezas + la idea madre.
