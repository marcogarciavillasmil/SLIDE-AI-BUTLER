# Activación por presencia: AIDEN te saluda cuando LLEGAS al PC, sin que digas nada.
#
# Diseño ANTI-MOLESTIA (clave para que no canse):
#   1. Solo te saluda a TI: reconoce tu cara (Imagenes/Marco.jpg); ignora a otros.
#   2. Solo en la transición ausente->presente, y tras una ausencia REAL (AUSENCIA_MINIMA).
#      Si solo te volteas un momento, NO re-saluda.
#   3. Cooldown global: máximo 1 saludo cada COOLDOWN segundos.
#   4. Requiere verte en VERIFICACIONES chequeos seguidos (evita falsos positivos).
#   5. NO abre el micrófono ni inicia conversación: solo un saludo corto y variado.
#   6. Se PAUSA en modo gaming y fuera de la franja HORA_INICIO–HORA_FIN (nada de madrugada).
#
# Además NO deja la cámara prendida: la abre un instante cada INTERVALO seg y la cierra.
# Todos los parámetros de abajo se pueden ajustar a gusto.

import os
import random
import threading
import time
from datetime import datetime

import cv2
import face_recognition

# ── Parámetros ajustables ────────────────────────────────────────────────────
INTERVALO = 25            # cada cuántos seg revisa la cámara (súbelo si el LED molesta)
AUSENCIA_MINIMA = 8 * 60  # seg fuera para que tu regreso cuente como una "llegada"
COOLDOWN = 30 * 60        # seg mínimos entre saludos, pase lo que pase
VERIFICACIONES = 2        # chequeos seguidos viéndote para confirmar "presente"
HORA_INICIO = 7           # solo saluda dentro de esta franja horaria...
HORA_FIN = 23             # ...(nada de madrugada)
TOLERANCIA = 0.5          # estrictez del reconocimiento facial (menor = más estricto)

_SALUDOS = [
    "Bienvenido de vuelta, señor.",
    "Por aquí de nuevo, señor. A su servicio.",
    "Lo estaba esperando, señor.",
    "De regreso al puesto de mando, señor.",
    "Un placer tenerlo de vuelta, señor.",
]

_pausado = False
_ultimo_saludo = 0           # timestamp del último saludo (para el cooldown)
_ultima_vez_visto = 0        # timestamp de la última vez que se te vio
_chequeos_seguidos = 0       # detecciones consecutivas en la visita actual
_saludado_esta_visita = True # arranca True para no saludar apenas inicia (ya hiciste login)
_ref = None                  # vector de tu cara (se calcula una vez)


def pausar_presencia(pausar=True):
    # Silencia la presencia (lo usa el modo gaming).
    global _pausado
    _pausado = bool(pausar)


def _cargar_referencia():
    # Calcula el "vector" de la cara de Marco desde Imagenes/Marco.jpg, una sola vez.
    global _ref
    if _ref is not None:
        return _ref
    try:
        ruta = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "Imagenes", "Marco.jpg",
        )
        img = face_recognition.load_image_file(ruta)
        locs = face_recognition.face_locations(img)
        if not locs:
            return None
        _ref = face_recognition.face_encodings(img, known_face_locations=[locs[0]])[0]
        return _ref
    except Exception:
        return None


def _marco_en_camara():
    # Abre la cámara un instante, toma un frame y devuelve True si ve la cara de Marco.
    ref = _cargar_referencia()
    if ref is None:
        return False
    cam = None
    try:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cam.isOpened():
            return False                # cámara ocupada (p.ej. una tool de visión): saltar ciclo
        frame = None
        for _ in range(4):              # descarta los primeros frames (cámara "fría")
            ok, f = cam.read()
            if ok:
                frame = f
        if frame is None:
            return False
        pequeno = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)   # reducir acelera el reconocimiento
        rgb = cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        if not locs:
            return False
        encs = face_recognition.face_encodings(rgb, known_face_locations=locs)
        for e in encs:
            if face_recognition.compare_faces([ref], e, tolerance=TOLERANCIA)[0]:
                return True
        return False
    except Exception:
        return False
    finally:
        if cam is not None:
            cam.release()


def _revisar(hablar):
    global _ultimo_saludo, _ultima_vez_visto, _chequeos_seguidos, _saludado_esta_visita
    if _pausado:
        return
    if not (HORA_INICIO <= datetime.now().hour < HORA_FIN):
        return

    if not _marco_en_camara():
        _chequeos_seguidos = 0          # no te veo: el hueco de ausencia crecerá
        return

    ahora = time.time()
    hueco = ahora - _ultima_vez_visto   # cuánto llevabas sin que te vieran
    _ultima_vez_visto = ahora

    if hueco >= AUSENCIA_MINIMA:
        # Acabas de LLEGAR tras una ausencia real -> empieza una visita nueva.
        _chequeos_seguidos = 1
        _saludado_esta_visita = False
    else:
        _chequeos_seguidos += 1

    if (not _saludado_esta_visita
            and _chequeos_seguidos >= VERIFICACIONES
            and (ahora - _ultimo_saludo) >= COOLDOWN):
        _saludado_esta_visita = True
        _ultimo_saludo = ahora
        hablar(random.choice(_SALUDOS))


def iniciar_presencia(hablar):
    # Arranca el bucle de presencia en segundo plano.
    def _bucle():
        global _ultima_vez_visto
        time.sleep(90)                  # deja pasar el briefing y el arranque
        _ultima_vez_visto = time.time() # acabas de hacer login: ya estás presente, no saludes de una
        while True:
            try:
                _revisar(hablar)
            except Exception:
                pass
            time.sleep(INTERVALO)

    threading.Thread(target=_bucle, daemon=True).start()
