from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import urllib.parse
import time
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
                'https://n8n.expressiontcf.com/webhook/agent-tradution',
             
            ]
            
            last_error = None
            
            for url in urls:
                # Tentative avec retry exponentiel
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        print(f"Tentative de connexion a: {url} (tentative {attempt + 1}/{max_retries})")
                        response = requests.post(
                            url,
                            json=data,
                            headers={
                                'Content-Type': 'application/json; charset=utf-8',
                                'Accept': 'application/json'
                            },
                            timeout=6000,  # Augmenté à 100 minutes pour éviter les timeouts
                            verify=False
                        )
                        
                        print("Reponse recue - Status: " + str(response.status_code))
                        
                        if response.status_code == 200:
                            return response.json(), 200
                        elif response.status_code == 504:
                            # Gateway timeout - retry
                            print(f"Gateway timeout (504) - retrying attempt {attempt + 1}")
                            if attempt < max_retries - 1:
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        else:
                            last_error = "Status " + str(response.status_code) + ": " + str(response.text[:200])
                            break
                            
                    except requests.exceptions.Timeout:
                        last_error = "Timeout avec " + str(url)
                        print(f"Timeout avec {url} - tentative {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        break
                    except requests.exceptions.ConnectionError as e:
                        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                        last_error = "Erreur de connexion avec " + str(url) + ": " + error_msg
                        print(f"Erreur de connexion avec {url}: {error_msg} - tentative {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        break
                    except Exception as e:
                        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                        last_error = "Erreur avec " + str(url) + ": " + error_msg
                        print(f"Erreur avec {url}: {error_msg} - tentative {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        break
            
            # Si toutes les tentatives ont echoue
            return {
                "error": "Impossible de se connecter a l'API de traduction",
                "message": "Toutes les tentatives ont echoue. Derniere erreur: " + str(last_error),
                "api_endpoint": "https://n8n.expressiontcf.com"
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