from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import urllib.parse
import time
import urllib3

# Désactiver les avertissements SSL pour éviter l'encombrement des logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxy_ns = Namespace('proxy', description='Proxy services for external APIs')

# Modèle pour la requête de correction
correction_request_model = proxy_ns.model(
    "CorrectionRequest",
    {
        "text": fields.String(required=True, description="Texte à corriger"),
        "type": fields.String(required=True, description="Type de correction"),
        "additional_data": fields.Raw(description="Données additionnelles")
    }
)

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
            
            # URLs de fallback avec HTTPS et HTTP
            urls = [
                'https://n8n.expressiontcf.com/webhook/agent-expression-ecrite',
                'http://n8n.expressiontcf.com/webhook/agent-expression-ecrite',
              
            ]
            
            last_error = None
            
            # Essayer chaque URL une seule fois
            for url in urls:
                try:
                    print(f"Tentative de connexion a: {url}")
                    response = requests.post(
                        url,
                        json=data,
                        headers={
                            'Content-Type': 'application/json; charset=utf-8',
                            'Accept': 'application/json'
                        },
                        timeout=6000,  # 100 minutes timeout
                        verify=False
                    )
                    
                    print(f"Reponse recue - Status: {response.status_code}")
                    
                    # Si succès, retourner immédiatement sans essayer d'autres URLs
                    if response.status_code == 200:
                        print(f"Succès avec {url} - Arrêt des tentatives")
                        return response.json(), 200
                    else:
                        last_error = f"Status {response.status_code}: {response.text[:200]}"
                        print(f"Échec avec {url}: {last_error}")
                        # Continuer avec l'URL suivante
                        
                except requests.exceptions.Timeout:
                    last_error = f"Timeout avec {url}"
                    print(f"Timeout avec {url}")
                    continue
                except requests.exceptions.ConnectionError as e:
                    error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                    last_error = f"Erreur de connexion avec {url}: {error_msg}"
                    print(f"Erreur de connexion avec {url}: {error_msg}")
                    continue
                except Exception as e:
                    error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                    last_error = f"Erreur avec {url}: {error_msg}"
                    print(f"Erreur avec {url}: {error_msg}")
                    continue
            
            # Si toutes les tentatives ont échoué
            print(f"Toutes les URLs ont échoué. Dernière erreur: {last_error}")
            return {
                "error": "Impossible de se connecter a l'API de correction",
                "message": f"Toutes les tentatives ont echoue avec {len(urls)} URLs",
                "details": str(last_error),
                "api_endpoints": urls,
                "suggestion": "Verifiez la connectivité réseau et l'état du service externe"
            }, 500
            
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print("Erreur dans le proxy de correction: " + error_msg)
            print(traceback.format_exc())
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
proxy_correction_ns = proxy_ns