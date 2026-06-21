# AIDEN — Estado completo del proyecto

Asistente de voz personal (tipo Jarvis) de Marco, en Python. Este documento resume TODO
lo construido, cómo funciona y qué queda pendiente. Sirve de memoria del proyecto.

---

## Cómo se ejecuta
- Por el **ícono de AIDEN** en el escritorio, o corriendo **`Main.py`** (nunca un archivo suelto).
- Entorno virtual: **`Asistente_Slide_311`**.
- Flujo: login facial → palabra clave → interfaz (esfera) → conversación por voz/texto.

## Entorno / hardware (lo que costó configurar)
- GPU **RTX 5050 (Blackwell, sm_120)** → requiere **torch 2.11.0+cu128** y **torchaudio 2.11.0+cu128**.
- **Kokoro (TTS)** corre en CUDA con `torch.backends.cudnn.enabled = False`.
- **FasterWhisper (STT)**: modelo "small", `device="cuda"`, `compute_type="int8_float16"`.
- **LLM**: `google/gemini-2.5-flash` (cerebro/texto Y visión/documentos), vía **OpenRouter**. Antes el
  texto usaba `flash-lite`, pero con 44 tools malformaba ~50% de las llamadas (MALFORMED_FUNCTION_CALL);
  `flash` es confiable (0 errores) y casi igual de rápido. Temp 0.7 (chispa) + reintento a 0 si malforma.
- Datos privados en **`secretos.py`** (fuera de git): `OPENROUTER_API_KEY`, `CONTACTOS`, `PORTAFOLIO`, `DISPOSITIVO_LLAMADA`.

## Arquitectura (paquetes)
- **Nucleo_Slide/**: `Cerebro.py` (LLM + function calling + system prompt), `configuracion_del_agente.py` (las 37 herramientas), `Memoria.py`, `Auto_Programacion.py`.
- **Voz_Slide/**: `Herramientas_del_asistente.py` (Kokoro TTS, barge-in, candado de audio, hablar_en_dispositivo), `Transcriptor.py` (Whisper STT), `VAD.py` (palabra clave).
- **Funciones_Slide/**: todas las herramientas (ver abajo).
- **Interfaz/**: `Interfaz_En_Python.py` (PySide6 + QWebChannel), `index.html` (esfera HUD reactiva a la voz).
- **Main.py**: punto de entrada.

---

## Comportamientos "Jarvis" (no son tools, son cómo se siente)
- **Voz bidireccional** con Kokoro + Whisper.
- **Barge-in**: lo interrumpes hablando y se calla; luego te escucha sin repetir la palabra clave.
- **Conversación continua**: tras responder, escucha ~5s por si sigues hablando.
- **Multi-tool (encadenamiento)**: en un mismo turno puede usar VARIAS herramientas (hasta 5 rondas)
  — ej. calcular algo y consultar el clima en la misma orden. (`proceso_de_ia` es un loop de tool-calling.)
- **Personalidad con humor seco** (estilo Jarvis), que baja el humor si estás estresado.
- **Memoria persistente** entre sesiones (recordar/olvidar → `memoria.json`), ahora **estructurada**
  con fecha y categoría; se agrupa por categoría al inyectarla en el prompt.
- **Control remoto desde el celular (Telegram)**: `procesar_remoto` (cerebro de texto, mismas tools)
  + `Telegram_Control.py`. Bloqueado a tu chat_id. Necesita token (ver `CONTROL_CELULAR.md`).
- **Briefing al entrar** (hora + clima + recordatorios pendientes).
- **Proactividad**: alertas de mercado, take-over (resumen de notificaciones), anti-maratón.
- **Candado de audio**: nunca se montan dos voces a la vez.
- **Filtro de Markdown** para que Kokoro no lea símbolos. **stdout en UTF-8** (no crashea con emojis).

## Las 44 herramientas (function calling)
**Comunicación**: Enviar_mensaje_Whatsapp, llamada_whatsapp, colgar, contestar_llamada.
**Apps/web**: Abrir_Apps, Abrir_Videos_Youtube, Buscar_en_Google (ABRE el navegador), buscar_en_internet (DEVUELVE texto para responder).
**Sistema/PC**: control_volumen, cerrar_aplicacion, ver_apps_abiertas, controlar_energia (apagar/reiniciar/suspender/bloquear), tomar_captura, ajustar_brillo, buscar_archivo, control_ventana, dictar, abrir_carpeta, leer_portapapeles, control_musica, estado_sistema (batería/CPU/RAM/IP).
**Info**: clima (actual o pronóstico de varios días), consultar_accion, resumen_acciones, mi_portafolio, resumir_documento, resumen_actividad (take-over de notificaciones), noticias_del_dia.
**Utilidades**: calculadora (matemática exacta), convertir_moneda (tasa actual), traducir, definir (Wikipedia), resumir_youtube (transcripción de videos).
**Visión**: analizar_vision (cámara), analizar_pantalla (pantalla).
**Productividad**: tomar_nota, leer_notas, guardar_en_json (tareas/recordatorios).
**Modos**: activar_protocolo (cine/buenas noches/concentración/normal), modo_gaming.
**Memoria**: recordar, olvidar.
**Avanzado**: Auto_Modificacion (auto-programación), Salir.

> Nota de diseño: junio 2026 se añadieron 8 tools nuevas (37 → 45) y luego se consolidó `clima`
> (antes `obtener_clima` + `pronostico_clima`) → quedan **44**. `obtener_clima` y `pronostico_clima`
> siguen existiendo como funciones internas (`clima` las enruta; el briefing usa `obtener_clima`).
> `Buscar_en_Google` (abre navegador) y `buscar_en_internet` (devuelve texto) NO se fusionaron porque
> hacen cosas distintas; se afinaron sus descripciones. Demasiadas tools degradan el function-calling:
> si AIDEN empieza a confundir herramientas, consolidar más.

## Hilos en segundo plano (arrancan tras el login)
- `monitor_de_tareas`: ejecuta tareas/recordatorios programados a su hora.
- `iniciar_alertas`: avisa de movimientos fuertes (±4%) o precios objetivo de tus acciones.
- `iniciar_guardian_descanso`: anti-maratón (tras 2h de actividad real sugiere descansar).

---

## PENDIENTE
- 🔴 **Rotar la API key de OpenRouter** + hacer el repo privado (la key vieja sigue en el historial público).
- 🔌 **Cable de llamadas**: instalar VB-CABLE, poner micrófono de WhatsApp en "CABLE Output" y `DISPOSITIVO_LLAMADA = "CABLE Input"` en secretos.py.
- 🔵 **Tier 3 opcional**: Google Calendar, correo, control desde el celular (Telegram), casa inteligente.
- ⚙️ Menores: `Salir()` no cierra del todo (corre en hilo); habilidades auto-programadas no se vuelven llamables sin reiniciar.

## Decisiones de diseño importantes (no repetir errores)
- **NO usar tkinter** para el splash → causa `Tcl_AsyncDelete` (crash fatal). Si se quiere splash, usar Qt.
- **La cámara se abre dentro de las funciones** (hilo principal), no a nivel de módulo.
- **Vigilancia** (cámara siempre encendida) está **desactivada** del auto-arranque (peleaba con el login).
- Comandos frecuentes (música) tienen **atajos en Main.py sin pasar por el LLM** = $0.
