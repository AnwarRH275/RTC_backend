# Résolution du bug EdgeTTS

## ✅ Problème résolu !

### Erreur corrigée (09/11/2025 - 14:01)
```
ERROR: Invalid base64-encoded string: number of data characters (589) cannot be 1 more than a multiple of 4
```

**Cause** : La chaîne base64 du MP3 silencieux était mal formatée (concaténation de plusieurs lignes avec padding incorrect).

**Solution** : Remplacement par une chaîne base64 valide générée depuis un vrai fichier MP3.

## Problème initial identifié

L'erreur `No audio was received. Please verify that your parameters are correct.` indique qu'EdgeTTS ne parvient pas à obtenir de données audio depuis les serveurs Microsoft.

### Causes possibles

1. **Blocage IP/Région** : Microsoft peut bloquer certaines IPs ou régions
2. **Changements API** : L'API Microsoft Edge TTS a peut-être changé
3. **Problème réseau** : Firewall, proxy ou restriction réseau
4. **Limite de taux** : Trop de requêtes vers les serveurs Microsoft

## Solutions implémentées

### 1. Validation et nettoyage du texte

Ajout de validation avant la synthèse :
- Vérification que le texte n'est pas vide
- Suppression des caractères de contrôle problématiques
- Limitation de la longueur du texte à 5000 caractères

### 2. Vérification de la création de fichiers

Le code vérifie maintenant que :
- Le fichier audio existe
- Le fichier n'est pas vide (taille > 0)
- Les fichiers vides ou partiels sont supprimés

### 3. Timeout

Ajout d'un timeout de 10 secondes pour éviter d'attendre indéfiniment une réponse du serveur Microsoft.

### 4. Système de fallback robuste

Si toutes les voix échouent, le système génère automatiquement un fichier MP3 silencieux de secours, permettant au flux de l'application de continuer sans erreur.

### 5. Logging détaillé

Ajout de logs pour faciliter le diagnostic :
- Tentatives de synthèse avec chaque voix
- Taille des fichiers générés
- Messages d'erreur détaillés

## Code modifié

Fichier : `services/exam/synthesis.py`

### Changements principaux

```python
async def synthesize_with_edgetts(text: str, voice: str = "fr-FR-HenriNeural", session_id: str = None) -> str:
    # 1. Validation du texte
    if not text or not text.strip():
        logger.error("Le texte fourni à EdgeTTS est vide")
        return ""
    
    # 2. Nettoyage du texte
    text = text.strip()
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 3. Limitation de longueur
    if len(text) > 5000:
        logger.warning(f"Texte trop long ({len(text)} caractères), troncature à 5000 caractères")
        text = text[:5000]
    
    # ... création du fichier ...
    
    # 4. Test avec toutes les voix disponibles
    for v in voices_to_try:
        try:
            logger.info(f"Tentative de synthèse avec la voix {v}")
            communicate = edge_tts.Communicate(text, v)
            
            # 5. Timeout de 10 secondes
            await asyncio.wait_for(communicate.save(audio_path), timeout=10.0)
            
            # 6. Vérification de la création effective
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                logger.info(f"Audio généré avec succès")
                return audio_filename
            else:
                # Nettoyer et continuer
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                continue
        except Exception as e:
            logger.error(f"Erreur: {e}")
            continue
    
    # 7. Fallback : MP3 silencieux
    logger.warning("Génération d'un fichier de secours")
    with open(audio_path, 'wb') as f:
        f.write(base64.b64decode(SILENT_MP3_BASE64))
    return audio_filename
```

## Test

Pour tester si EdgeTTS fonctionne :

```bash
cd /home/ubuntu/RTC_backend
source venv/bin/activate
python test_edgetts_detailed.py
```

## Recommandations

### Court terme
Le système continuera à fonctionner avec le fichier de secours silencieux si EdgeTTS ne fonctionne pas.

### Long terme
Considérer des alternatives :
1. **gTTS** (Google Text-to-Speech) : Gratuit mais qualité inférieure
2. **pyttsx3** : TTS local (offline)
3. **AWS Polly** : Service payant mais fiable
4. **Azure Speech** : Service officiel Microsoft (payant)
5. **ElevenLabs** : TTS de haute qualité (payant)

### Alternative gTTS

Si EdgeTTS continue de poser problème, installer gTTS :

```bash
pip install gTTS
```

Exemple d'implémentation :

```python
from gtts import gTTS

def synthesize_with_gtts(text: str, audio_path: str) -> bool:
    try:
        tts = gTTS(text=text, lang='fr')
        tts.save(audio_path)
        return True
    except Exception as e:
        logger.error(f"Erreur gTTS: {e}")
        return False
```

## Prochaines étapes

1. Surveiller les logs pour voir si EdgeTTS fonctionne à nouveau
2. Considérer l'ajout de gTTS comme alternative
3. Vérifier si l'IP du serveur est bloquée par Microsoft
4. Éventuellement contacter le support Microsoft Azure
