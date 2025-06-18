from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback

proxy_ns = Namespace('proxy-note-moyenne', description='Proxy services for note moyenne API')

# Modèle pour la requête de note moyenne
note_moyenne_request_model = proxy_ns.model(
    "NoteMoyenneRequest",
    {
        "Tache1": fields.String(required=True, description="Niveau pour la tâche 1"),
        "Tache2": fields.String(required=True, description="Niveau pour la tâche 2"),
        "Tache3": fields.String(required=True, description="Niveau pour la tâche 3"),
        "sessionId": fields.String(required=False, description="Identifiant de session")
    }
)

@proxy_ns.route('/note-moyenne')
class NoteMoyenneProxy(Resource):
    @proxy_ns.expect(note_moyenne_request_model)
    @proxy_ns.doc('proxy_note_moyenne')
    def post(self):
        """
        Proxy pour l'API de calcul de note moyenne
        Connecte uniquement à l'API externe via ngrok
        """
        try:
            # Récupérer les données de la requête
            data = request.get_json()
            
            # Récupération de l'ID de session pour le logging
            session_id = data.get('sessionId', 'non_specifie')
            print(f"Traitement de la session {session_id}")
            
            try:
                # URL du webhook pour la note moyenne
                urls = [
                    'https://91ec-203-161-57-107.ngrok-free.app/webhook/agent-note-moyenne',
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
                            timeout=300,  # Timeout de 5 minutes
                            verify=False
                        )
                        
                        print("Reponse recue - Status: " + str(response.status_code))
                        
                        if response.status_code == 200:
                            # Récupérer la réponse de l'API
                            api_response = response.json()
                            
                            # Vérifier si la réponse a le format attendu
                            if 'output' in api_response and 'noteMoyenne' in api_response['output']:
                                # Retourner directement la réponse formatée
                                return api_response, 200
                            else:
                                # Si la structure n'est pas celle attendue, retourner un message d'erreur
                                return {
                                    "error": "Format de réponse incorrect",
                                    "message": "La réponse de l'API n'a pas le format attendu",
                                    "received": api_response
                                }, 500
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
                
                # Si toutes les tentatives ont échoué
                return {
                    "error": "Impossible de se connecter a l'API de note moyenne",
                    "message": "Toutes les tentatives ont échoué. Dernière erreur: " + str(last_error),
                    "api_endpoint": "https://91ec-203-161-57-107.ngrok-free.app"
                }, 500
            finally:
                # Session terminée
                print(f"Session {session_id} terminée")
                
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print("Erreur dans le proxy de note moyenne: " + error_msg)
            print(traceback.format_exc())
            
            # Logging de l'erreur pour la session
            if 'session_id' in locals():
                print(f"Erreur lors du traitement de la session {session_id}")
            
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_note_moyenne_ns = proxy_ns