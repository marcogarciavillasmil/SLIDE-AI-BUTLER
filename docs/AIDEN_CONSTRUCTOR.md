# AIDEN — AIDEN Constructor y auto-modificación vía Claude Code (fuente para la wiki)

> Documento-fuente para el segundo cerebro. Describe el salto de "AIDEN escribe código a mano"
> a "AIDEN delega la escritura de código a Claude Code (headless) y luego ejecuta el resultado".
> Cubre las DOS rutas que usan este patrón: construir proyectos nuevos (sandbox) y auto-modificarse
> (repo real). Estado: junio 2026, 45 herramientas. Complementa *Arquitectura §2* (los dos cerebros)
> y *Herramientas §10* (catálogo).

---

## 1. El salto conceptual

**Antes** (`Auto_Modificacion` original): el LLM (gemini, el cerebro normal) generaba el
`codigo_python` él mismo, como texto dentro del JSON de function-calling, y ese texto se
appendeaba directo a `Nucleo_Slide/Auto_Programacion.py`. Frágil: un LLM de chat escribiendo
código Python completo dentro de un argumento JSON tropieza con escapes de `\n`, comillas y
errores de sintaxis silenciosos — el tipo de tarea para la que gemini-flash NO está optimizado.

**Ahora**: gemini ya NO escribe código. Solo describe **qué** quiere en lenguaje natural
(`instruccion`) y delega la escritura real a **Claude Code en modo headless**
(`claude -p "<prompt>" --permission-mode bypassPermissions`, vía `subprocess.run` con
argumentos en lista — nunca se concatena un string a un shell, así que no hay inyección de
comandos). Claude Code es quien de verdad sabe programar; gemini solo orquesta la petición y
relata el resultado.

Esta idea tiene DOS implementaciones según para qué se use el código generado:

```
gemini (cerebro)
   │  decide QUÉ construir, en lenguaje natural
   ▼
subprocess: claude -p "<instrucción>" --permission-mode bypassPermissions   (hilo daemon)
   │
   ├── crear_proyecto / ejecutar_proyecto  →  SANDBOX (~/Desktop/Proyectos_AIDEN/<slug>)
   │                                          un proyecto/app NUEVO y separado
   │
   └── Auto_Modificacion                   →  REPO REAL de AIDEN (cwd = raíz del proyecto)
                                              una FUNCIÓN nueva para el propio AIDEN
```

---

## 2. Ruta 1 — AIDEN Constructor (`Funciones_Slide/Sistema/Programador.py`)

Para cuando Marco pide algo de alto nivel tipo "hazme una app que..." / "construye un script
que...". Dos tools (#44 y #45):

### `crear_proyecto(instruccion, nombre?)`
- Crea (o reutiliza) una carpeta en el **sandbox** `~/Desktop/Proyectos_AIDEN/<slug-del-nombre>`.
- Lanza Claude Code con `cwd` = esa carpeta y un prompt que le pide construir TODO lo necesario
  (con punto de entrada claro: `main.py`/`app.py`) y resumir en 2-3 líneas qué hizo.
- Corre en **hilo daemon** (`threading.Thread(daemon=True)`) porque puede tardar minutos
  (`TIMEOUT_CLAUDE = 1800`s); AIDEN responde de inmediato ("manos a la obra, señor... le aviso
  en cuanto termine") y solo cuando el hilo termina avisa por voz (`hablado_del_asistente`) con
  el resumen real.
- El proyecto queda **visible en el Escritorio**, no escondido — Marco puede abrirlo, editarlo,
  subirlo a git por su cuenta.

### `ejecutar_proyecto(nombre?, archivo?)`
- Resuelve la carpeta (por nombre, o la última modificada si no se especifica).
- Busca un punto de entrada (`main.py`/`app.py`/`run.py`/`__main__.py`, o el primer `.py` que
  encuentre) y lo corre con `sys.executable` (el mismo intérprete/venv de AIDEN), `cwd` =
  la carpeta del proyecto, `timeout = 60`s.
- Devuelve stdout si salió bien, o las últimas líneas de stderr si falló — AIDEN puede leer el
  error en voz alta o pasarlo a `explicar_error`.

**Pendiente real**: un proyecto generado con dependencias propias (ej. necesita `requests` y el
venv de AIDEN no lo tiene) fallaría al ejecutar — v1 corre con el venv de AIDEN, no crea uno
nuevo ni hace `pip install` automático. No probado en vivo todavía.

---

## 3. Ruta 2 — `Auto_Modificacion` ahora también vía Claude Code

Vive en `Comunicacion/Funciones_Variadas.py` (no en Programador.py — sigue siendo la tool
"clásica" de auto-programación, solo que internamente cambió de motor).

- **Firma nueva**: `Auto_Modificacion(nombre_habilidad, instruccion)` — el parámetro
  `codigo_python` desapareció; ahora es `instruccion` en lenguaje natural (igual que
  `crear_proyecto`). El schema en `configuracion_del_agente.py` y el `PROTOCOLO DE
  AUTO-PROGRAMACIÓN` del prompt en `Cerebro.py` se actualizaron para reflejarlo.
- **Sin sandbox**: a diferencia de `crear_proyecto`, aquí `cwd` = la **raíz real del repo de
  AIDEN**. El prompt a Claude Code está acotado a "agrega esta función al final de
  `Nucleo_Slide/Auto_Programacion.py`, sin tocar nada más" — pero sigue siendo edición directa
  del código que AIDEN ejecuta. Riesgo aceptado (igual que el resto: `bypassPermissions`, Marco
  ya corre todo en bypass).
- **Validación antes de activar**: una vez Claude Code termina, se lee el archivo y se valida
  con `compile()` que el Python generado sea sintácticamente correcto ANTES de hacer
  `importlib.reload(Auto_Programacion)`. Si falla la sintaxis, no se recarga (evita dejar a
  AIDEN en un estado roto a medias).
- **En vivo, sin reiniciar**: gracias al `reload`, la nueva habilidad queda disponible de
  inmediato en la misma sesión — no hace falta reiniciar AIDEN.
- Igual que `crear_proyecto`: corre en hilo daemon y avisa por voz al terminar.

### La distinción que importa
| | `crear_proyecto` / `ejecutar_proyecto` | `Auto_Modificacion` |
|---|---|---|
| Dónde escribe | Sandbox `Proyectos_AIDEN/` | Repo real de AIDEN |
| Qué produce | Un proyecto/app **aparte** | Una **habilidad propia** de AIDEN |
| Se activa | Ejecutándolo a mano (`ejecutar_proyecto`) | Solo (`importlib.reload`, en caliente) |
| Analogía | "AIDEN te construye una app" | "AIDEN aprende algo nuevo" |

---

## 4. De regalo: Interfaz Always-On más Jarvis

No usa Claude Code, pero se hizo en la misma tanda de mejoras y es parte de la "experiencia
Jarvis": que Marco controle por voz si la ventana se queda, se esconde, y cómo lo escucha AIDEN.
Todos son **atajos SIN LLM** en `Procesar_Peticion` (igual que los comandos de música: coste $0,
instantáneos, no gastan tokens).

### 4.1 Ventana: quedarse o esconderse
- `Interfaz_En_Python.py` (SlideHUD): el timeout de inactividad de la ventana subió de
  **60s a 120s** (`_ms_inactividad`); se reinicia con cada texto/voz nueva vía
  `_reiniciar_timer()`, que respeta un flag `_fijada`.
- **Quédate**: "quédate" / "mantente" / "no te ocultes" / "no te vayas" / "no te escondas"
  → `pedir_fijar.emit(True)`: la ventana NO se auto-oculta.
- **Descansa / ocúltate** (lista ampliada a propósito, antes era muy restrictiva): "descansa",
  "descansar", "ocúltate", "escóndete", "duerme", "a dormir", "puedes irte", "retírate"…
  → oculta la ventana y vuelve a REPOSO. Truco: se usan **raíces sueltas** (`"descansa"` ya
  engancha *descansa/descansar/ya descansa/puedes descansar*), por eso funciona con frases
  naturales y no solo con la frase exacta.
- Señales Qt nuevas, thread-safe: `pedir_fijar` (bool) y `pedir_ocultar`.
- **Decisión**: el auto-recogerse es MÁS Jarvis que una ventana fija por defecto — pero el
  usuario manda con los comandos.

### 4.2 Modo MANOS LIBRES (sesión de mic abierto)
Para no tener que decir la palabra clave (ni dar clic) en cada turno. Es una **sesión que se
activa y desactiva por voz** (no un "siempre encendido"), justo para no responderle a la tele
todo el día.
- **Entrar**: "modo manos libres" / "escúchame" / "modo conversación" → abre el mic: hablas
  todo lo que quieras y AIDEN responde, turno tras turno, sin palabra clave ni clic.
- **Salir**: "descansa" (sale y oculta) / "modo normal" / "deja de escuchar" (sale y sigue
  visible). Y **auto-salida por silencio**: tras ~5 min sin hablar (`MAX_SILENCIOS=15` turnos ×
  `ESPERA=20s`) sale solo y avisa, para no dejar el mic abierto eternamente.
- Estado en dos globales de `Main_AlwaysOn.py`/`Main.py`: `_manos_libres` y
  `_silencios_manos_libres`. La lógica vive en el bucle de seguimiento de `Procesar_Peticion`
  (un `while` interno que escucha y NO re-procesa el comando viejo).
- **Tradeoff aceptado** (Marco lo eligió sobre las otras opciones): mientras está activo, si la
  tele/música/otra persona habla con voz clara, AIDEN puede contestar. Por eso es una sesión
  acotada + auto-salida, no un mic permanente. El filtro anti-alucinaciones (ver *Bugs A7*)
  amortigua el ruido de fondo.

---

## 5. Qué falta probar en vivo

Ninguna de las piezas de este documento se ha probado con AIDEN corriendo de verdad todavía
(necesitan reiniciar AIDEN + usar voz real):
1. `crear_proyecto` construyendo algo real de punta a punta y `ejecutar_proyecto` corriéndolo.
2. `Auto_Modificacion` con la nueva firma, verificando que el `reload` deje la habilidad usable
   en la misma sesión.
3. Los comandos "quédate"/"descansa" y el **modo manos libres** en la ventana Always-On.

---

### Para la wiki
- Página de entidad: **Programador.py** (AIDEN Constructor), enlazada a la página de
  *Auto_Modificacion* y a la de *los dos cerebros* (Arquitectura §2).
- Página de decisión: **"sandbox vs repo real — cuándo cada ruta"** (la tabla de §3 es la base).
- Página de decisión: **"por qué AIDEN dejó de escribir código él mismo"** (gemini orquesta,
  Claude Code programa) — enlaza con la página de *modelo de dos niveles* (Decisiones).
- Actualizar la página de la herramienta *Auto_Modificacion* existente: cambió de parámetro
  (`codigo_python` → `instruccion`) y de motor (gemini → Claude Code).
- Página de concepto: **"Control por voz / experiencia Jarvis"** (§4) — comandos de ventana +
  modo manos libres; enlazar con *barge-in* (Arquitectura §4) y con *Bugs A7* (alucinaciones).
- Página de decisión: **"manos libres como sesión, no como mic permanente"** (las 3 opciones que
  se evaluaron y por qué se eligió la sesión acotada).