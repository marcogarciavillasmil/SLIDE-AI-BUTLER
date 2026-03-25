import torch
from collections import deque
import numpy as np
from Transcriptor import escuchador_de_usuario
from faster_whisper import WhisperModel
import pyaudio
from Herramientas_del_asistente import buscar_microfono
import time
from Herramientas_del_asistente import hablado_del_asistente

palabras = ["DESPIERTA","SLIDE","SLIGHT","OYE","ACTIVATE","PAPA ESTA EN CASA","TE NECESITO","PAPA ESTA EN CAZA"]

microfono =  buscar_microfono()
print(microfono)

modelo, herramientas = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', source="github")


segundos = 25
tiempo_despierto = 0


(tiempo_de_habla,_,_,_,_) = herramientas
asistente_despierto = False

memoria_de_audio = deque(maxlen=100)

#Whisper  pero rapido y pyaudio

modelo_rapido = WhisperModel("small",device="cpu",compute_type="int8")

Formato=pyaudio.paInt16
Muestreo=16000
Canales=1
Chunk=512 

pyaudio_=pyaudio.PyAudio()

stream = pyaudio_.open(format=Formato,channels=Canales,rate=Muestreo,input=True,frames_per_buffer=Chunk,input_device_index=microfono)

print("termino la configuracion")

def quitar_tildes_simple(texto):
    reemplazos = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return texto.translate(reemplazos)

def Reconocimiento_de_habla():

    if stream.is_stopped():
       stream.start_stream()



    global tiempo_despierto
    global asistente_despierto
    while True:
      while stream.get_read_available() > Chunk:
        data = stream.read(Chunk,exception_on_overflow=False)

      tiempo_inicial = time.time()
      data = stream.read(Chunk,exception_on_overflow=False)
     

      chunk_numpy = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0 #Ahi se convierten datos a numpy
      torch_datos = torch.from_numpy(chunk_numpy)# aqui a torch, q es un lenguaje que las IAS entienden 
 
      probabilidad = modelo(torch_datos,16000).item()
      Tiempo_total = tiempo_inicial - tiempo_despierto

      if probabilidad > 0.6:
        memoria_de_audio.append(chunk_numpy)
      else:
        if len(memoria_de_audio) > 10:
            print("fin frase")
            frase_completa = np.concatenate(list(memoria_de_audio))
            


            segmentos,_ = modelo_rapido.transcribe(frase_completa,language="es",beam_size=5)
            texto = "".join([s.text for s in segmentos]).strip()#aqui como modelo_rapido devuelve muchas cosas, nos enfocamos en solo texto con " s.text" para despues pegar con el join todas las frases
            #que tengan ""
            texto = texto.upper()
            texto_limpio = quitar_tildes_simple(texto)
            print(texto_limpio)

            memoria_de_audio.clear()

            if asistente_despierto == True and Tiempo_total < segundos:
                tiempo_despierto = time.time()
                stream.stop_stream()
               
                return True, texto_limpio
            elif any(i in texto_limpio for i in palabras):
                tiempo_despierto = time.time()
                asistente_despierto=True
                stream.stop_stream()
                hablado_del_asistente("A su servicio señor")
                return True, texto_limpio

                

            



            