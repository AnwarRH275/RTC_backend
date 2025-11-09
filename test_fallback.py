#!/usr/bin/env python3
"""Test du système de fallback avec MP3 silencieux"""
import base64
import os

# MP3 silencieux (même que dans synthesis.py)
SILENT_MP3_BASE64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAASAAAeMwAUFBQUFCIiIiIiIjAwMDAwPj4+Pj4+TExMTExZWVlZWVlnZ2dnZ3V1dXV1dYODg4ODkZGRkZGRn5+fn5+frKysrKy6urq6urrIyMjIyNbW1tbW1uTk5OTk8vLy8vLy//////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAQKAAAAAAAAHjOZTf9/AAAAAAAAAAAAAAAAAAAAAP/7kGQAD/AAAGkAAAAIAAANIAAAAQAAAaQAAAAgAAA0gAAABExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//uQZAQP8AAAaQAAAAgAAA0gAAABAAABpAAAACAAADSAAAAEVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVQ=="

def test_fallback():
    """Test la génération du fichier de fallback"""
    output_file = "test_fallback.mp3"
    
    try:
        print("Test de décodage base64...")
        audio_data = base64.b64decode(SILENT_MP3_BASE64)
        print(f"✓ Décodage réussi : {len(audio_data)} bytes")
        
        print("\nCréation du fichier MP3...")
        with open(output_file, 'wb') as f:
            f.write(audio_data)
        print(f"✓ Fichier créé : {output_file}")
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ Taille du fichier : {file_size} bytes")
            
            if file_size > 0:
                print("✓ Le fichier n'est pas vide")
                print("\n✅ Test de fallback réussi !")
                
                # Vérifier le type de fichier
                import subprocess
                result = subprocess.run(['file', output_file], capture_output=True, text=True)
                print(f"\nType de fichier : {result.stdout.strip()}")
                
                # Nettoyer
                os.remove(output_file)
                print(f"\n✓ Fichier de test supprimé")
                return True
            else:
                print("✗ Le fichier est vide !")
                os.remove(output_file)
                return False
        else:
            print("✗ Le fichier n'a pas été créé !")
            return False
            
    except Exception as e:
        print(f"✗ Erreur : {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(output_file):
            os.remove(output_file)
        return False

if __name__ == "__main__":
    success = test_fallback()
    exit(0 if success else 1)
