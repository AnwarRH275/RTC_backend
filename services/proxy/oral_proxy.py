from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
import requests
import traceback
import urllib.parse
import time
import json

proxy_ns = Namespace('proxy', description='Proxy services for external APIs')

def validate_oral_json_format(response_data):
    """
    Valide que la réponse JSON respecte strictement le format attendu pour l'oral TCF.
    Retourne True si valide, False sinon.
    """
    try:
        # Vérifier que c'est une liste
        if not isinstance(response_data, list):
            print("Erreur validation: La réponse n'est pas une liste")
            return False
        
        # Vérifier qu'il y a exactement 3 éléments (tâches)
        if len(response_data) != 3:
            print(f"Erreur validation: Nombre de tâches incorrect ({len(response_data)} au lieu de 3)")
            return False
        
        # Définir les tâches attendues
        expected_tasks = ['tache1', 'tache2', 'tache3']
        required_fields = ['corrections_taches', 'pointsForts', 'pointsAmeliorer', 'NoteExam', 'NoteExamCorrection']
        
        for i, task_data in enumerate(response_data):
            # Vérifier la structure de base
            if not isinstance(task_data, dict) or 'output' not in task_data:
                print(f"Erreur validation tâche {i+1}: Structure 'output' manquante")
                return False
            
            output = task_data['output']
            if not isinstance(output, dict):
                print(f"Erreur validation tâche {i+1}: 'output' n'est pas un dictionnaire")
                return False
            
            # Vérifier que la tâche attendue existe
            task_name = expected_tasks[i]
            if task_name not in output:
                print(f"Erreur validation tâche {i+1}: '{task_name}' manquante")
                return False
            
            task_content = output[task_name]
            if not isinstance(task_content, dict):
                print(f"Erreur validation tâche {i+1}: Le contenu de '{task_name}' n'est pas un dictionnaire")
                return False
            
            # Vérifier tous les champs requis
            for field in required_fields:
                if field not in task_content:
                    if field == 'NoteExamCorrection':
                        # Créer automatiquement le champ NoteExamCorrection avec la valeur par défaut 'B1'
                        task_content['NoteExamCorrection'] = 'C1'
                        print(f"Champ 'NoteExamCorrection' manquant dans tâche {i+1} - ajouté automatiquement avec la valeur 'B1'")
                    else:
                        print(f"Erreur validation tâche {i+1}: Champ '{field}' manquant")
                        return False
                
                # Vérifier les types des champs
                if field in ['corrections_taches', 'pointsForts', 'pointsAmeliorer']:
                    if not isinstance(task_content[field], list):
                        print(f"Erreur validation tâche {i+1}: '{field}' doit être une liste")
                        return False
                elif field in ['NoteExam', 'NoteExamCorrection']:
                    if not isinstance(task_content[field], str):
                        print(f"Erreur validation tâche {i+1}: '{field}' doit être une chaîne")
                        return False
        
        print("Validation JSON réussie: Format correct")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la validation JSON: {str(e)}")
        return False

# Modèle pour la requête de correction orale
oral_request_model = proxy_ns.model(
    "OralRequest",
    {
        "text": fields.String(required=True, description="Texte à analyser pour l'oral"),
        "type": fields.String(required=True, description="Type d'analyse orale"),
        "additional_data": fields.Raw(description="Données additionnelles")
    }
)

@proxy_ns.route('/oral')
class OralProxy(Resource):
    @proxy_ns.expect(oral_request_model)
    @proxy_ns.doc('proxy_oral')
    def post(self):
        """
        Proxy pour l'API d'expression orale
        Connecte uniquement à l'API externe 203.161.57.107:5678
        """
        try:
            # Récupérer les données de la requête
            data = request.get_json()
            
            # Essayer d'abord HTTPS, puis HTTP
            urls = [
                'https://n8n.expressiontcf.com/webhook/agent-expression-oral',
                'http://n8n.expressiontcf.com/webhook/agent-expression-oral',
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
                            response_json = response.json()
                            
                            # Validation stricte du format JSON
                            if validate_oral_json_format(response_json):
                                print("Format JSON validé avec succès")
                                return response_json, 200
                            else:
                                print("Format JSON invalide - nouvelle tentative requise")
                                # Si le format est invalide, on considère cela comme une erreur temporaire
                                # et on continue avec les tentatives suivantes
                                last_error = f"Format JSON invalide reçu de {url}"
                                if attempt < max_retries - 1:
                                    time.sleep(2 ** attempt)  # Exponential backoff
                                    continue
                                break
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
                "error": "Impossible de se connecter a l'API d'expression orale",
                "message": "Toutes les tentatives ont echoue. Derniere erreur: " + str(last_error),
                "api_endpoint": "203.161.57.107:5678"
            }, 500
            
        except Exception as e:
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print("Erreur dans le proxy d'expression orale: " + error_msg)
            print(traceback.format_exc())
            return {
                'error': 'Erreur interne du serveur',
                'message': error_msg
            }, 500

# Export du namespace pour l'importation
oral_proxy_ns = proxy_ns