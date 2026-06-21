# Control REMOTO de AIDEN desde el celular vía Telegram (sin librerias extra: usa requests).
# Marco le escribe a un bot de Telegram y AIDEN ejecuta la orden en el PC y le responde.
#
# SETUP (una vez): ver CONTROL_CELULAR.md. Resumen:
#   1. En Telegram, habla con @BotFather -> /newbot -> te da un TOKEN.
#   2. Pon ese token en secretos.py:  TELEGRAM_TOKEN = "123456:ABC..."
#   3. Escríbele algo al bot; AIDEN te responderá tu chat_id. Ponlo en secretos.py:
#         TELEGRAM_CHAT_ID = "tu_chat_id"
#   4. Reinicia AIDEN. Desde ahí, solo TÚ podrás controlarlo por Telegram.

import time
import threading
import requests

from Nucleo_Slide.Cerebro import procesar_remoto

try:
    from secretos import TELEGRAM_TOKEN
except ImportError:
    TELEGRAM_TOKEN = None
try:
    from secretos import TELEGRAM_CHAT_ID
except ImportError:
    TELEGRAM_CHAT_ID = None

_API = "https://api.telegram.org/bot{token}/{metodo}"


def _enviar(token, chat_id, texto):
    try:
        requests.post(
            _API.format(token=token, metodo="sendMessage"),
            json={"chat_id": chat_id, "text": texto},
            timeout=15,
        )
    except Exception as e:
        print(f"[Telegram] no pude enviar: {e}")


def _bucle(token, chat_autorizado):
    offset = None
    if chat_autorizado:
        _enviar(token, chat_autorizado, "AIDEN en línea, señor. Listo para recibir órdenes.")

    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(
                _API.format(token=token, metodo="getUpdates"),
                params=params, timeout=40,
            )
            data = r.json()

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat_id = str(msg.get("chat", {}).get("id"))
                texto = (msg.get("text") or "").strip()
                if not texto:
                    continue

                # SEGURIDAD: si aun no hay chat autorizado, dile su id y NO ejecutes nada.
                if not chat_autorizado:
                    _enviar(token, chat_id,
                            f"Tu chat_id es {chat_id}. Ponlo en secretos.py como "
                            f"TELEGRAM_CHAT_ID = \"{chat_id}\" y reinicia AIDEN para autorizarte, señor.")
                    continue
                # Solo responde al chat de Marco; a desconocidos los ignora.
                if chat_id != str(chat_autorizado):
                    continue

                try:
                    respuesta = procesar_remoto(texto)
                except Exception as e:
                    respuesta = f"Tuve un problema procesando eso, señor: {e}"
                _enviar(token, chat_id, respuesta)

        except Exception as e:
            print(f"[Telegram] error en el bucle: {e}")
            time.sleep(5)   # error de red: espera y reintenta


def iniciar_telegram():
    # Arranca el control remoto por Telegram en un hilo de fondo, si hay token.
    if not TELEGRAM_TOKEN:
        print("[Telegram] sin TELEGRAM_TOKEN en secretos.py — control remoto desactivado.")
        return False
    hilo = threading.Thread(target=_bucle, args=(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID), daemon=True)
    hilo.start()
    print("[Telegram] control remoto activo.")
    return True
