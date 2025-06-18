from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback

proxy_ns = Namespace('proxy-translation', description='Proxy services for translation API')

# Modèle pour la requête de traduction
translation_request_model = proxy_ns.model(
    "TranslationRequest",
    {
        "pointsForts": fields.List(fields.String, description="Points forts"),
        "pointsAmeliorer": fields.List(fields.String, description="Points à améliorer"),
        "targetLanguage": fields.String(required=True, description="Langue cible")
    }
)

@proxy_ns.route('/translation')
class TranslationProxy(Resource):
    @proxy_ns.expect(translation_request_model)
    @proxy_ns.doc('proxy_translation')
    def post(self):
        """
        Proxy pour l'API de traduction
        Connecte uniquement à l'API externe 203.161.57.107:5678
        """
        try:
            # Récupérer les données de la requête
            data = request.get_json()
            
            # Essayer d'abord HTTPS, puis HTTP
            urls = [
                'https://91ec-203-161-57-107.ngrok-free.app/webhook/agent-traduction',
                
            ]
            
            last_error = None
            
            for url in urls:
                try:
                    print("Tentative de connexion a: " + str(url))
                    response = requests.post(
                        "https://91ec-203-161-57-107.ngrok-free.app/webhook/agent-tradution",
                        json=data,
                        headers={
                            'Content-Type': 'application/json; charset=utf-8',
                            'Accept': 'application/json'
                        },
                        timeout=1360,
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
                "error": "Impossible de se connecter a l'API de traduction",
                "message": "Toutes les tentatives ont echoue. Derniere erreur: " + str(last_error),
                "api_endpoint": "https://91ec-203-161-57-107.ngrok-free.app"
            }, 500
            
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print("Erreur dans le proxy de traduction: " + error_msg)
            print(traceback.format_exc())
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_translation_ns = proxy_ns