# AIDEN — Catálogo de las 43 herramientas (fuente para la wiki)

> Documento-fuente para el segundo cerebro. Una ficha por herramienta (tool) de function-calling:
> qué hace, cuándo se usa, parámetros y en qué módulo vive. Estado: junio 2026, 43 tools.
> Registro central: `Nucleo_Slide/configuracion_del_agente.py` (esquema `tools` + mapa `tools_map`).
> Sugerencia para la wiki: crear UNA página de entidad por herramienta y enlazarlas a sus conceptos.

Convención de columnas: **Herramienta** · qué hace / cuándo se usa · **Parámetros** (los opcionales con `?`) · **Módulo**.

---

## 1. Comunicación — WhatsApp y llamadas

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `Enviar_mensaje_Whatsapp` | Envía un WhatsApp inmediato a un contacto. | `nombre_contacto`, `mensaje` | Comunicacion/Funciones_Variadas.py |
| `llamada_whatsapp` | Inicia una llamada de WhatsApp a un contacto. | `nombre_contacto` | Comunicacion/Funciones_Variadas.py |
| `colgar` | Cuelga / finaliza la llamada en curso. | — | Comunicacion/Funciones_Variadas.py |
| `contestar_llamada` | Contesta una llamada y le dice un mensaje al contacto con la voz de AIDEN (vía VB-CABLE). Si no se especifica qué decir, AIDEN pregunta primero. | `mensaje` (en 3ª persona) | Comunicacion/Llamadas.py |

> Los contactos viven en `secretos.py` (`CONTACTOS`). Las llamadas necesitan VB-CABLE configurado (`DISPOSITIVO_LLAMADA`).

---

## 2. Control del PC — apps, ventanas, energía, multimedia

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `Abrir_Apps` | Abre una app por el buscador de Windows (tecla Win). | `Aplicacion` | Sistema/Comandos_Asistente.py |
| `cerrar_aplicacion` | Cierra una app por su proceso (ej. chrome.exe). | `nombre_app` | Sistema/Funciones_Sistema.py |
| `ver_apps_abiertas` | Lista los procesos/apps en ejecución. | — | Sistema/Funciones_Sistema.py |
| `control_volumen` | Sube/baja/silencia o pone un nivel exacto (0-100). | `accion`, `nivel?` | Sistema/Funciones_Sistema.py |
| `control_ventana` | Minimiza/maximiza/cierra/cambia ventana o muestra escritorio. | `accion` | Sistema/Control_PC.py |
| `controlar_energia` | Apaga/reinicia/suspende/bloquea (o cancela), con retraso opcional. | `accion`, `minutos?` | Sistema/Control_PC.py |
| `ajustar_brillo` | Sube/baja o fija el brillo de pantalla. | `accion` | Sistema/Control_PC.py |
| `tomar_captura` | Toma un screenshot y lo guarda en la carpeta Capturas. | — | Sistema/Control_PC.py |
| `abrir_carpeta` | Abre una carpeta del PC (descargas, documentos, etc.). | `nombre` | Sistema/Control_PC.py |
| `dictar` | Escribe un texto donde esté el cursor (vía portapapeles). | `texto` | Sistema/Control_PC.py |
| `buscar_archivo` | Busca un archivo por nombre en tus carpetas y abre el primero. | `nombre` | Sistema/Control_PC.py |
| `control_musica` | Teclas multimedia: pausa/play/siguiente/anterior/parar. | `accion` | Sistema/Funciones_Sistema.py |
| `estado_sistema` | Reporta batería, CPU, RAM, GPU/VRAM/temperatura e IP. | — | Sistema/Funciones_Sistema.py |
| `Salir` | Se despide y cierra el asistente. | — | Sistema/Comandos_Asistente.py |

> Atajo: en Main.py los comandos de música más comunes ("pausa", "siguiente", …) se atienden SIN LLM (coste $0, instantáneo).

---

## 3. Búsqueda, web e información

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `buscar_en_internet` | Busca en la web y DEVUELVE EL TEXTO para que AIDEN responda con datos reales (no abre navegador). | `consulta` | Sistema/Funciones_Sistema.py |
| `Buscar_en_Google` | ABRE el navegador con los resultados de Google (cuando Marco quiere VERLOS). | `Pagina` | Sistema/Comandos_Asistente.py |
| `Abrir_Videos_Youtube` | Busca y reproduce un video/música en YouTube. | `Tipo_Video` | Sistema/Comandos_Asistente.py |
| `noticias_del_dia` | Trae titulares recientes (con fecha y fuente), opcional por tema/país. | `tema?` | Info/Noticias.py |
| `clima` | Clima actual o pronóstico de una ciudad (default Bogotá). | `ciudad`, `cuando?` | Sistema/Funciones_Sistema.py |

> Distinción clave: `buscar_en_internet` = texto para responder; `Buscar_en_Google` = abrir la búsqueda en pantalla. NO se fusionaron a propósito (son distintas).

---

## 4. Visión y pantalla

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `analizar_vision` | Usa la CÁMARA para ver el entorno y analizarlo (qué ve, opina, detecta daños). | `consulta?` | Info/Vision.py |
| `analizar_pantalla` | Captura la PANTALLA y la analiza (explicar error en pantalla, resumir lo abierto). | `consulta?` | Info/Vision.py |
| `leer_portapapeles` | Lee lo que copiaste para explicarlo/resumirlo. | — | Sistema/Funciones_Sistema.py |

---

## 5. Finanzas

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `consultar_accion` | Precio actual, cambio del día, objetivo y recomendación de UN activo (acción, cripto, oro…). | `simbolo` | Info/Finanzas.py |
| `mis_acciones` | Resumen de su watchlist y/o su portafolio (posiciones + ganancia/pérdida). **Fusiona** las antiguas `resumen_acciones` + `mi_portafolio`. | `tipo?` (resumen/portafolio/todo) | Info/Finanzas.py |

> El portafolio vive en `secretos.py` (`PORTAFOLIO`).

---

## 6. Productividad — tareas, notas, protocolos, modos

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `guardar_en_json` | Programa una tarea/mensaje/llamada/recordatorio para el FUTURO. | `accion`, `target`, `info`, `hora` | Productividad/Gestion_datos.py |
| `tomar_nota` | Guarda una nota rápida. | `nota` | Productividad/Notas.py |
| `leer_notas` | Lee las notas guardadas. | — | Productividad/Notas.py |
| `activar_protocolo` | Escena tipo Jarvis: cine / buenas noches / concentración / normal. | `nombre` | Productividad/Protocolos.py |
| `modo_gaming` | Activa/desactiva modo gaming: silencia notis, pausa avisos y LIBERA VRAM. | `activar` | Sistema/Modos.py |
| `resumen_actividad` | Resume lo que pasó mientras no estabas (notificaciones de Windows). | `horas?` | Info/Bitacora.py |

---

## 7. Resúmenes y utilidades

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `resumir` | Resume un documento (PDF/texto por nombre) O un video de YouTube (por enlace) — detecta solo cuál es. **Fusiona** `resumir_documento` + `resumir_youtube`. | `fuente` | Info/Documentos.py |
| `calculadora` | Resuelve matemática EXACTA (AST seguro, sin `eval`): potencias, raíces, trig, %, etc. | `expresion` | Info/Utilidades.py |
| `convertir_moneda` | Convierte dinero con la tasa actual. | `cantidad`, `desde`, `hacia` | Info/Utilidades.py |

> Nota: `traducir` y `definir` se QUITARON — el modelo es multilingüe y sabe definiciones, lo hace inline (MODO CONOCIMIENTO del prompt). Para lo raro/reciente queda `buscar_en_internet`.

---

## 8. Memoria

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `recordar` | Guarda un dato PERMANENTE sobre Marco (gustos, fechas, datos). | `dato`, `categoria?` | Nucleo_Slide/Memoria.py |
| `olvidar` | Borra un recuerdo permanente. | `dato` | Nucleo_Slide/Memoria.py |
| `recordar_conversacion` | Busca en el historial de CONVERSACIONES pasadas ("¿de qué hablamos ayer?"). | `tema?`, `dias?` | Nucleo_Slide/Memoria_Episodica.py |

> Ver la fuente *Arquitectura §7* para cómo se combinan las tres memorias.

---

## 9. Razonamiento profundo y código

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `consultar_experto` | Enruta una pregunta GENUINAMENTE difícil al modelo potente (gemini-2.5-pro) y relata su respuesta. | `pregunta` (con todo el contexto) | Info/Experto.py |
| `explicar_error` | Explica un error/traceback y cómo arreglarlo (usa el experto). Si no se da, lo lee del portapapeles. | `error?` | Info/Codigo.py |

---

## 10. Auto-programación

| Herramienta | Qué hace / cuándo | Parámetros | Módulo |
|---|---|---|---|
| `Auto_Modificacion` | AIDEN se escribe a sí mismo una nueva función/habilidad en Python y la guarda. | `nombre_habilidad`, `codigo_python` | Comunicacion/Funciones_Variadas.py |

---

## Resumen por categoría (conteo)
- Comunicación: 4 · Control PC: 14 · Búsqueda/info: 5 · Visión/pantalla: 3 · Finanzas: 2
- Productividad: 6 · Resúmenes/utilidades: 3 · Memoria: 3 · Experto/código: 2 · Auto-prog: 1
- **Total: 43** ✅

## Historia del conteo (para la página de decisión "anti-bloat")
47 → quitar `traducir` y `definir` → 45 → fusionar (`resumen_acciones`+`mi_portafolio`→`mis_acciones`)
y (`resumir_documento`+`resumir_youtube`→`resumir`) → **43**. Motivo: más tools degradan la precisión
del function-calling y pesan ~8k tokens por llamada. Se consolidó SIN perder capacidad.

---

### Para la wiki
- Crear una **página de entidad por herramienta** (43 páginas), enlazada a su **módulo** y a los
  **conceptos** que toca (ej. `modo_gaming` ↔ *liberación de VRAM*; `consultar_experto`/`explicar_error`
  ↔ *modelo de dos niveles*; `recordar_conversacion` ↔ *las tres memorias*).
- Crear una **página de decisión**: *"anti-bloat: por qué 43 y no 47 tools"*.
