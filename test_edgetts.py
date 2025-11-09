#!/usr/bin/env python3
"""Script de test pour EdgeTTS"""
import asyncio
import edge_tts
import os

async def test_edgetts():
    """Test simple de EdgeTTS"""
    text = "Bonjour, ceci est un test de synthèse vocale."
    voice = "fr-FR-HenriNeural"
    output_file = "test_audio.mp3"
    
    try:
        print(f"Test de synthèse avec la voix {voice}...")
        print(f"Texte: {text}")
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ Fichier créé: {output_file} ({file_size} bytes)")
            
            if file_size > 0:
                print("✓ Le fichier contient des données")
                # Nettoyer
                os.remove(output_file)
                return True
            else:
                print("✗ Le fichier est vide!")
                os.remove(output_file)
                return False
        else:
            print("✗ Le fichier n'a pas été créé")
            return False
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_edgetts())
    if result:
        print("\n✓ Test réussi!")
    else:
        print("\n✗ Test échoué!")
