from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import uuid
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

task2_ns = Namespace('proxy-task2', description='Proxy services for Task 2 AI agent')

# Modèle pour la requête à l'agent IA de la tâche 2
task2_request_model = task2_ns.model(
    "Task2Request",
    {
        "chatInput": fields.String(required=True, description="Message transcrit de l'utilisateur"),
        "sessionId": fields.String(description="ID de session unique pour l'utilisateur"),
        "objectif": fields.String(description="Objectif de la tâche pour l'agent IA")
    }
)

# Modèle pour la réponse
task2_response_model = task2_ns.model(
    "Task2Response",
    {
        "output": fields.String(description="Réponse de l'agent IA"),
        "audio_url": fields.String(description="URL du fichier audio généré"),
        "sessionId": fields.String(description="ID de session utilisé")
    }
)

@task2_ns.route('/agent-vocal')
class Task2Proxy(Resource):
    @task2_ns.expect(task2_request_model)
    @task2_ns.doc('proxy_task2_agent')
    def post(self):
        """
        Proxy pour l'API de l'agent IA de la tâche 2
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
            url = "https://91ec-203-161-57-107.ngrok-free.app/webhook/agent-vocal-tache2"
            
            try:
                logger.info(f"Envoi de la requête à {url} avec sessionId: {session_id}")
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=60,
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
                    
                    # Convertir la réponse en audio via le service de synthèse
                    try:
                        # URL du service de synthèse (même serveur)
                        synthesis_url = f"{request.url_root.rstrip('/')}/synthesis/synthesize"
                        
                        synthesis_response = requests.post(
                            synthesis_url,
                            json={"text": output_text},
                            headers={
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            }
                        )
                        
                        if synthesis_response.status_code == 200:
                            synthesis_data = synthesis_response.json()
                            audio_url = synthesis_data.get('audio_url', '')
                            
                            # Retourner la réponse complète avec l'audio
                            return {
                                "output": output_text,
                                "audio_url": audio_url,
                                "sessionId": session_id
                            }, 200
                        else:
                            logger.error(f"Erreur de synthèse vocale: {synthesis_response.text}")
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
            logger.error(f"Erreur dans le proxy de la tâche 2: {error_msg}")
            logger.error(traceback.format_exc())
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_task2_ns = task2_ns