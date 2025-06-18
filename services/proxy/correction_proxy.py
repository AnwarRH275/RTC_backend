from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import urllib.parse
import threading

proxy_ns = Namespace('proxy', description='Proxy services for external APIs')

# Modèle pour la requête de correction
correction_request_model = proxy_ns.model(
    "CorrectionRequest",
    {
        "chatInput": fields.List(fields.String, required=True, description="Réponses des tâches"),
        "sessionId": fields.String(required=True, description="Identifiant de session"),
        "Taches": fields.List(fields.String, required=True, description="Titres des tâches"),
        "Structures": fields.List(fields.String, required=True, description="Structures des tâches"),
        "Instructions": fields.List(fields.String, required=True, description="Instructions des tâches"),
        "Documents": fields.List(fields.String, required=True, description="Documents des tâches")
    }
)

# Suppression du mécanisme de blocage des sessions pour permettre le traitement concurrent
# active_sessions = {}
# active_sessions_lock = threading.Lock()

@proxy_ns.route('/correction')
class CorrectionProxy(Resource):
    @proxy_ns.expect(correction_request_model)
    @proxy_ns.doc('proxy_correction')
    def post(self):
        """
        Proxy pour l'API de correction d'expression écrite
        Connecte uniquement à l'API externe 203.161.57.107:5678
        """
        try:
            # Récupérer les données de la requête
            data = request.get_json()
            
            # Récupération de l'ID de session pour le logging
            session_id = data.get('sessionId')
            print(f"Traitement de la session {session_id}")
            
            try:
                # Essayer d'abord HTTPS, puis HTTP
                urls = [
                    'https://91ec-203-161-57-107.ngrok-free.app/webhook/agent-expression-ecrite',
                    
                ]
                
                last_error = None
                
                for url in urls:
                    try:
                        print("Tentative de connexion a: " + str(url))
                        response = requests.post(
                            url,
                            json=data,
                            headers={
                                'Content-Type': 'application/json; charset=utf-8',
                                'Accept': 'application/json'
                            },
                            timeout=1200,  # Timeout de 20 minutes
                            verify=False
                        )
                        
                        print("Reponse recue - Status: " + str(response.status_code))
                        
                        if response.status_code == 200:
                            return response.json(), 200
                        else:
                            last_error = "Status " + str(response.status_code) + ": " + str(response.text[:200])
                            
                    except requests.exceptions.Timeout:
                        last_error = "Timeout avec " + str(url)
                        print("Timeout avec " + str(url))
                        continue
                    except requests.exceptions.ConnectionError as e:
                        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                        last_error = "Erreur de connexion avec " + str(url) + ": " + error_msg
                        print("Erreur de connexion avec " + str(url) + ": " + error_msg)
                        continue
                    except Exception as e:
                        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                        last_error = "Erreur avec " + str(url) + ": " + error_msg
                        print("Erreur: " + last_error)
                        continue
                
                # Si toutes les tentatives ont echoue
                return {
                    "error": "Impossible de se connecter a l'API de correction",
                    "message": "Toutes les tentatives ont echoue. Derniere erreur: " + str(last_error),
                    "api_endpoint": "203.161.57.107:5678"
                }, 500
            finally:
                # Session terminée
                print(f"Session {session_id} terminée")
                
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print("Erreur dans le proxy de correction: " + error_msg)
            print(traceback.format_exc())
            
            # Logging de l'erreur pour la session
            if 'session_id' in locals() and session_id:
                print(f"Erreur lors du traitement de la session {session_id}")
            
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_correction_ns = proxy_ns