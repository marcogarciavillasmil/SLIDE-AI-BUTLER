import cv2
import os
import time
import threading
from datetime import datetime
import face_recognition

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CARPETA = os.path.join(_BASE, "Vigilancia")
_FOTO_MARCO = os.path.join(_BASE, "Imagenes", "Marco.jpg")

_lock = threading.Lock()
_camara = {"frame": None}
_estado = {"presente": False, "visto": 0.0, "ultimo_intruso": 0.0}


def ultimo_frame():
    with _lock:
        f = _camara["frame"]
    return f.copy() if f is not None else None


def _ref_marco():
    if not os.path.exists(_FOTO_MARCO):
        return None
    img = face_recognition.load_image_file(_FOTO_MARCO)
    locs = face_recognition.face_locations(img)
    if not locs:
        return None
    return face_recognition.face_encodings(img, known_face_locations=[locs[0]])[0]


def _guardar_intruso(frame):
    if not os.path.exists(_CARPETA):
        os.makedirs(_CARPETA)
    nombre = datetime.now().strftime("intruso_%Y-%m-%d_%H-%M-%S.jpg")
    cv2.imwrite(os.path.join(_CARPETA, nombre), frame)


def _bucle(ref, hablar):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        return
    ultimo_chequeo = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.5)
            continue
        with _lock:
            _camara["frame"] = frame
        ahora = time.time()
        if ahora - ultimo_chequeo < 3:
            time.sleep(0.05)
            continue
        ultimo_chequeo = ahora
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        chico = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)
        locs = face_recognition.face_locations(chico)
        if not locs:
            if _estado["presente"] and ahora - _estado["visto"] > 25:
                _estado["presente"] = False
            continue
        encs = face_recognition.face_encodings(chico, known_face_locations=locs)
        es_marco = any(face_recognition.compare_faces([ref], e, tolerance=0.6)[0] for e in encs)
        if es_marco:
            _estado["visto"] = ahora
            if not _estado["presente"]:
                _estado["presente"] = True
                hablar("Bienvenido de nuevo, Marco.")
        else:
            if ahora - _estado["ultimo_intruso"] > 30:
                _estado["ultimo_intruso"] = ahora
                _guardar_intruso(frame)
                hablar("Señor, detecté una persona no reconocida. Guardé una captura en la carpeta de vigilancia.")


def iniciar_vigilancia(hablar):
    ref = _ref_marco()
    if ref is None:
        return
    _estado["presente"] = True
    _estado["visto"] = time.time()
    threading.Thread(target=_bucle, args=(ref, hablar), daemon=True).start()
