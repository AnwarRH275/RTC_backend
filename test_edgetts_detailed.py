#!/usr/bin/env python3
"""Script de test détaillé pour EdgeTTS"""
import asyncio
import edge_tts
import os

async def test_voice(voice, text):
    """Test une voix spécifique"""
    output_file = f"test_{voice.replace('/', '_')}.mp3"
    
    try:
        print(f"\nTest avec {voice}...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size > 0:
                print(f"  ✓ Succès ({file_size} bytes)")
                os.remove(output_file)
                return True
            else:
                print(f"  ✗ Fichier vide")
                os.remove(output_file)
                return False
        else:
            print(f"  ✗ Fichier non créé")
            return False
            
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return False

async def list_voices():
    """Liste toutes les voix françaises disponibles"""
    try:
        print("Récupération de la liste des voix...")
        voices = await edge_tts.list_voices()
        french_voices = [v for v in voices if v["Locale"].startswith("fr-")]
        
        print(f"\nVoix françaises disponibles ({len(french_voices)}):")
        for v in french_voices[:10]:  # Limiter à 10
            print(f"  - {v['ShortName']} ({v['Locale']}) - {v['Gender']}")
        
        return french_voices
    except Exception as e:
        print(f"Erreur lors de la récupération des voix: {e}")
        return []

async def main():
    """Test principal"""
    text = "Bonjour, ceci est un test."
    
    # Tester la liste des voix
    voices = await list_voices()
    
    if voices:
        # Tester quelques voix
        print("\n=== Tests de synthèse ===")
        for voice_info in voices[:3]:
            await test_voice(voice_info['ShortName'], text)
    else:
        print("\nImpossible de récupérer la liste des voix. Test avec des voix connues...")
        test_voices = ["fr-FR-HenriNeural", "fr-FR-DeniseNeural"]
        for voice in test_voices:
            await test_voice(voice, text)

if __name__ == "__main__":
    asyncio.run(main())
