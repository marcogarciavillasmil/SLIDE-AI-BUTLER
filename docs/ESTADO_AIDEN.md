# AIDEN — Estado completo del proyecto

Asistente de voz personal (tipo Jarvis) de Marco, en Python. Este documento resume TODO
lo construido, cómo funciona y qué queda pendiente. Sirve de memoria del proyecto.

> 🗺️ Punto de entrada y mapa de TODA la documentación: [SINTESIS_SESION.md](SINTESIS_SESION.md).
> Detalle por tema: [ARQUITECTURA_AIDEN.md](ARQUITECTURA_AIDEN.md) · [HERRAMIENTAS_AIDEN.md](HERRAMIENTAS_AIDEN.md) ·
> [DECISIONES_Y_FILOSOFIA.md](DECISIONES_Y_FILOSOFIA.md) · [BUGS_ARREGLADOS.md](BUGS_ARREGLADOS.md) ·
> [ENTORNO_Y_ARRANQUE.md](ENTORNO_Y_ARRANQUE.md).

---

## Cómo se ejecuta
- **Real (always-on)**: `AIDEN.bat` → `Main_AlwaysOn.py` (Qt siempre vivo + icono en bandeja). Fallback: `python Main.py`. Nunca un archivo suelto.
- Entorno virtual: **`Asistente_Slide_311`**.
- Flujo: instancia única → Telegram → login facial → palabra clave → interfaz (esfera) → conversación por voz/texto.

## Entorno / hardware (lo que costó configurar)
- GPU **RTX 5050 (Blackwell, sm_120)** → requiere **torch 2.11.0+cu128** y **torchaudio 2.11.0+cu128**.
- **Kokoro (TTS)** corre en CUDA con `torch.backends.cudnn.enabled = False`.
- **FasterWhisper (STT)**: modelo "small", `device="cuda"`, `compute_type="int8_float16"`.
- **LLM**: `google/gemini-2.5-flash` (cerebro/texto Y visión/documentos), vía **OpenRouter**. Antes el
  texto usaba `flash-lite`, pero con 44 tools malformaba ~50% de las llamadas (MALFORMED_FUNCTION_CALL);
  `flash` es confiable (0 errores) y casi igual de rápido. Temp 0.7 (chispa) + reintento a 0 si malforma.
- Datos privados en **`secretos.py`** (fuera de git): `OPENROUTER_API_KEY`, `CONTACTOS`, `PORTAFOLIO`, `DISPOSITIVO_LLAMADA`.

## Arquitectura (paquetes)
- **Nucleo_Slide/**: `Cerebro.py` (LLM + function calling + system prompt), `configuracion_del_agente.py` (las **43 herramientas**), `Memoria.py` (datos), `Memoria_Episodica.py` (conversaciones), `Auto_Programacion.py`.
- **Voz_Slide/**: `Herramientas_del_asistente.py` (Kokoro TTS, barge-in, candado de audio, hablar_en_dispositivo), `Transcriptor.py` (Whisper STT), `VAD.py` (palabra clave).
- **Funciones_Slide/**: las herramientas en 4 subpaquetes (`Comunicacion/`, `Sistema/`, `Info/`, `Productividad/`).
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
- **Proactividad**: alertas de mercado, take-over (resumen de notificaciones), anti-maratón, y **anticipación** (8 avisos: clima, disco, GPU, RAM, internet, mercado, notas, trasnochada).
- **Activación por presencia**: te saluda al llegar al PC (cámara + reconocimiento facial), con candados anti-molestia.
- **Memoria episódica**: recuerda conversaciones pasadas (recall pasivo + tool `recordar_conversacion`).
- **Fecha/hora** real inyectada en el prompt cada turno (antes AIDEN no sabía el día/hora).
- **Wake word "AIDEN"** (responde a su propio nombre).
- **Candado de audio**: nunca se montan dos voces a la vez.
- **Filtro de Markdown** para que Kokoro no lea símbolos. **stdout en UTF-8** (no crashea con emojis).

## Las 43 herramientas (function calling)
> Catálogo COMPLETO y al día (1 ficha por tool, con parámetros y módulo) en
> [HERRAMIENTAS_AIDEN.md](HERRAMIENTAS_AIDEN.md). Resumen por categoría:

**Comunicación**: Enviar_mensaje_Whatsapp, llamada_whatsapp, colgar, contestar_llamada.
**Apps/web/info**: Abrir_Apps, Abrir_Videos_Youtube, Buscar_en_Google (ABRE navegador), buscar_en_internet (DEVUELVE texto), noticias_del_dia, clima.
**Sistema/PC**: control_volumen, cerrar_aplicacion, ver_apps_abiertas, controlar_energia, tomar_captura, ajustar_brillo, buscar_archivo, control_ventana, dictar, abrir_carpeta, leer_portapapeles, control_musica, estado_sistema, Salir.
**Finanzas**: consultar_accion, mis_acciones (= antiguas resumen_acciones + mi_portafolio).
**Visión/pantalla**: analizar_vision, analizar_pantalla.
**Productividad**: tomar_nota, leer_notas, guardar_en_json, activar_protocolo, modo_gaming, resumen_actividad.
**Resúmenes/utilidades**: resumir (= documento + YouTube), calculadora, convertir_moneda.
**Memoria**: recordar, olvidar, recordar_conversacion.
**Razonamiento/código**: consultar_experto, explicar_error.
**Auto-programación**: Auto_Modificacion.

> Cambios (jun 2026): **47 → 43**. Se quitaron `traducir` y `definir` (el modelo los hace inline) y se
> fusionaron finanzas (`mis_acciones`) y resúmenes (`resumir`). Antes ya se había consolidado `clima`
> (= obtener_clima + pronostico_clima, que siguen como funciones internas). `Buscar_en_Google` (abre
> navegador) y `buscar_en_internet` (devuelve texto) NO se fusionaron (son distintas). Demasiadas tools
> degradan el function-calling: si AIDEN empieza a confundir herramientas, consolidar más.

## Hilos en segundo plano (arrancan tras el login)
- `monitor_de_tareas`: ejecuta tareas/recordatorios programados a su hora.
- `iniciar_alertas`: avisa de movimientos fuertes (±4%) o precios objetivo de tus acciones.
- `iniciar_guardian_descanso`: anti-maratón (tras 2h de actividad real sugiere descansar).
- `iniciar_anticipacion`: 8 avisos proactivos (clima, disco, GPU, RAM, internet, mercado, notas, trasnochada).
- `iniciar_presencia`: te saluda al llegar (cámara cada 25s + reconocimiento facial).
- `iniciar_telegram`: bot de control remoto (arranca ANTES del login). El centinela de código vigila SyntaxError.
> Todos se PAUSAN en modo gaming.

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
