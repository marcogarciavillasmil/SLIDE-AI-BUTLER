# AIDEN — Síntesis general (fuente 1 / punto de entrada para la wiki)

> Overview que ata todo: qué es AIDEN, quién es Marco, la filosofía, y el mapa hacia las fuentes
> detalladas. Para el detalle, seguir los enlaces a los otros documentos de `docs/`.

## Qué es AIDEN
Asistente de voz tipo **Jarvis** hecho en Python: mayordomo digital con personalidad, voz,
visión, control total del PC, proactividad y **43 herramientas** de function-calling. Arranca en
modo always-on (`AIDEN.bat` → `Main_AlwaysOn.py`).

## Quién es Marco
Estudiante universitario, gamer, fan del fútbol, inversor, **programador principiante**.
Preferencia de trabajo: **analizar antes de editar, cambios quirúrgicos, no editar de más**.

## La filosofía en una frase
**Personalidad sagrada + acción sobre explicación + latencia > IQ + menos tools (mejor precisión)
+ proactividad con candados.** (Detalle en [decisiones](DECISIONES_Y_FILOSOFIA.md).)

## Mapa de fuentes (léelas en este orden)
1. **Esta síntesis** — overview.
2. [ARQUITECTURA_AIDEN.md](ARQUITECTURA_AIDEN.md) — cómo está construido por dentro (2 cerebros,
   loop multi-tool, streaming+barge-in, escalada de temperatura, 3 memorias, voz, always-on).
3. [HERRAMIENTAS_AIDEN.md](HERRAMIENTAS_AIDEN.md) — catálogo de las 43 tools (1 ficha c/u).
4. [DECISIONES_Y_FILOSOFIA.md](DECISIONES_Y_FILOSOFIA.md) — el PORQUÉ de cada decisión (D1–D17).
5. [BUGS_ARREGLADOS.md](BUGS_ARREGLADOS.md) — bugs resueltos con causa raíz + fix.
6. [ENTORNO_Y_ARRANQUE.md](ENTORNO_Y_ARRANQUE.md) — stack, secretos, cómo correrlo y extenderlo.
7. [ESTADO_AIDEN.md](ESTADO_AIDEN.md) — estado general del proyecto.
8. [CONTROL_CELULAR.md](CONTROL_CELULAR.md) y [PLAN_ALWAYS_ON.md](PLAN_ALWAYS_ON.md) — features puntuales.

## Lo hecho en la última sesión (junio 2026)
- **Wake word "AIDEN"** (responde a su nombre).
- **Activación por presencia** (te saluda al llegar; 6 candados anti-molestia).
- **Memoria episódica** (recuerda conversaciones) + tool `recordar_conversacion`.
- **Tool `explicar_error`** (lee el portapapeles, usa el modelo experto).
- **Fecha/hora en el prompt** (AIDEN no sabía el día/hora).
- **Consolidación de tools 47 → 43** (quitadas `traducir`/`definir`; fusionadas `mis_acciones` y `resumir`).
- **Prompt** limpiado (secciones de ejecución fusionadas, MODO EXPERTO pulido, typos).
- **Limpieza** de imports `whisper` muertos + paquete Graphite ajeno.
- **Bugfixes**: path de `Marco.jpg`, acceso denegado tardío.
- **GitHub**: `.gitignore` arreglado (venv fuera) y push hecho.

## Pendientes clave
- 🔴 Rotar la API key de OpenRouter (sigue en el historial público) + repo privado.
- 🟡 Probar en vivo lo nuevo; liberar disco C.
- 🔵 Verificación por voz (speaker ID) — necesitaría dependencia nueva.

> Para el detalle de CUALQUIER punto de arriba, abrir el documento correspondiente del mapa.
