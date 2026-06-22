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
Jarvis" que motivó todo esto (que Marco controle si la ventana se queda o se esconde, en vez de
que se auto-oculte sin avisar a medio uso).

- `Interfaz_En_Python.py` (SlideHUD): el timeout de inactividad de la ventana subió de
  **60s a 120s** (`_ms_inactividad`); se reinicia con cada texto/voz nueva vía
  `_reiniciar_timer()`, que respeta un flag `_fijada`.
- **Comandos de voz SIN LLM** (atajos directos en `Procesar_Peticion`, igual que los de
  música): "quédate" / "mantente" / "no te ocultes" → fija la ventana (no se auto-oculta);
  "ocúltate" / "escóndete" / "ya descansa" / "puedes descansar" → la oculta y vuelve a REPOSO.
- Señales Qt nuevas, thread-safe: `pedir_fijar` (bool) y `pedir_ocultar`.
- **Decisión de diseño**: el auto-recogerse es MÁS fiel al estilo Jarvis que una ventana fija
  por defecto — pero el usuario manda con los comandos cuando quiere lo contrario.

---

## 5. Qué falta probar en vivo

Ninguna de las piezas de este documento se ha probado con AIDEN corriendo de verdad todavía
(necesitan reiniciar AIDEN + usar voz real):
1. `crear_proyecto` construyendo algo real de punta a punta y `ejecutar_proyecto` corriéndolo.
2. `Auto_Modificacion` con la nueva firma, verificando que el `reload` deje la habilidad usable
   en la misma sesión.
3. Los comandos "quédate"/"ocúltate" en la ventana Always-On.

---

### Para la wiki
- Página de entidad: **Programador.py** (AIDEN Constructor), enlazada a la página de
  *Auto_Modificacion* y a la de *los dos cerebros* (Arquitectura §2).
- Página de decisión: **"sandbox vs repo real — cuándo cada ruta"** (la tabla de §3 es la base).
- Página de decisión: **"por qué AIDEN dejó de escribir código él mismo"** (gemini orquesta,
  Claude Code programa) — enlaza con la página de *modelo de dos niveles* (Decisiones).
- Actualizar la página de la herramienta *Auto_Modificacion* existente: cambió de parámetro
  (`codigo_python` → `instruccion`) y de motor (gemini → Claude Code).