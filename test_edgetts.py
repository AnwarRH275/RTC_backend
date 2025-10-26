#!/usr/bin/env python3
"""
Script de test pour EdgeTTS - Diagnostic de connectivité
"""
import asyncio
import edge_tts
import os
import sys

async def test_edgetts():
    """Test de base EdgeTTS"""
    print("=== Test EdgeTTS ===")
    
    # Configuration
    text = "Bonjour, ceci est un test de synthèse vocale."
    voice = "fr-FR-HenriNeural"
    output_file = "/tmp/test_edgetts.mp3"
    
    print(f"Texte: {text}")
    print(f"Voix: {voice}")
    print(f"Fichier de sortie: {output_file}")
    
    # Variables d'environnement proxy
    http_proxy = os.getenv('HTTP_PROXY', 'Non défini')
    https_proxy = os.getenv('HTTPS_PROXY', 'Non défini')
    no_proxy = os.getenv('NO_PROXY', 'Non défini')
    
    print(f"\nConfiguration proxy:")
    print(f"HTTP_PROXY: {http_proxy}")
    print(f"HTTPS_PROXY: {https_proxy}")
    print(f"NO_PROXY: {no_proxy}")
    
    try:
        print("\n1. Test de liste des voix...")
        voices = await edge_tts.list_voices()
        french_voices = [v for v in voices if v['Locale'].startswith('fr-')]
        print(f"Voix françaises disponibles: {len(french_voices)}")
        for v in french_voices[:3]:  # Afficher les 3 premières
            print(f"  - {v['ShortName']}: {v['FriendlyName']}")
        
        print(f"\n2. Test de synthèse avec {voice}...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        
        # Vérifier le fichier
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Succès! Fichier créé: {output_file} ({file_size} bytes)")
            
            # Nettoyer
            os.remove(output_file)
            print("Fichier de test supprimé.")
        else:
            print("❌ Échec: Fichier non créé")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_edgetts())