import json
import os
import uuid
import logging
import time
import asyncio
import re
from collections import deque
from threading import Lock
from flask_restx import Resource, Namespace, fields
from flask import request, send_file
from pydantic import BaseModel
import edge_tts
from flask_cors import cross_origin
from bs4 import BeautifulSoup
import markdown
import requests
# from flask_jwt_extended import jwt_required  # Supprimé car non utilisé

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

synthesis_ns = Namespace('synthesis', description='Service de synthèse vocale pour TCF')

# Modèle pour la requête de synthèse
synthesis_request_model = synthesis_ns.model(
    "SynthesisRequest",
    {
        "text": fields.String(required=True, description="Texte à convertir en audio")
    }
)

# Modèle pour la réponse de synthèse
synthesis_response_model = synthesis_ns.model(
    "SynthesisResponse",
    {
        "audio_url": fields.String(required=False, description="URL du fichier audio généré"),
        "filename": fields.String(required=False, description="Nom du fichier audio")
    }
)

def markdown_to_plain_text(md_text: str) -> str:
    """Convertit le markdown en texte brut"""
    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")
    plain_text = soup.get_text(separator=" ")
    plain_text = re.sub(r'\*{1,2}', '', plain_text)
    return plain_text

async def synthesize_with_edgetts(text: str, voice: str = "Microsoft Server Speech Text to Speech Voice (fr-FR, HenriNeural)") -> str:
    """Synthétise le texte en audio avec EdgeTTS"""
    audio_filename = f"response_{uuid.uuid4()}.mp3"
    
    # Créer le dossier audio_responses dans le répertoire backend
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audio_dir = os.path.join(backend_dir, "audio_responses")
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, audio_filename)

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(audio_path)
        logger.info(f"Audio généré avec EdgeTTS: {audio_filename}")
        return audio_filename
    except Exception as e:
        logger.error(f"Erreur lors de la synthèse vocale avec EdgeTTS: {e}")
        return ""

# Variables globales pour le rate limiting
_groq_request_times = deque()
_groq_lock = Lock()
MAX_REQUESTS_PER_MINUTE = 28

def _wait_for_rate_limit():
    """Gère la limitation de débit pour l'API Groq (28 requêtes/minute)"""
    with _groq_lock:
        current_time = time.time()
        
        # Supprimer les requêtes plus anciennes qu'une minute
        while _groq_request_times and current_time - _groq_request_times[0] >= 60:
            _groq_request_times.popleft()
        
        # Si on a atteint la limite, attendre
        if len(_groq_request_times) >= MAX_REQUESTS_PER_MINUTE:
            # Calculer le temps d'attente jusqu'à ce que la plus ancienne requête expire
            wait_time = 60 - (current_time - _groq_request_times[0]) + 0.1  # +0.1s de marge
            if wait_time > 0:
                logger.info(f"Rate limit atteint pour Groq API. Attente de {wait_time:.1f} secondes...")
                time.sleep(wait_time)
                # Nettoyer à nouveau après l'attente
                current_time = time.time()
                while _groq_request_times and current_time - _groq_request_times[0] >= 60:
                    _groq_request_times.popleft()
        
        # Enregistrer cette requête
        _groq_request_times.append(current_time)

def process_text_with_groq(text: str) -> str:
    """Traite le texte avec l'API Groq pour le préparer à la synthèse vocale"""
    try:
        # Appliquer la limitation de débit
        _wait_for_rate_limit()
        
        from groq import Groq
        
        client = Groq(api_key="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")
        
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {
                    "role": "user",
                    "content": "Transforme ce texte pour qu'il soit converti en audio text brut. "
                              "Supprime les éléments qui pourraient perturber la lecture, comme les émoticônes ou autres distractions. "
                              "Je souhaite une lecture fluide et naturelle. Ne pas lire le tableau ni le graphe; "
                              "Ne jamais répéter cette description. Retourne uniquement le texte transformé : TEXT >> "
                              + text
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        # Extraction du texte de la réponse
        texte_extrait = completion.choices[0].message.content
        
        if not texte_extrait:
            raise Exception("Réponse vide de l'API Groq")
            
        plain_text = markdown_to_plain_text(texte_extrait)
        
        if not plain_text.strip():
            raise Exception("Le texte résultant est vide après le nettoyage")
            
        return plain_text
        
    except Exception as e:
        logger.error(f"Erreur dans le traitement Groq: {str(e)}")
        raise e

@synthesis_ns.route("/synthesize")
class SynthesisResource(Resource):
    @synthesis_ns.expect(synthesis_request_model)
    @cross_origin()
    def post(self):
        """Convertit le texte en audio"""
        try:
            data = request.get_json()
            text = data.get('text', '')
            
            if not text.strip():
                return {'error': 'Le texte ne peut pas être vide'}, 400
            
            # Traiter le texte avec Groq
            processed_text = process_text_with_groq(text)
            
            # Synthétiser avec EdgeTTS
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_filename = loop.run_until_complete(synthesize_with_edgetts(processed_text))
            loop.close()
            
            if audio_filename:
                # Construire l'URL dynamiquement basée sur la requête
                base_url = request.url_root.rstrip('/')
                print(base_url)
                audio_url = f"{base_url}/synthesis/audio_responses/{audio_filename}"
                print(audio_url)
                return {
                    "audio_url": audio_url,
                    "filename": audio_filename
                }
            else:
                return {'error': 'Erreur lors de la synthèse vocale'}, 500
                
        except Exception as e:
            logger.error(f"Erreur dans l'endpoint /synthesize: {str(e)}", exc_info=True)
            return {'error': 'Erreur interne du serveur'}, 500

@synthesis_ns.route("/audio_responses/<string:filename>")
class AudioFileResource(Resource):
    @cross_origin()
    def get(self, filename):
        """Sert les fichiers audio générés"""
        try:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            audio_dir = os.path.join(backend_dir, "audio_responses")
            file_path = os.path.join(audio_dir, filename)
            
            if not os.path.exists(file_path):
                return {'error': 'Fichier audio non trouvé'}, 404
                
            return send_file(file_path, mimetype="audio/mpeg", as_attachment=False)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du fichier audio: {str(e)}")
            return {'error': 'Erreur lors de la récupération du fichier'}, 500