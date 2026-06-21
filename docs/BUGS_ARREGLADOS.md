# Bugs arreglados — AIDEN

Resumen claro de los 4 bugs que se corrigieron y por qué fallaban.

---

## 1. `cerrar_aplicacion` — se rendía antes de tiempo
**Archivo:** `Funciones_Slide/Funciones_Sistema.py`

**El problema:** el `except` que captura errores tenía un `return` DENTRO del bucle.
Como Python recorre TODOS los procesos del sistema, si uno cualquiera (de Windows,
por ejemplo) negaba el acceso, la función se rendía y devolvía "no se pudo" ANTES de
llegar a tu aplicación.

**El arreglo:** cambié ese `return` por un `continue` (saltar ese proceso y seguir
buscando). Ahora recorre todos, cierra el tuyo, y solo al final decide el mensaje.
De paso ahora cierra TODAS las ventanas si hay varias (ej. varios chrome.exe).

```python
# ANTES (mal):
except (...):
    return "No se pudo cerrar"   # <- se rendía con el primer proceso ajeno

# AHORA (bien):
except (...):
    continue                      # <- ignora ese y sigue buscando
```

---

## 2. `monitor_de_tareas` — crasheaba el hilo de tareas
**Archivo:** `Funciones_Slide/Tareas_Hilos_Comandos.py`

**Dos problemas:**
- **`ident=4`** estaba mal escrito. La palabra correcta es **`indent=4`**. Con `ident`,
  `json.dump` lanzaba error y **mataba el hilo cada vez que se completaba una tarea**.
- Si el archivo `tareas.json` no existía, `open(...)` reventaba al arrancar.

**El arreglo:**
- `ident=4` -> `indent=4`.
- Si `tareas.json` no existe, espera 30s y reintenta (no crashea).
- (Extra) saqué el aviso de voz de adentro del bloque que escribe el archivo.

```python
# ANTES:
json.dump(tareas, f, ident=4)     # ident no existe -> error

# AHORA:
if not os.path.exists("tareas.json"):
    time.sleep(30); continue       # sin archivo, reintenta sin morir
...
json.dump(tareas, f, indent=4)    # correcto
```

---

## 3. `limpiar_historial` — crasheaba siempre
**Archivo:** `Funciones_Slide/Comandos_Asistente.py`

**El problema:** el mismo `ident=4` mal escrito -> cada vez que AIDEN intentaba limpiar
el historial, fallaba.

**El arreglo:** `ident` -> `indent`, protección por si no existe el archivo, y ahora
devuelve un mensaje de confirmación (antes no devolvía nada, así que AIDEN no sabía
si funcionó).

---

## 4. El centinela hacía `.lower()` sobre algo vacío
**Archivo:** `Nucleo_Slide/Cerebro.py`

**El problema:** antes, cuando escuchar al usuario fallaba por silencio, se cerraba todo
el programa. Eso ya lo cambiamos a que devuelva `None`. Pero quedó un punto donde se
hacía `escuchador_de_usuario().lower()`. Si devuelve `None`, `None.lower()` revienta
(`None` no tiene la función `.lower()`).

**El arreglo:** usar `or ""` para que, si viene vacío, trabaje sobre un texto vacío
en vez de romperse.

```python
# ANTES:
respuesta = escuchador_de_usuario().lower()        # None.lower() -> error

# AHORA:
respuesta = (escuchador_de_usuario() or "").lower() # si es None, usa ""
```

---

## Lo que aprendiste con estos bugs
- **Un typo en un parámetro** (`ident` vs `indent`) puede tumbar un hilo entero en silencio.
- **`return` dentro de un bucle** corta el bucle: cuidado dónde lo pones.
- **Siempre asume que una función puede devolver `None`** y protégete con `or ""`.
- **Verifica que un archivo exista** antes de abrirlo, si no siempre va a estar.

## Lo que NO se tocó (pendiente, decisión tuya)
- La **API key** en `Cerebro.py` y los **teléfonos** en `Funciones_Variadas.py` siguen
  expuestos en el repo público. Eso requiere rotar la credencial y limpiar el historial
  de git, por eso se deja para hacerlo juntos.
