import os as os
import speech_recognition as sr
import time
from Voz_Slide.Herramientas_del_asistente import buscar_microfono, marcar_fin_peticion
from faster_whisper import WhisperModel





instancia = sr.Recognizer()
instancia.pause_threshold = 2
print("Cargando Modelo...")
model = WhisperModel("small", device="cuda", compute_type="int8_float16")


def _asegurar_modelo():
    # Recarga el Whisper de voz si fue descargado (p. ej. en modo gaming).
    global model
    if model is None:
        print("Recargando Whisper (voz)...")
        model = WhisperModel("small", device="cuda", compute_type="int8_float16")
    return model


def descargar_modelo_voz():
    # Libera el Whisper de la GPU para soltar VRAM (modo gaming).
    global model
    model = None
    try:
        import gc
        gc.collect()
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass


def recargar_modelo_voz():
    # Vuelve a dejar el Whisper listo en la GPU.
    _asegurar_modelo()


microfono_encontrado = buscar_microfono()
_calibrado = False


# --- Guardia anti-alucinaciones de Whisper ---------------------------------
# Cuando Whisper recibe SILENCIO o ruido (un suspiro, el ventilador, la calle) tiende a
# "inventar" frases que vio miles de veces en subtitulos de YouTube. Estas son las mas
# famosas en espanol. Si la transcripcion es SOLO una de estas, NO es un comando real.
_ALUCINACIONES = (
    "subtitulos realizados por la comunidad de amara.org",
    "subtitulos por la comunidad de amara.org",
    "subtitulado por la comunidad de amara.org",
    "mas informacion www.amara.org",
    "amara.org",
    "subtitulos por subtitulamos.tv",
    "gracias por ver el video",
    "gracias por ver el vídeo",
    "gracias por ver este video",
    "no olvides suscribirte",
    "suscribete al canal",
    "dale like y suscribete",
)
# Frases cortas que SOLO son alucinacion si vienen solas (texto completo == esto).
_ALUCINACIONES_EXACTAS = (
    "suscribete", "¡suscribete!", "gracias", "¡gracias!", "gracias.", "subtitulos",
)


def es_alucinacion(texto):
    """True si el texto transcrito es una alucinacion tipica de Whisper sobre silencio/ruido."""
    if not texto:
        return True
    limpio = texto.strip().lower()
    limpio = limpio.translate(str.maketrans("áéíóúü", "aeiouu"))
    if not limpio:
        return True
    if limpio in _ALUCINACIONES_EXACTAS:
        return True
    return any(frase in limpio for frase in _ALUCINACIONES)


def escuchador_de_usuario(timeout=15):
 global _calibrado
 try:

  with sr.Microphone(device_index=microfono_encontrado) as source:
    if not _calibrado:
        print("Calibrando microfono (solo la primera vez)...")
        instancia.adjust_for_ambient_noise(source, duration=0.5)
        _calibrado = True
    print("Escuchandote....")
    audio_capturar = instancia.listen(source, phrase_time_limit=50, timeout=timeout)
    marcar_fin_peticion()   # terminaste de hablar -> arranca el cronometro de respuesta
    print("Fin de la conversacion, procesando...")
  if audio_capturar is not None: 
   with open("archivo_temporal_voz.wav","wb") as x:
     x.write(audio_capturar.get_wav_data())
    
   _t0 = time.perf_counter()
   # vad_filter: el Silero interno de faster-whisper descarta el audio SIN voz antes de
   # transcribir -> mata casi todas las alucinaciones de silencio.
   # condition_on_previous_text=False: evita que arrastre/repita texto fantasma.
   segmentos,_ = _asegurar_modelo().transcribe(
       "archivo_temporal_voz.wav", language="es",
       vad_filter=True, condition_on_previous_text=False,
   )
   texto = "".join([s.text for s in segmentos]).strip()
   print(f"⏱  Transcripcion (Whisper) : {time.perf_counter() - _t0:5.2f} s")
   if es_alucinacion(texto):
       print(f"🛇 Alucinacion descartada: {texto!r}")
       return None
   return texto
  else:
    print("No se capturo audio...")


 except sr.WaitTimeoutError:
   print("Paso mucho tiempo y no dijiste nada, volviendo a esperar...")
   return None

 except Exception as e:
    print(f"Error detectado: {e}") 


  
    
   


