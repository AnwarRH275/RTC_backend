#!/usr/bin/env python3
import asyncio
import edge_tts
import os

async def test_edgetts():
    """Test EdgeTTS avec différents paramètres"""
    
    # Texte de test simple
    text = "Bonjour, ceci est un test de synthèse vocale."
    
    # Voix française par défaut
    voice = "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)"
    
    print(f"Test EdgeTTS avec:")
    print(f"- Texte: {text}")
    print(f"- Voix: {voice}")
    
    try:
        # Créer le répertoire de sortie s'il n'existe pas
        output_dir = "audio_responses"
        os.makedirs(output_dir, exist_ok=True)
        
        # Nom du fichier de sortie
        output_file = os.path.join(output_dir, "test_edgetts.mp3")
        
        print(f"- Fichier de sortie: {output_file}")
        
        # Créer l'objet Communicate
        communicate = edge_tts.Communicate(text, voice)
        
        print("Génération de l'audio en cours...")
        
        # Sauvegarder l'audio
        await communicate.save(output_file)
        
        # Vérifier si le fichier a été créé
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Succès! Fichier créé: {output_file}")
            print(f"   Taille: {file_size} bytes")
            
            if file_size == 0:
                print("❌ Erreur: Le fichier audio est vide!")
                return False
            else:
                print("✅ Le fichier audio contient des données.")
                return True
        else:
            print("❌ Erreur: Le fichier audio n'a pas été créé!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la synthèse: {str(e)}")
        return False

async def test_voice_list():
    """Test pour lister les voix disponibles"""
    print("\n--- Test des voix disponibles ---")
    try:
        voices = await edge_tts.list_voices()
        french_voices = [v for v in voices if 'fr-FR' in v['Locale']]
        
        print(f"Nombre total de voix: {len(voices)}")
        print(f"Voix françaises disponibles: {len(french_voices)}")
        
        for voice in french_voices[:5]:  # Afficher les 5 premières voix françaises
            print(f"  - {voice['Name']} ({voice['Gender']})")
            
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des voix: {str(e)}")
        return False

async def main():
    print("=== Test EdgeTTS ===\n")
    
    # Test 1: Lister les voix
    await test_voice_list()
    
    # Test 2: Synthèse vocale
    print("\n--- Test de synthèse vocale ---")
    success = await test_edgetts()
    
    if success:
        print("\n✅ Tous les tests EdgeTTS ont réussi!")
    else:
        print("\n❌ Les tests EdgeTTS ont échoué!")

if __name__ == "__main__":
    asyncio.run(main())