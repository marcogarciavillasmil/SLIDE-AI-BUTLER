import whisper 
import os as os 
import speech_recognition as sr
import sys
from Herramientas_del_asistente import buscar_microfono
from faster_whisper import WhisperModel





instancia = sr.Recognizer()
instancia.pause_threshold = 2
print("Cargando Modelo...")
model = WhisperModel("medium",device="cpu",compute_type="int8")

microfono_encontrado = buscar_microfono()


def escuchador_de_usuario(): 
 try:

  with sr.Microphone(device_index=microfono_encontrado) as source:
    print("Ajustando parametros..., porfavor no hables")
    instancia.adjust_for_ambient_noise(source, duration=0.5)
    print("Escuchandote....")
    audio_capturar = instancia.listen(source, phrase_time_limit=50, timeout=5)
    print("Fin de la conversacion, procesando...")
  if audio_capturar is not None: 
   with open("archivo_temporal_voz.wav","wb") as x:
     x.write(audio_capturar.get_wav_data())
    
   segmentos,_ = model.transcribe("archivo_temporal_voz.wav", language = "es")
   texto = "".join([s.text for s in segmentos]).strip()
   return texto
  else:
    print("No se capturo audio...")


 except sr.WaitTimeoutError:
   print("Paso mucho tiempo y no dijiste nada, cerrando el programa....")
   sys.exit()

 except Exception as e:
    print(f"Error detectado: {e}") 
  
    
   


