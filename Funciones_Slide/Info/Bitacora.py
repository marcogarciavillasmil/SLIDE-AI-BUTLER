import os
import sqlite3
import shutil
import tempfile
from xml.etree import ElementTree
from datetime import datetime, timedelta

# Windows guarda TODAS las notificaciones en esta base de datos SQLite.
_DB = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Microsoft", "Windows", "Notifications", "wpndatabase.db"
)
_EPOCH_WIN = datetime(1601, 1, 1)


def _texto_de_payload(payload):
    # Cada notificacion guarda un XML (toast). Sacamos sus textos.
    if not payload:
        return ""
    try:
        if isinstance(payload, (bytes, bytearray)):
            payload = bytes(payload).decode("utf-8", "ignore")
        root = ElementTree.fromstring(payload)
        textos = [e.text.strip() for e in root.iter()
                  if e.tag.split("}")[-1] == "text" and e.text and e.text.strip()]
        return " | ".join(textos)
    except Exception:
        return ""


def _leer_notificaciones(horas):
    if not os.path.exists(_DB):
        return None
    tmp = os.path.join(tempfile.gettempdir(), "aiden_wpn.db")
    try:
        shutil.copy2(_DB, tmp)   # copia para evitar el bloqueo de Windows
    except Exception:
        return None

    desde = datetime.now() - timedelta(hours=horas)
    ft_desde = int((desde - _EPOCH_WIN).total_seconds() * 10_000_000)

    eventos = []
    try:
        con = sqlite3.connect(tmp)
        cur = con.cursor()
        cur.execute(
            "SELECT Payload, HandlerId, ArrivalTime FROM Notification "
            "WHERE ArrivalTime > ? ORDER BY ArrivalTime DESC", (ft_desde,)
        )
        filas = cur.fetchall()
        cur.execute("SELECT RecordId, PrimaryId FROM NotificationHandler")
        apps = {rid: pid for rid, pid in cur.fetchall()}
        con.close()
        for payload, hid, _arrival in filas:
            texto = _texto_de_payload(payload)
            if texto:
                eventos.append((apps.get(hid, ""), texto))
    except Exception:
        eventos = []
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return eventos


def contar_actividad(horas=12):
    eventos = _leer_notificaciones(int(horas))
    return len(eventos) if eventos else 0


def resumen_actividad(horas=16):
    try:
        horas = int(horas)
    except (ValueError, TypeError):
        horas = 16
    eventos = _leer_notificaciones(horas)
    if eventos is None:
        return "No pude acceder al registro de notificaciones de Windows, señor."
    if not eventos:
        return "No hubo notificaciones en ese periodo, señor."
    lineas = []
    vistos = set()
    for app, txt in eventos:
        if (app, txt) in vistos:
            continue
        vistos.add((app, txt))
        app_corto = (app or "App").replace("App", "").split("!")[-1].split("_")[0][:30] or "App"
        lineas.append(f"- [{app_corto}] {txt}")
        if len(lineas) >= 25:
            break
    return "Notificaciones recientes en tu PC:\n" + "\n".join(lineas)
