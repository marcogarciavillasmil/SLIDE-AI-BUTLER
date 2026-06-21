import sounddevice as sd, numpy as np

tono = (np.sin(2*np.pi*440*np.arange(44100)/44100)*0.5).astype('float32')
devs = sd.query_devices()

print("=== Probando dispositivos de salida ===")
for i, d in enumerate(devs):
    if d['max_output_channels'] < 1:
        continue
    nombre = d['name']
    try:
        sd.play(tono, 44100, device=i, blocking=True)
        print(f"[{i}] {nombre[:45]} -> FUNCIONO")
    except Exception as e:
        print(f"[{i}] {nombre[:45]} -> fallo")

print("\nDefault output:", sd.default.device[1])