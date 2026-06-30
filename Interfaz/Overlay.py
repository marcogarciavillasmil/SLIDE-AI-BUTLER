# OVERLAY DE PRESENCIA: hace VISIBLE el núcleo Jarvis. Una ventanita siempre-encima, semi-transparente
# y CLICK-THROUGH (no roba el mouse) en una esquina, que muestra EN VIVO lo que AIDEN percibe y piensa:
# tu foco, tu estado, tus metas, los últimos eventos y su lectura de tu momento. Se refresca sola.
#
# Resuelve la queja de Marco de "no se nota en pantalla": todo el trabajo de fondo (Estado_Del_Mundo,
# metas, reflexión) ahora se VE. Es PySide6 (tkinter está prohibido). Aislado: si algo falla, no toca
# la app principal. Debe crearse en el HILO de Qt (lo hace Main_AlwaysOn tras crear la QApplication).

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication

# ── Parámetros ajustables ─────────────────────────────────────────────────────
ANCHO, ALTO = 340, 230
MARGEN = 20
REFRESCO_MS = 3000
_MAX_EVENTOS = 3


def _estado():
    try:
        from Nucleo_Slide.Estado_Del_Mundo import obtener
        return obtener() or {}
    except Exception:
        return {}


def _reflexion_corta():
    try:
        from Nucleo_Slide.Reflexion import reflexion_texto
        t = (reflexion_texto() or "").replace("\n", " ").strip()
        return (t[:140] + "…") if len(t) > 140 else t
    except Exception:
        return ""


def _construir_html():
    est = _estado()
    foco = est.get("foco_actual") or "—"
    partes = [
        "<div style='font-size:13px;font-weight:bold;color:#00ffcc;letter-spacing:1px;'>◆ AIDEN</div>",
        f"<div style='color:#9fb3c8;font-size:11px;margin-top:4px;'>Foco: "
        f"<span style='color:#e6eef7;'>{_esc(foco)[:38]}</span></div>",
    ]

    chips = []
    if not est.get("marco_presente", True):
        chips.append("ausente")
    if est.get("en_reunion"):
        chips.append("reunión")
    if est.get("modo") and est.get("modo") != "normal":
        chips.append(est["modo"])
    if chips:
        partes.append(f"<div style='color:#ffb454;font-size:11px;'>Estado: {_esc(', '.join(chips))}</div>")

    metas = [m.get("texto", "") for m in (est.get("metas") or []) if m.get("estado") != "hecha"][:2]
    if metas:
        partes.append("<div style='color:#9fb3c8;font-size:11px;margin-top:4px;'>Metas:</div>")
        for m in metas:
            partes.append(f"<div style='color:#c3f0e0;font-size:11px;'>· {_esc(m)[:40]}</div>")

    evs = (est.get("eventos") or [])[-_MAX_EVENTOS:]
    if evs:
        partes.append("<div style='color:#9fb3c8;font-size:11px;margin-top:4px;'>Reciente:</div>")
        for e in reversed(evs):
            partes.append(
                f"<div style='color:#aebfcf;font-size:10px;'>· [{_esc(e.get('hora',''))}] "
                f"{_esc(e.get('texto',''))[:42]}</div>"
            )

    refl = _reflexion_corta()
    if refl:
        partes.append(
            f"<div style='color:#7d8ea0;font-size:10px;font-style:italic;margin-top:5px;'>“{_esc(refl)}”</div>"
        )
    return "".join(partes)


def _esc(t):
    return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class OverlayJarvis(QWidget):
    def __init__(self):
        super().__init__()
        # Sin marco, siempre encima, fuera de la barra de tareas, y SIN robar el foco/los clics.
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._label = QLabel("")
        self._label.setTextFormat(Qt.RichText)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.addWidget(self._label)

        self.setStyleSheet(
            "QWidget { background: rgba(8,12,20,205); border: 1px solid rgba(0,255,204,60);"
            " border-radius: 12px; }"
        )
        self.resize(ANCHO, ALTO)
        self._reposicionar()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refrescar)
        self._timer.start(REFRESCO_MS)
        self._refrescar()

    def _reposicionar(self):
        try:
            geo = QGuiApplication.primaryScreen().availableGeometry()
            self.move(geo.right() - self.width() - MARGEN, geo.bottom() - self.height() - MARGEN)
        except Exception:
            pass

    def _refrescar(self):
        try:
            self._label.setText(_construir_html())
        except Exception:
            pass


def crear_overlay():
    # Crea, muestra y DEVUELVE el overlay (hay que llamarlo dentro del hilo de Qt). None si falla.
    try:
        ov = OverlayJarvis()
        ov.show()
        return ov
    except Exception as e:
        print(f"[overlay] no se pudo crear: {e}")
        return None
