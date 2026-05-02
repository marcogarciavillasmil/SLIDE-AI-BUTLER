import speech_recognition as sr
import sys
from kokoro import KPipeline as pipe
import sounddevice as sound 

def buscar_microfono():
    microfonos = sr.Microphone.list_microphone_names()
    for i, nombre in enumerate(microfonos):
        nombre_minuscula = nombre.lower()
        if "microphone" in nombre_minuscula or "realtek" in nombre_minuscula or "high definition" in nombre_minuscula:
            return i  
    
    print("No se encontro microfono")
    return None
 

#ESTE ES EL MOTOR CON LAS REGLAS DE COMO SE PRONUNCIAN LAS COSAS COMO LETRAS Y COMO DEBEN SONAR 

pipeline = pipe(lang_code='es')

voz1= pipeline.load_voice('em_santa')
voz2= pipeline.load_voice('af_bella')
voz3= pipeline.load_voice('jf_alpha')
voz_mezclada = (voz1*0.45)+(voz3*0.55)



def hablado_del_asistente(texto_final):
#este es el comando para usar el kokoro, se define el texto_final que es el que se pasa a audio, la voz y la velocidad, 1 es velocidad humana
    frases = texto_final.split(".")
   
    for frase in frases:
        frase = frase.strip()
        if not frase:
            continue
        generador = pipeline(frase + ".",voice=voz_mezclada,speed=1)


#bucle que recorre parte a parte el audio
        for gs, ps, audio in generador: 
         sound.play(audio,24000)
         sound.wait()






