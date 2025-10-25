#!/usr/bin/env python3
"""
Petit script de test pour EdgeTTS.
Génère un fichier MP3 dans backend/audio_responses/test_edge_tts.mp3
Usage:
  python services/exam/edgetts_smoke_test.py "Texte à dire" [ShortName de la voix]
Exemple:
  python services/exam/edgetts_smoke_test.py "Bonjour, ceci est un test." fr-FR-HenriNeural
"""
import os
import sys
import asyncio
import logging

import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def ensure_audio_dir() -> str:
    # /Users/.../backend/services/exam -> on remonte à .../backend
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audio_dir = os.path.join(backend_dir, "audio_responses")
    os.makedirs(audio_dir, exist_ok=True)
    return audio_dir


async def pick_voice(preferred: str | None = None) -> str:
    voices = await edge_tts.list_voices()
    if preferred and any(v.get("ShortName") == preferred for v in voices):
        return preferred
    fallbacks = ["fr-FR-HenriNeural", "fr-FR-DeniseNeural", "fr-FR-SylvieNeural"]
    for fb in fallbacks:
        if any(v.get("ShortName") == fb for v in voices):
            return fb
    fr_voice = next((v.get("ShortName") for v in voices if v.get("Locale") == "fr-FR"), None)
    return fr_voice or voices[0].get("ShortName")


async def main():
    text = "Bonjour, ceci est un test de synthèse vocale."
    preferred = None
    if len(sys.argv) > 1:
        text = sys.argv[1]
    if len(sys.argv) > 2:
        preferred = sys.argv[2]

    voice = await pick_voice(preferred)
    logging.info(f"Voix EdgeTTS utilisée: {voice}")

    audio_dir = ensure_audio_dir()
    out_path = os.path.join(audio_dir, "test_edge_tts.mp3")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

    print(out_path)


if __name__ == "__main__":
    asyncio.run(main())