# Control de AIDEN desde el celular (Telegram)

AIDEN puede recibir órdenes desde tu teléfono por Telegram: le escribes a un bot y él
ejecuta la orden en el PC y te responde. Usa el mismo cerebro y las mismas 44 herramientas.

> **IMPORTANTE:** el control por Telegram arranca al ENCENDER AIDEN, **sin necesidad de pasar
> el reconocimiento facial ni la palabra clave**. O sea: con el PC prendido (y el auto-arranque),
> puedes controlarlo desde el celular aunque NO estés en casa. La seguridad la da el bloqueo a
> tu chat_id, no la cámara.

## Cómo reiniciar AIDEN (corre oculto, sin ventana)
Como AIDEN se ejecuta sin consola, para "reiniciarlo":
- **Cerrarlo:** abre el Administrador de tareas (Ctrl+Shift+Esc) → pestaña Detalles → busca
  `python.exe` (el de AIDEN) → clic derecho → Finalizar tarea. (O simplemente reinicia el PC.)
- **Abrirlo:** doble clic al ícono de AIDEN (o se abre solo al iniciar Windows por el auto-arranque).

## Activarlo (una sola vez, ~3 minutos)

1. **Crea el bot.** En Telegram busca **@BotFather**, ábrelo y manda `/newbot`.
   - Te pedirá un nombre (ej. `AIDEN`) y un usuario que termine en `bot` (ej. `aiden_marco_bot`).
   - Al final te da un **TOKEN** que se ve así: `123456789:AAH...xyz`.

2. **Pega el token** en `secretos.py`:
   ```python
   TELEGRAM_TOKEN = "123456789:AAH...xyz"
   ```

3. **Reinicia AIDEN** (ver arriba cómo). No necesitas pasar la cámara ni la palabra clave:
   el Telegram arranca al inicio. (En `AIDEN_log.txt` aparece `[Telegram] control remoto activo.`,
   pero no hace falta que lo revises — lo confirmas en el paso 4.)

4. **Autorízate.** Abre tu bot en Telegram y escríbele cualquier cosa (ej. "hola").
   AIDEN te responderá con tu **chat_id** (esa respuesta confirma que el bot ya está vivo).
   Copia ese número y ponlo en `secretos.py`:
   ```python
   TELEGRAM_CHAT_ID = "tu_chat_id"
   ```

5. **Reinicia AIDEN otra vez.** Desde ahora, **solo tú** puedes controlarlo por Telegram
   (a cualquier otro que le escriba al bot, AIDEN lo ignora).

## Cómo se usa

Le escribes al bot como si le hablaras en voz. Ejemplos:
- "¿cómo van mis acciones?"
- "sube el volumen al 30"
- "resume las notificaciones de hoy"
- "cuánto es 1500 dólares en pesos"
- "qué noticias hay de tecnología"

AIDEN ejecuta en el PC y te responde por chat. (No habla en voz alta para no asustarte
si no estás en casa; las respuestas llegan como texto al celular.)

## Seguridad
- El control queda **bloqueado a tu chat_id**. Nadie más puede mandarle órdenes.
- El token es como una contraseña: NO lo subas a GitHub. Vive en `secretos.py`, que está
  en `.gitignore` (fuera del repo público).

## Si algo no funciona
- ¿No dice "control remoto activo"? → falta `TELEGRAM_TOKEN` en `secretos.py`.
- ¿El bot no responde? → revisa que reiniciaste AIDEN y que el token está bien pegado.
- ¿Responde "no estás autorizado" o nada? → te falta poner tu `TELEGRAM_CHAT_ID`.
