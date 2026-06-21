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
   segmentos,_ = _asegurar_modelo().transcribe("archivo_temporal_voz.wav", language = "es")
   texto = "".join([s.text for s in segmentos]).strip()
   print(f"⏱  Transcripcion (Whisper) : {time.perf_counter() - _t0:5.2f} s")
   return texto
  else:
    print("No se capturo audio...")


 except sr.WaitTimeoutError:
   print("Paso mucho tiempo y no dijiste nada, volviendo a esperar...")
   return None

 except Exception as e:
    print(f"Error detectado: {e}") 


  
    
   


