# Contexto del Proyecto: Aiden (SLIDE-AI-BUTLER)
Eres el asistente de desarrollo autónomo para el proyecto "Aiden". Tienes control sobre el código local en este directorio y acceso de lectura/escritura a nuestra base de conocimiento externa en Obsidian.

## Ruta de la Base de Conocimiento (Obsidian)
Nuestra documentación, mapa de arquitectura y logs históricos de decisiones están en la siguiente ruta absoluta:
`C:\Users\Usuario\Documents\Cerebros\Inversion\Aiden_AI_Cerebro\Aiden-AI\`

## Reglas de Navegación y Ahorro de Contexto
Para optimizar el uso de mensajes y mantener tus respuestas rápidas, sigue estrictamente estas reglas al interactuar con Obsidian:

1. **Estado Actual y Tareas:** Para saber qué se ha hecho, qué bugs recientes surgieron o qué está pendiente, lee únicamente el archivo:
   `C:\Users\Usuario\Documents\Cerebros\Inversion\Aiden_AI_Cerebro\Aiden-AI\log.md`
2. **Mapa General:** Si necesitas entender la arquitectura global de Aiden o cómo se conectan las carpetas, lee únicamente el archivo:
   `C:\Users\Usuario\Documents\Cerebros\Inversion\Aiden_AI_Cerebro\Aiden-AI\Index.md`
3. **Búsquedas en la Wiki:** NUNCA leas las carpetas `wiki/` o `raw/` completas. Si necesitas información sobre un bug pasado o una API, usa comandos de búsqueda en la terminal (`grep` o comandos de listado) dentro de la ruta de Obsidian para localizar el archivo `.md` exacto antes de abrirlo.
4. **Documentación de Progreso:** Cada vez que resolvamos un bug complejo o implementemos una función clave aquí en VS Code, debes escribir un resumen breve y estructurado al final del archivo `log.md` en Obsidian para que quede registrado.

## Comandos del Proyecto
- **Instalar dependencias:** `pip install -r requirements.txt`
- **Ejecutar proyecto:** `python Main.py` (o `python Main_AlwaysOn.py` según se requiera)
- **Pruebas:** `python -m unittest` (revisar carpeta /Pruebas/)
5. **Formato de Log Ultra-Corto:** Al documentar en `log.md`, usa ÚNICAMENTE este formato de tres líneas:
   - **[FECHA]** - [Breve descripción del cambio]
   - *Razón:* [Por qué se hizo]
   - *Archivos modificados:* [Lista de archivos]
## Restricciones de Output (Ahorro de Tokens)
1. **Sin Introducciones ni Despedidas:** No digas "¡Claro, con gusto te ayudo!", "Aquí está el código" ni "Espero que esto funcione". Ve directo al grano.
2. **Explicaciones en Comentarios:** Si necesitas explicar por qué cambiaste una línea de código, ponlo como un comentario corto `#` arriba de la línea modificada. No escribas párrafos explicativos fuera del bloque de código.
3. **Formato DIFF o Parcial:** NUNCA me devuelvas un archivo de código completo si solo modificamos 3 líneas. Muéstrame únicamente el fragmento modificado o usa formato `diff`.
4. **Respuestas de Texto en Viñetas:** Si te hago una pregunta teórica, responde en un máximo de 3 viñetas (bullet points) de una sola frase cada una.