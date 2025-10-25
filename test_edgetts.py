import edge_tts
import asyncio
import os

async def test_edgetts():
    """Test EdgeTTS pour vérifier qu'il fonctionne correctement"""
    try:
        text = "Bonjour, ceci est un test de synthèse vocale avec EdgeTTS version 7.2.3"
        voice = "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)"
        
        print(f"Test EdgeTTS avec le texte: {text}")
        print(f"Voix utilisée: {voice}")
        
        comm = edge_tts.Communicate(text, voice)
        await comm.save('test_audio_local.mp3')
        
        # Vérifier que le fichier a été créé
        if os.path.exists('test_audio_local.mp3'):
            file_size = os.path.getsize('test_audio_local.mp3')
            print(f"✅ EdgeTTS fonctionne correctement!")
            print(f"Fichier créé: test_audio_local.mp3 ({file_size} bytes)")
            return True
        else:
            print("❌ Erreur: Fichier audio non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur EdgeTTS: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_edgetts())
    if result:
        print("\n🎉 EdgeTTS version 7.2.3 fonctionne parfaitement en local!")
    else:
        print("\n💥 Problème avec EdgeTTS en local")