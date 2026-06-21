# Plan: AIDEN siempre encendido (always-on)

> Documento de diseño. **No implementado todavía** — es el mapa para convertir AIDEN
> de "se enciende, una sesión, se apaga" a "vive encendido y escucha siempre, gastando
> casi nada cuando está en reposo". Escrito desde el código real de `Main.py` (junio 2026).

---

## 1. Cómo está hoy (y por qué no es "always-on")

Flujo actual en [Main.py](Main.py):

1. `iniciar_hilos()` al importar.
2. Voz "Iniciando sistema de seguridad".
3. `Reconocimiento_Facial()` → login con cámara.
4. `Reconocimiento_de_habla()` → palabra clave para activar.
5. Si login OK: briefing, alertas, guardián de descanso, y `ejecutar_slide(...)` (abre la esfera Qt).
6. `while Activado:` vuelve a abrir la esfera y **re-pide la palabra clave** cada vuelta.

**Problemas para ser always-on:**

- **El login se repite.** Cada vez que se cierra la ventana de la esfera, el `while` vuelve a
  pedir palabra clave (`Reconocimiento_de_habla()`). No es "una vez y ya".
- **La esfera Qt manda el ciclo de vida.** `ejecutar_slide()` bloquea hasta que la ventana se
  cierra; al cerrarse, el programa cae al `while` o termina. La app no "vive de fondo".
- **Activación por palabra clave fija (VAD).** El [VAD](Voz_Slide/VAD.py) busca una palabra
  concreta, no entiende contexto. No se puede "hablarle natural" sin la palabra.
- **No hay estado de reposo explícito.** O está en login, o en conversación. Falta un modo
  "dormido pero escuchando" que consuma casi nada.

---

## 2. Objetivo

Un solo proceso que:

1. Hace login **una sola vez** al arrancar (auto-arranque ya configurado: carpeta Inicio → VBS).
2. Entra en un **bucle de vida permanente** que nunca termina solo.
3. Tiene **dos estados**: `REPOSO` (escuchando barato) y `ACTIVO` (conversando).
4. En `REPOSO` consume mínimo: solo el VAD ligero corriendo; Whisper y el LLM **no** trabajan.
5. La esfera Qt es **opcional/secundaria**: se muestra al activarse y se oculta al volver a reposo,
   pero cerrarla **no mata** el proceso.

---

## 3. Arquitectura propuesta

### 3.1 Separar "ciclo de vida" de "interfaz"
Hoy `ejecutar_slide()` (Qt) es el dueño del loop. Hay que invertirlo:

- **Hilo principal = Qt** (PySide6 exige que la GUI viva en el hilo principal). El `app.exec()`
  de Qt es el loop permanente que nunca termina → eso ya da el "no se apaga".
- **Hilo de fondo = cerebro de voz** (`bucle_de_vida()`): login una vez, luego REPOSO↔ACTIVO.
- Comunicación hilo→GUI por **señales Qt** (ya existe `senal_voz`; añadir `senal_estado` para
  mostrar/ocultar la esfera y cambiar color según REPOSO/ACTIVO).

> Regla de oro del proyecto: **nunca tocar la GUI desde un hilo que no sea el principal**
> (por eso la cámara se abre dentro de las funciones, no a nivel de módulo). Todo cruce
> hilo→GUI va por señal.

### 3.2 El nuevo bucle de vida (pseudocódigo)

```python
def bucle_de_vida(ventana):
    if Reconocimiento_Facial() != "Bienvenido Marco":
        hablado_del_asistente("Acceso denegado")
        return                      # login UNA vez
    hablado_del_asistente("Bienvenido Marco")
    hablado_del_asistente(briefing())
    iniciar_alertas(hablado_del_asistente)
    iniciar_guardian_descanso(hablado_del_asistente)

    while True:                     # vive para siempre
        # --- REPOSO: barato, solo VAD escuchando la palabra/sonido de activación ---
        ventana.senal_estado.emit("reposo")     # esfera apagada/tenue
        Activado, _ = Reconocimiento_de_habla() # bloquea barato hasta oír activación
        if not Activado:
            continue

        # --- ACTIVO: conversación normal con barge-in + follow-up ---
        ventana.senal_estado.emit("activo")     # esfera encendida
        texto = escuchador_de_usuario()
        Procesar_Peticion(texto, ventana)
        # al terminar Procesar_Peticion vuelve arriba → REPOSO
```

`Main.py` quedaría: crear la app Qt + ventana, lanzar `bucle_de_vida` en un hilo
(`threading.Thread(daemon=True)`), y `app.exec()` en el principal.

### 3.3 Manejo del cierre de ventana
- Interceptar el `closeEvent` de la ventana: en vez de salir, **ocultar** (`hide()`) y seguir en
  REPOSO. Salir de verdad solo con el comando `Salir()` o una bandeja del sistema (tray icon).
- Opcional: **icono en la bandeja** (QSystemTrayIcon) con "Mostrar esfera / Salir". Es lo que da
  la sensación de "vive de fondo" como un servicio.

---

## 4. Consumo en reposo (lo que pidió Marco: "que no consuma casi")

| Componente | En REPOSO | Nota |
|---|---|---|
| VAD (Silero) | ligero, corre siempre | es el único que trabaja en reposo; CPU baja |
| Whisper STT | **inactivo** | solo transcribe cuando ya estás ACTIVO |
| LLM (OpenRouter) | **inactivo** | $0 en reposo; solo llama al conversar |
| Kokoro TTS | **inactivo** | solo al responder |
| Modelos en VRAM | cargados, 0% cómputo | ocupan memoria pero no calientan la GPU |

**Decisión clave:** mantener Whisper/Kokoro **cargados** en VRAM (no recargar cada vez) a cambio
de RAM/VRAM ocupada. Recargar modelos por cada activación añade segundos de latencia. Si la VRAM
molesta para juegos, el `modo_gaming` podría descargarlos y recargarlos al salir del juego.

---

## 5. La frontera cara: activación por CONTEXTO (no palabra clave)

Marco quiere "hablarle natural sin palabra clave". Eso es lo más caro y se deja para el final:

- Requiere **ASR continuo** (Whisper transcribiendo TODO el tiempo) + un clasificador que decida
  "¿esto me lo dijo a mí?". Eso rompe el ahorro en reposo (Whisper dejaría de estar inactivo).
- **Camino intermedio recomendado:** wake-word más natural/entrenable (p.ej. "AIDEN" / "oye AIDEN")
  con un detector tipo openWakeWord, que es barato y permite varias frases sin ASR completo.
- **Camino caro (futuro):** ventana corta de ASR local siempre activa + filtro de intención por
  LLM pequeño. Solo si Marco acepta el costo de CPU/GPU constante.

---

## 6. Orden de implementación sugerido (de menos a más riesgo)

1. **Invertir el control:** Qt en hilo principal, `bucle_de_vida` en hilo de fondo. (Riesgo medio:
   tocar el arranque; probar que el login y la esfera siguen funcionando.)
2. **Login una sola vez** + `while True` con estados REPOSO/ACTIVO. (Quita el re-login del `while`.)
3. **closeEvent → hide()** + tray icon para no morir al cerrar la ventana.
4. **Señal de estado** a la esfera (tenue en reposo, encendida en activo).
5. (Opcional) Descarga de modelos en `modo_gaming` para liberar VRAM.
6. (Futuro, caro) Activación por contexto / wake-word entrenable.

> Cada paso es probar-y-confirmar **con Marco presente** (necesita micrófono, cámara y ver la
> esfera). Por eso NO se implementa de noche sin supervisión: este doc es el plan, no el cambio.

---

## 7. Riesgos / cosas a no repetir
- **No usar tkinter** para nada de UI (crash `Tcl_AsyncDelete`). Todo Qt.
- **Cámara** se abre dentro de las funciones del hilo correcto, nunca a nivel de módulo.
- PortAudio **no es reentrante**: mantener el candado de audio (`_lock_audio`) — en always-on hay
  más hilos vivos, así que el candado importa aún más.
- `Salir()` hoy no cierra del todo (corre en hilo). En always-on, `Salir()` debe cerrar la app Qt
  de verdad (`QApplication.quit()` vía señal al hilo principal).
