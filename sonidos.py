# Efectos del teaser con ElevenLabs (/v1/sound-generation; la clave la pone el proxy). Uso: python3 sonidos.py [nombre ...]
import json, os, sys, urllib.request
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sonidos'); os.makedirs(DIR, exist_ok=True)
EFECTOS = {
    'ambiente': ('quiet modern bathroom room tone, very soft low cinematic drone, premium product commercial', 3.5),
    'barrido': ('subtle airy cinematic whoosh, light sweeping across glossy surface, premium product reveal', 1.2),
    'encendido': ('soft elegant digital chime, smart device display turning on, clean high-end UI sound', 1.0),
    'pasos': ('soft footsteps walking slowly into a quiet bathroom on tile floor, indoor, morning, close mic', 2.5),
    'clic': ('small soft plastic button click, premium device, close up, single click', 0.5),
    'conector': ('usb-c cable plugging into a device, small satisfying click, close up', 0.7),
    'pegado': ('soft muffled thud of a small device pressed against a wall, gentle click, satisfying', 0.8),
    'apagado': ('soft descending electronic tone, smart device screen turning off, subtle', 0.8),
    'espuma': ('soft foam soap dispenser pump, gentle airy squish of thick foam coming out, close up', 1.2),
}
if 'musica' in sys.argv[1:]:          # música del anuncio (/v1/music)
    pet = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', method='POST',
        data=json.dumps({'prompt': 'modern minimal lifestyle product commercial music, warm soft house beat with plucks and airy pads, clean, '
                         'positive, morning bathroom routine, steady 110 bpm, subtle build and satisfying ending, no vocals',
                         'music_length_ms': 20000, 'force_instrumental': True}).encode(),
        headers={'xi-api-key': os.environ.get('ELEVENLABS_API_KEY', 'proxy'), 'Content-Type': 'application/json'})
    with urllib.request.urlopen(pet, timeout=300) as r: open(os.path.join(DIR, 'musica.mp3'), 'wb').write(r.read())
    print('musica ok', flush=True); sys.argv.remove('musica')
    if len(sys.argv) == 1: sys.exit()
for n in sys.argv[1:] or EFECTOS:
    t, s = EFECTOS[n]
    pet = urllib.request.Request('https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128',
        data=json.dumps({'text': t, 'duration_seconds': s, 'prompt_influence': 0.55}).encode(), method='POST',
        headers={'xi-api-key': os.environ.get('ELEVENLABS_API_KEY', 'proxy'), 'Content-Type': 'application/json'})
    with urllib.request.urlopen(pet, timeout=300) as r: open(os.path.join(DIR, n + '.mp3'), 'wb').write(r.read())
    print(n, 'ok', flush=True)
