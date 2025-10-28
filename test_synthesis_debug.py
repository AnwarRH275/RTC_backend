#!/usr/bin/env python3
import asyncio
import edge_tts
import os
import uuid
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def synthesize_with_edgetts_debug(text: str, voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)", session_id: str = None) -> str:
    """Version debug de la fonction synthesize_with_edgetts"""
    
    print(f"=== DEBUG synthesize_with_edgetts ===")
    print(f"Texte reçu: '{text}'")
    print(f"Longueur du texte: {len(text)}")
    print(f"Voix: {voice}")
    print(f"Session ID: {session_id}")
    
    # Vérifier si le texte est vide ou ne contient que des espaces
    if not text or not text.strip():
        print("❌ ERREUR: Texte vide ou ne contient que des espaces!")
        return ""
    
    if session_id:
        audio_filename = f"response_{session_id}_{uuid.uuid4()}.mp3"
    else:
        audio_filename = f"response_{uuid.uuid4()}.mp3"
    
    print(f"Nom du fichier audio: {audio_filename}")
    
    # Créer le dossier audio_responses dans le répertoire backend
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audio_dir = os.path.join(backend_dir, "audio_responses")
    print(f"Répertoire backend: {backend_dir}")
    print(f"Répertoire audio: {audio_dir}")
    
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, audio_filename)
    print(f"Chemin complet du fichier: {audio_path}")

    try:
        print("Création de l'objet Communicate...")
        communicate = edge_tts.Communicate(text, voice)
        
        print("Sauvegarde de l'audio...")
        await communicate.save(audio_path)
        
        # Vérifier si le fichier a été créé et sa taille
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Fichier créé avec succès: {audio_path}")
            print(f"   Taille: {file_size} bytes")
            
            if file_size == 0:
                print("❌ ERREUR: Le fichier audio est vide!")
                logger.error("Erreur lors de la synthèse vocale avec EdgeTTS: No audio was received. Please verify that your parameters are correct.")
                return ""
            else:
                logger.info(f"Audio généré avec EdgeTTS: {audio_filename}")
                return audio_filename
        else:
            print("❌ ERREUR: Le fichier n'a pas été créé!")
            logger.error("Erreur lors de la synthèse vocale avec EdgeTTS: No audio was received. Please verify that your parameters are correct.")
            return ""
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        logger.error(f"Erreur lors de la synthèse vocale avec EdgeTTS: {e}")
        return ""

def process_text_with_groq_mock(text: str) -> str:
    """Version mock de process_text_with_groq pour les tests"""
    print(f"=== MOCK process_text_with_groq ===")
    print(f"Texte d'entrée: '{text}'")
    
    # Simuler le traitement Groq - retourner le texte tel quel pour le test
    processed = text.strip()
    print(f"Texte traité: '{processed}'")
    return processed

async def test_synthesis_flow():
    """Test du flux complet de synthèse"""
    print("=== Test du flux complet de synthèse ===\n")
    
    # Test avec différents types de texte
    test_cases = [
        "Bonjour, ceci est un test simple.",
        "   Texte avec espaces au début et à la fin   ",
        "",
        "   ",
        "Texte avec des caractères spéciaux: éàùç!",
        "Texte très long: " + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Texte original: '{test_text}'")
        
        # Simuler le traitement Groq
        processed_text = process_text_with_groq_mock(test_text)
        
        # Tester la synthèse
        result = await synthesize_with_edgetts_debug(processed_text, session_id=f"test_{i}")
        
        if result:
            print(f"✅ Test {i} réussi: {result}")
        else:
            print(f"❌ Test {i} échoué")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_synthesis_flow())