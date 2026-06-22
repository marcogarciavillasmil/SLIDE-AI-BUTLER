# AIDEN — Entorno, arranque y cómo extenderlo (fuente para la wiki)

> Documento-fuente para el segundo cerebro: el setup técnico, cómo se ejecuta, qué necesita
> `secretos.py`, cómo añadir una herramienta nueva, los hilos de fondo y los pendientes.

---

## 1. Hardware y stack

| Pieza | Detalle |
|---|---|
| GPU | RTX 5050 (Blackwell, **sm_120**) → requiere **torch 2.11.0+cu128** y torchaudio 2.11.0+cu128 |
| venv | **`Asistente_Slide_311`** (Python 3.11) |
| LLM cerebro | `google/gemini-2.5-flash` vía **OpenRouter** |
| LLM experto | `google/gemini-2.5-pro` (solo `consultar_experto` / `explicar_error`) |
| STT (petición) | FasterWhisper **`small`**, `device="cuda"`, `compute_type="int8_float16"` |
| STT (wake word) | Whisper **`medium`** en **CPU** (para que liberar VRAM no mate la palabra clave) |
| VAD | Silero VAD (detecta si hay voz) |
| TTS | **Kokoro-82M** (es), CUDA, `torch.backends.cudnn.enabled = False`. Voz = mezcla `em_santa` 45% + `jf_alpha` 55% |
| GUI | PySide6 (QWebChannel) + `index.html` (esfera HUD reactiva a la voz) |

Instalación de dependencias: `pip install -r requirements.txt` (incluye `--extra-index-url`
de cu128 para que torch baje con CUDA).

---

## 2. `secretos.py` (NO va en git)

Está en `.gitignore`. Plantilla en `secretos.ejemplo.py`. Claves que usa el proyecto:

```python
OPENROUTER_API_KEY = "..."          # clave de OpenRouter (cerebro + visión + experto)
CONTACTOS = {"MAMA": "57...", ...}  # números para WhatsApp/llamadas
PORTAFOLIO = {"NVDA": {"acciones": x, "precio_compra": y}, ...}  # finanzas
DISPOSITIVO_LLAMADA = "CABLE Input" # VB-CABLE para meter la voz en llamadas (None si no se usa)
TELEGRAM_TOKEN = "..."              # control remoto por Telegram (sin token, queda desactivado)
TELEGRAM_CHAT_ID = "..."            # chat autorizado (solo Marco)
```

🔴 **Pendiente crítico**: la API key vieja quedó en el historial de git (repo público) → **rotarla**.

---

## 3. Cómo se ejecuta

- **Real / always-on**: `AIDEN.bat` → `Main_AlwaysOn.py` (Qt siempre vivo + icono en bandeja +
  reposo escuchando la palabra clave). También hay `AIDEN_oculto.vbs` para arrancar sin consola.
- **Fallback manual**: `python Main.py` (mismo flujo sin bandeja/persistencia).
- **Flujo**: candado de instancia única → `iniciar_telegram()` → login facial → palabra clave →
  esfera (GUI) → conversación por voz/texto. Tras el login arrancan los hilos de fondo.
- NUNCA correr un archivo suelto del paquete; siempre por `Main*.py` (por los imports relativos).

---

## 4. Llamadas con VB-CABLE (opcional)

Para que AIDEN hable DENTRO de una llamada de WhatsApp:
1. Instalar **VB-CABLE**.
2. Micrófono de WhatsApp = **"CABLE Output"**.
3. `DISPOSITIVO_LLAMADA = "CABLE Input"` en `secretos.py`.
AIDEN reproduce su voz por "CABLE Input" → entra como micrófono a la llamada. Ya quedó configurado.

---

## 5. Hilos en segundo plano (arrancan tras el login)

| Hilo | Archivo | Qué hace |
|---|---|---|
| Tareas programadas | Productividad/Tareas_Hilos_Comandos.py | Ejecuta tareas/recordatorios a su hora |
| Alertas de mercado | Productividad/Alertas_Mercado.py | Avisa movimientos fuertes / precios objetivo |
| Guardián de descanso | Productividad/Descanso.py | Anti-maratón (tras ~2h sugiere descansar) |
| Anticipación | Productividad/Anticipacion.py | 8 avisos proactivos (clima, disco, GPU, etc.) |
| Presencia | Sistema/Presencia.py | Te saluda al llegar (cámara, cada 25s) |
| Telegram | Comunicacion/Telegram_Control.py | Polling del bot (control remoto) |
| Centinela de código | Nucleo_Slide/Cerebro.py | Detecta SyntaxError en tus .py y se ofrece a ayudar |

Todos se **pausan en modo gaming**. Detalle en *Arquitectura §10*.

---

## 6. Cómo AÑADIR una herramienta nueva (receta)

1. Escribe la función en el módulo que corresponda dentro de `Funciones_Slide/<Categoria>/`
   (o `Nucleo_Slide/` si es de memoria). Que devuelva un **string** (lo que AIDEN dirá/usará).
2. En `Nucleo_Slide/configuracion_del_agente.py`:
   - **Importa** la función arriba.
   - Añade su **esquema** a la lista `tools` (name, description clara de *cuándo* usarla, parameters).
   - Añade la entrada al **mapa** `tools_map` (`"nombre": funcion`).
3. Verifica: `python -m py_compile Nucleo_Slide/configuracion_del_agente.py` y que `tools` y
   `tools_map` tengan el MISMO número de entradas (sin descuadres).
4. Reinicia AIDEN para que cargue la tool nueva.

> Regla de oro (anti-bloat): antes de añadir, pregúntate si el modelo ya lo puede hacer inline
> o si se puede fusionar con una tool existente. Más tools = peor precisión de function-calling.

---

## 7. Estructura de carpetas (resumen)

```
SLIDE-AI-BUTLER/
  Main_AlwaysOn.py / Main.py        # arranque
  Nucleo_Slide/                     # cerebro, tools registry, memorias
  Voz_Slide/                        # VAD, Transcriptor, TTS
  Interfaz/                         # GUI (PySide6 + HTML)
  Funciones_Slide/
    Comunicacion/ Sistema/ Info/ Productividad/   # las herramientas
  Imagenes/                         # Marco.jpg (login facial) — gitignored
  docs/                             # documentación (estas fuentes)
  secretos.py                       # privado, gitignored
  Asistente_Slide_311/              # venv, gitignored
```

---

## 8. PENDIENTES (estado a junio 2026)
- 🔴 **Rotar la API key de OpenRouter** + repo privado (la key vieja sigue en el historial público).
- 🟡 **Probar en vivo** lo nuevo: presencia, memoria episódica, `explicar_error`, fecha/hora (necesita cámara/mic/GUI).
- 🟡 **Liberar disco C** (la anticipación lo detectó al 95%).
- 🔵 **Verificación por voz** (speaker ID): única feature pendiente que necesitaría dependencia nueva (resemblyzer/speechbrain + enrolamiento).
- 🔵 Tier 3 opcional: Google Calendar / correo / casa inteligente (necesitan credenciales/hardware).
- ⚙️ Menores: `Salir()` no cierra del todo (corre en hilo); habilidades auto-programadas no se vuelven llamables sin reiniciar.
- 💡 Idea guardada sin implementar: sacar info de LinkedIn (descartada por ahora).
