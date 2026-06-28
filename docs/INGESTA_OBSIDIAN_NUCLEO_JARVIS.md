# AIDEN — El NÚCLEO JARVIS (FUENTE para ingesta en el segundo cerebro)

> **Para el Claude Code de Obsidian (ingesta):** documento-FUENTE autocontenido con el salto más
> importante de AIDEN: pasar de "muchos scripts reactivos sueltos" a **una mente continua con
> propósito**. Procésalo como las otras fuentes: crea/actualiza páginas de ENTIDAD (módulos), de
> CONCEPTO y de DECISIÓN, y enlázalas con [[wikilinks]]. Al final de cada sección dejo sugerencias
> "Para la wiki". Estado: junio 2026, 47 herramientas. Complementa (y va DESPUÉS de) la fuente
> *Voz/Llamadas/Escalado*. Enlaza con *Arquitectura*, *Decisiones*, *AIDEN Constructor*.

## El porqué (la idea madre)
Marco sentía que AIDEN, pese a tener muchas funciones, seguía lejos de Jarvis. Razonándolo, la
brecha NO eran más features, sino tres cosas de fondo:
1. **Una sola mente** (las partes no compartían estado).
2. **Que lo MODELE** (guardaba datos, no aprendía quién es).
3. **Propósito / agencia** (reaccionaba al presente, no perseguía nada en el tiempo).
El "Núcleo Jarvis" ataca exactamente eso. Frase guía: *"Jarvis = una mente continua, que te conoce,
con propósito, que habla con intención."*

Cubre 6 piezas:
1. Conciencia compartida (la mente única).
2. Metas (objetivos que sostiene).
3. Seguimiento activo de metas (los persigue).
4. Perfil que aprende (te conoce).
5. Vocero (habla con intención, no de más).
6. Integración + pruebas.

---

## 1. Conciencia compartida — `Nucleo_Slide/Estado_Del_Mundo.py`

**Qué es:** el "estado del mundo", una SOLA mente que TODAS las partes de AIDEN leen y escriben.
Convierte scripts sueltos en un agente con CONTINUIDAD: sabe qué pasa ahora, qué pasó hace un rato,
en qué anda Marco y qué metas tiene.

- Módulo **HOJA** (solo stdlib) → cualquiera lo importa sin ciclos. Persiste en `estado_del_mundo.json`
  (GITIGNORED, privado). Thread-safe (RLock).
- Campos: `foco_actual`, `marco_presente`, `en_reunion`, `modo` (normal/gaming/…), `eventos`
  (hilo rolling de 40), `metas`.
- API: `actualizar(**campos)`, `registrar_evento(texto, origen)`, `marcar_interaccion()`,
  `resumen_texto()` (lo que ve toda la mente), y la API de metas (§2).
- **Quién lo ALIMENTA:** el cerebro de voz (cada turno), la conciencia ambiental, los vigilantes
  (llamadas, pantalla, portapapeles, reunión), la presencia (`marco_presente`) y el modo gaming.
- **Quién lo LEE:** el cerebro de voz inyecta "CONTEXTO ACTUAL" en su prompt (`_instrucciones_completas`);
  la conciencia razona sobre el cuadro completo.

### Para la wiki
- Página de entidad: **`Estado_Del_Mundo.py`** (la "mente compartida"); enlazar a TODOS los que la
  alimentan/leen.
- Página de concepto: **"una sola mente vs scripts sueltos"** (la idea madre del núcleo).

---

## 2. Metas — `Funciones_Slide/Productividad/Metas.py` + tool `gestionar_metas`

Objetivos de ALTO NIVEL que AIDEN acompaña en el tiempo (NO tareas con hora = `guardar_en_json`, NI
notas sueltas = `tomar_nota`). Viven en la conciencia compartida, así la conciencia los ve en cada
decisión. Tool #47 `gestionar_metas(accion, meta, nota)`:
- `agregar` ("mi meta es X"), `avance` ("avancé en X" → registra progreso, meta=cuál, nota=qué),
  `cerrar` ("ya cumplí X"), `listar` ("¿cuáles son mis metas?").

### Para la wiki
- Página de entidad: tool **`gestionar_metas`** / `Metas.py`; enlazar a *Estado_Del_Mundo* y
  *seguimiento de metas*. Diferenciar de `guardar_en_json` y `tomar_nota`.

---

## 3. Seguimiento ACTIVO de metas — `Funciones_Slide/Productividad/Seguimiento_Metas.py`

El "te acompaña" de Jarvis: AIDEN no solo recuerda las metas, las PERSIGUE. Comportamiento de fondo.
- **1 vez al día máximo** (en total), cada meta máx ~1 vez/22h, solo en franja 10-21h; se calla si
  Marco está en reunión/gaming/ausente (lo chequea vía `Estado_Del_Mundo`).
- Elige la meta más "olvidada" (`meta_para_seguimiento`) y, con el LLM (meta + avances + perfil),
  redacta UN mensaje útil: check-in / siguiente paso / empujón.
- Probado en vivo (LLM): generó *"¡excelente avance con el capítulo 2! ¿Y si usas Python para
  analizar datos de cripto en tu tesis?"* — conectó meta + perfil.

### Para la wiki
- Página de entidad: **`Seguimiento_Metas.py`**; enlazar a *metas*, *perfil*, *Vocero*, *anti-molestia*.
- Página de decisión: **"de memoria de metas a agencia sobre metas"** (recordar vs perseguir).

---

## 4. Perfil que aprende — `Nucleo_Slide/Perfil_Marco.py`

AIDEN APRENDE quién es Marco destilándolo de la memoria episódica, y lo usa en cada decisión.
- Capa **barata** (siempre): temas por frecuencia de palabras clave.
- Capa **inteligente** (auto-regulada, cada 6h / 12 episodios nuevos): el LLM (flash) redacta un
  perfil conciso en viñetas (intereses, rutinas, proyectos, forma de hablar). Limpiador
  `_solo_vinetas` quita preámbulos.
- `perfil_texto()` se inyecta en el cerebro de voz Y en la conciencia. `iniciar_perfil()` hilo de
  fondo. `perfil_marco.json` GITIGNORED.
- Probado: destiló un perfil real ("interesado en Bitcoin; desarrolla AIDEN en Python; sigue al Real
  Madrid; tiene una tesis en curso").

### Para la wiki
- Página de entidad: **`Perfil_Marco.py`**; enlazar a *memoria episódica*, *las tres memorias*.
- Página de concepto: **"guardar datos vs modelar a la persona"**.

---

## 5. Vocero — `Nucleo_Slide/Vocero.py` (habla con INTENCIÓN, no de más)

Al sumar tantas voces de fondo (conciencia, metas, presencia, vigilantes), el riesgo era que AIDEN
se volviera un loro. El Vocero es el punto ÚNICO por el que pasa TODA la voz proactiva:
- **Presupuesto global**: máx `MAX_POR_HORA=5`/hora, `GAP_MINIMO=90s` entre dos.
- **Dedup** (no repite), y se **calla** si reunión/gaming/ausente (lee `Estado_Del_Mundo`).
- **Urgencias** (`prioridad='alta'`, p.ej. llamada entrante) saltan el límite.
- Lo silenciado queda en el hilo de conciencia ("(callado para no molestar) …").
- `emitir(hablar, texto, origen, prioridad)`. Las RESPUESTAS directas a Marco NO pasan por aquí
  (esas siempre se dicen); el Vocero es solo para lo proactivo/no solicitado.
- Probado 7/7 (gap, tope/hora, dedup, silencio por estado, urgencia pasa).

### Para la wiki
- Página de entidad: **`Vocero.py`**; enlazar a TODOS los emisores proactivos.
- Página de concepto/decisión: **"voz proactiva con presupuesto global (anti-loro)"** — el valor
  anti-molestia llevado a su forma final.

---

## 6. Integración y pruebas

**Cómo se conecta todo (el flujo de una mente):**
- `Cerebro._instrucciones_completas` inyecta, además del prompt base + memoria + episódica:
  **CONTEXTO ACTUAL** (Estado_Del_Mundo) + **LO QUE HAS APRENDIDO DE MARCO** (perfil).
- `proceso_de_ia`/`procesar_remoto` registran cada turno como evento + `marcar_interaccion`.
- Vigilantes/presencia/modo escriben eventos y estado; la conciencia lee todo y, al decidir, emite
  por el Vocero; el seguimiento de metas también.
- Import circular evitado: `Estado_Del_Mundo` es HOJA; `Conciencia`/`Perfil`/`Vocero` hacen imports
  PEREZOSOS de `Cerebro`/`configuracion`.

**Pruebas de fuego (con el LLM real):**
- Núcleo end-to-end **19/19**: el cerebro, SIN que se lo cuenten, supo la app activa, quién llamó y
  la meta activa; el ruteo de `gestionar_metas` acertó 4/4; el perfil se destiló bien; el seguimiento
  generó un mensaje útil y personalizado.
- Vocero **7/7**.

**Pendiente (honesto):** probar EN VIVO (hilos de fondo disparándose solos: cámara/mic/GUI);
que las metas tengan seguimiento de avance más fino; **conocer la agenda de Marco** (calendario/
correo, necesita credenciales de Google); **cerrar el ciclo** (verificar que las acciones funcionaron).

### Para la wiki
- Página índice: **"Núcleo Jarvis"** que enlace las 6 piezas + la idea madre (§"El porqué").
- Página de decisión: **"qué falta para Jarvis"** (agenda + cerrar el ciclo + fiabilidad probada).

---

## Resumen para el índice del segundo cerebro
- AIDEN dejó de ser scripts reactivos: ahora tiene **una mente** (Estado_Del_Mundo) que **te conoce**
  (Perfil_Marco), **te acompaña** hacia tus metas (Metas + Seguimiento) y **habla con intención**
  (Vocero). Todo probado con el LLM real (19/19 + 7/7). Archivos nuevos GITIGNORED:
  estado_del_mundo.json, perfil_marco.json.
