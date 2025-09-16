import os
import sys
import asyncio
from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import uuid
import logging

# Importer les fonctions de synthèse directement
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
services_dir = os.path.join(backend_dir, "services", "exam")
sys.path.insert(0, services_dir)

from synthesis import process_text_with_groq, synthesize_with_edgetts

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

task1_ns = Namespace('proxy-task1', description='Proxy services for Task 1 AI agent')

# Modèle pour la requête à l'agent IA de la tâche 1
task1_request_model = task1_ns.model(
    "Task1Request",
    {
        "chatInput": fields.String(required=True, description="Message transcrit de l'utilisateur"),
        "sessionId": fields.String(description="ID de session unique pour l'utilisateur"),
        "objectif": fields.String(description="Objectif de la tâche pour l'agent IA")
    }
)

# Modèle pour la réponse
task1_response_model = task1_ns.model(
    "Task1Response",
    {
        "output": fields.String(description="Réponse de l'agent IA"),
        "audio_url": fields.String(description="URL du fichier audio généré"),
        "sessionId": fields.String(description="ID de session utilisé")
    }
)

@task1_ns.route('/agent-vocal')
class Task1Proxy(Resource):
    @task1_ns.expect(task1_request_model)
    @task1_ns.doc('proxy_task1_agent')
    def post(self):
        """
        Proxy pour l'API de l'agent IA de la tâche 1
        Connecte à l'API externe et convertit la réponse en audio
        """
        try:
            # Récupérer les données de la requête
            data = request.get_json()
            chat_input = data.get('chatInput')
            objectif = data.get('objectif')
            
            # Générer un sessionId s'il n'est pas fourni
            session_id = data.get('sessionId')
            if not session_id:
                session_id = str(uuid.uuid4().hex)
                logger.info(f"Nouveau sessionId généré: {session_id}")
            
            # Préparer les données pour l'API externe
            payload = {
                "chatInput": chat_input,
                "sessionId": session_id
            }
            
            # Ajouter l'objectif au payload s'il est fourni
            if objectif:
                payload["objectif"] = objectif
            
            # URL de l'API externe
            url = "https://n8n.expressiontcf.com/webhook/agent-vocal-tache1"
            
            try:
                logger.info(f"Envoi de la requête à {url} avec sessionId: {session_id}")
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=6000,  # Augmenté à 100 minutes pour éviter les timeouts
                    verify=False
                )
                
                logger.info(f"Réponse reçue - Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Récupérer la réponse de l'agent IA
                    agent_response = response.json()
                    output_text = agent_response.get('output', '')
                    
                    if not output_text:
                        return {
                            "error": "Réponse vide de l'agent IA",
                            "sessionId": session_id
                        }, 400
                    
                    # Convertir la réponse en audio via appel direct aux fonctions
                    try:
                        # Traiter le texte avec Groq
                        processed_text = process_text_with_groq(output_text)
                        
                        # Synthétiser avec EdgeTTS via appel direct
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        audio_filename = loop.run_until_complete(synthesize_with_edgetts(processed_text, session_id=session_id))
                        loop.close()
                        
                        if audio_filename:
                            # Construire l'URL dynamiquement basée sur la requête
                            base_url = os.getenv('URL_BACKEND')
                            audio_url = f"{base_url}/synthesis/audio_responses/{audio_filename}"
                            logger.info(f"URL de synthèse: {audio_url}")
                            # Retourner la réponse complète avec l'audio
                            return {
                                "output": output_text,
                                "audio_url": audio_url,
                                "sessionId": session_id
                            }, 200
                        else:
                            logger.error("Erreur lors de la synthèse vocale: aucun fichier généré")
                            # Retourner la réponse sans audio en cas d'échec de la synthèse
                            return {
                                "output": output_text,
                                "error": "Échec de la synthèse vocale",
                                "sessionId": session_id
                            }, 200
                    except Exception as e:
                        logger.error(f"Erreur lors de la synthèse vocale: {str(e)}")
                        # Retourner la réponse sans audio en cas d'erreur
                        return {
                            "output": output_text,
                            "error": "Erreur lors de la synthèse vocale",
                            "sessionId": session_id
                        }, 200
                else:
                    error_msg = f"Status {response.status_code}: {response.text[:200]}"
                    logger.error(f"Erreur de l'API externe: {error_msg}")
                    return {
                        "error": "Erreur de l'API externe",
                        "message": error_msg,
                        "sessionId": session_id
                    }, 500
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout avec {url}")
                return {
                    "error": "Timeout de l'API externe",
                    "sessionId": session_id
                }, 504
            except requests.exceptions.ConnectionError as e:
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logger.error(f"Erreur de connexion avec {url}: {error_msg}")
                return {
                    "error": "Erreur de connexion à l'API externe",
                    "message": error_msg,
                    "sessionId": session_id
                }, 503
            except Exception as e:
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                logger.error(f"Erreur avec {url}: {error_msg}")
                return {
                    "error": "Erreur lors de la communication avec l'API externe",
                    "message": error_msg,
                    "sessionId": session_id
                }, 500
            
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            logger.error(f"Erreur dans le proxy de la tâche 1: {error_msg}")
            logger.error(traceback.format_exc())
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_task1_ns = task1_ns