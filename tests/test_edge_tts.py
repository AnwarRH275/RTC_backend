import os
import asyncio
import time

# Ajuster le chemin pour importer synthesis
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
SERVICES_DIR = os.path.join(BACKEND_DIR, 'services', 'exam')
import sys
sys.path.insert(0, SERVICES_DIR)

from synthesis import synthesize_with_edgetts
import edge_tts


def test_synthesize_with_edgetts_basic():
    text = "Bonjour, ceci est un test de voix Edge TTS HenriNeural."
    session_id = f"test_{int(time.time())}"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    filename = loop.run_until_complete(
        synthesize_with_edgetts(text, session_id=session_id)
    )
    loop.close()

    assert filename and filename.endswith('.mp3'), "Le fichier audio devrait être généré"

    audio_dir = os.path.join(BACKEND_DIR, 'audio_responses')
    path = os.path.join(audio_dir, filename)
    assert os.path.exists(path), "Le fichier audio devrait exister"
    assert os.path.getsize(path) > 0, "Le fichier audio ne doit pas être vide"


def test_list_voices_edge_fr():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    voices = loop.run_until_complete(edge_tts.list_voices())
    loop.close()
    fr_voices = [v for v in voices if v.get('Locale', '').lower().startswith('fr')]
    assert len(fr_voices) > 0, "Il devrait y avoir des voix françaises disponibles"


if __name__ == '__main__':
    # Exécution simple
    test_synthesize_with_edgetts_basic()
    test_list_voices_edge_fr()
    print("Tests EdgeTTS passés.")