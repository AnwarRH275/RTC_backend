#!/usr/bin/env python3
"""
Script de test pour EdgeTTS - Vérification des voix disponibles et test de synthèse
"""

import asyncio
import edge_tts
import os

async def list_voices():
    """Liste toutes les voix françaises disponibles"""
    print("=== Voix françaises disponibles dans EdgeTTS ===")
    voices = await edge_tts.list_voices()
    french_voices = [v for v in voices if v["Locale"].startswith("fr-")]
    
    for voice in french_voices:
        # Utiliser les clés disponibles dans la structure de données
        name = voice.get('Name', voice.get('ShortName', 'Unknown'))
        gender = voice.get('Gender', 'Unknown')
        locale = voice.get('Locale', 'Unknown')
        print(f"- {name} ({gender}) - Locale: {locale}")
    
    return french_voices

async def test_voice(voice_name, text="Bonjour, ceci est un test de synthèse vocale."):
    """Teste une voix spécifique"""
    print(f"\n=== Test de la voix: {voice_name} ===")
    
    try:
        communicate = edge_tts.Communicate(text, voice_name)
        output_file = f"test_{voice_name.replace('-', '_')}.mp3"
        
        await communicate.save(output_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Succès! Fichier créé: {output_file} ({file_size} octets)")
            
            # Nettoyer le fichier de test
            os.remove(output_file)
            return True
        else:
            print(f"❌ Échec: Fichier non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

async def main():
    """Fonction principale"""
    print("EdgeTTS - Test des voix françaises\n")
    
    # Lister les voix disponibles
    french_voices = await list_voices()
    
    # Tester quelques voix courantes
    test_voices = [
        "fr-FR-DeniseNeural",
        "fr-FR-HenriNeural", 
        "fr-CA-AntoineNeural",
        "fr-CA-JeanNeural"
    ]
    
    print(f"\n=== Test de {len(test_voices)} voix ===")
    
    results = {}
    for voice in test_voices:
        results[voice] = await test_voice(voice)
    
    # Résumé des résultats
    print(f"\n=== Résumé des tests ===")
    for voice, success in results.items():
        status = "✅ OK" if success else "❌ ÉCHEC"
        print(f"{voice}: {status}")
    
    # Recommandation
    working_voices = [v for v, success in results.items() if success]
    if working_voices:
        print(f"\n🎯 Voix recommandées: {', '.join(working_voices)}")
    else:
        print(f"\n⚠️  Aucune voix testée ne fonctionne!")

if __name__ == "__main__":
    asyncio.run(main())