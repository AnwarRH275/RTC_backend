from flask_restx import Namespace, Resource, fields
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import json
from flask import request

# Création du namespace pour l'API
tcf_oral_ns = Namespace('tcf-oral', description='Opérations sur les sujets oraux TCF')

# Modèles de données pour la documentation Swagger
task_model = tcf_oral_ns.model('TCFOralTask', {
    'title': fields.String(required=True, description='Titre de la tâche'),
    'task_type': fields.String(required=True, description='Type de tâche: entretien, expression, questions'),
    'objective': fields.String(required=False, description='Objectif de la tâche'),
    'trigger': fields.String(required=False, description='Déclencheur/consigne de la tâche'),
    'evaluation_criteria': fields.String(required=False, description='Critères d\'évaluation'),
    'duration': fields.Integer(required=True, description='Durée en minutes'),
    'points': fields.Integer(required=False, description='Points attribués'),
    'preparation_time': fields.Integer(required=False, description='Temps de préparation en minutes'),
    'roleplay_scenario': fields.String(required=False, description='Scénario de jeu de rôle (pour le type questions)')
})

subject_model = tcf_oral_ns.model('TCFOralSubject', {
    'name': fields.String(required=True, description='Titre du sujet'),
    'description': fields.String(required=False, description='Description du sujet'),
    'date': fields.String(required=True, description='Date de création au format YYYY-MM-DD'),
    'status': fields.String(required=False, description='Statut (Actif, Inactif)', default='Actif'),
    'duration': fields.Integer(required=False, description='Durée totale en minutes'),
    'subject_type': fields.String(required=False, description='Type de sujet', default='Oral'),
    'combination': fields.String(required=False, description='Combinaison'),
    'tasks': fields.List(fields.Nested(task_model), required=True, description='Liste des tâches')
})

# Modèle pour la validation de l'agent
agent_validation_model = tcf_oral_ns.model('AgentValidation', {
    'transcript': fields.String(required=True, description='Transcription à valider')
})

# Endpoints pour les sujets oraux
@tcf_oral_ns.route('/oral-subjects')
class OralSubjectListResource(Resource):
    @tcf_oral_ns.doc('list_oral_subjects')
    def get(self):
        """Récupère tous les sujets oraux"""
        try:
            from models.exts import db
            service = create_tcf_oral_service(db.session)
            subjects = service.get_all_subjects()
            
            # Pagination et filtrage (à implémenter si nécessaire)
            return {
                'subjects': [service._serialize_subject(subject) for subject in subjects],
                'pagination': {
                    'total': len(subjects),
                    'page': 1,
                    'per_page': len(subjects)
                }
            }, 200
        except Exception as e:
            return handle_tcf_oral_error(e), 500
    
    @tcf_oral_ns.doc('create_oral_subject')
    @tcf_oral_ns.expect(subject_model)
    def post(self):
        """Crée un nouveau sujet oral"""
        try:
            from models.exts import db
            service = create_tcf_oral_service(db.session)
            data = tcf_oral_ns.payload
            subject = service.create_subject(data)
            return service._serialize_subject(subject), 201
        except Exception as e:
            return handle_tcf_oral_error(e), 500

@tcf_oral_ns.route('/oral-task-types')
class OralTaskTypesResource(Resource):
    @tcf_oral_ns.doc('get_oral_task_types')
    def get(self):
        """Récupère tous les types de tâches orales disponibles"""
        try:
            # Définition des types de tâches orales
            task_types = [
                {
                    'id': 'entretien',
                    'value': 'entretien',
                    'label': 'Entretien',
                    'color': 'info',
                    'defaultDuration': 5,
                    'defaultPreparationTime': 0
                },
                {
                    'id': 'expression',
                    'value': 'expression',
                    'label': 'Expression d\'un point de vue',
                    'color': 'success',
                    'defaultDuration': 10,
                    'defaultPreparationTime': 10
                },
                {
                    'id': 'questions',
                    'value': 'questions',
                    'label': 'Jeu de rôle',
                    'color': 'warning',
                    'defaultDuration': 10,
                    'defaultPreparationTime': 5
                }
            ]
            
            return {'success': True, 'data': task_types}, 200
        except Exception as e:
            return handle_tcf_oral_error(e), 500

@tcf_oral_ns.route('/oral-subjects/<int:id>')
class OralSubjectResource(Resource):
    @tcf_oral_ns.doc('get_oral_subject')
    def get(self, id):
        """Récupère un sujet oral par son ID"""
        try:
            from models.exts import db
            service = create_tcf_oral_service(db.session)
            subject = service.get_subject_by_id(id)
            if not subject:
                return {'message': 'Sujet non trouvé'}, 404
            return service._serialize_subject(subject), 200
        except Exception as e:
            return handle_tcf_oral_error(e), 500

    @tcf_oral_ns.doc('update_oral_subject')
    @tcf_oral_ns.expect(subject_model)
    def put(self, id):
        """Met à jour un sujet oral"""
        try:
            from models.exts import db
            service = create_tcf_oral_service(db.session)
            data = tcf_oral_ns.payload
            subject = service.update_subject(id, data)
            if not subject:
                return {'message': 'Sujet non trouvé'}, 404
            return service._serialize_subject(subject), 200
        except Exception as e:
            return handle_tcf_oral_error(e), 500

    @tcf_oral_ns.doc('delete_oral_subject')
    def delete(self, id):
        """Supprime un sujet oral"""
        try:
            from models.exts import db
            service = create_tcf_oral_service(db.session)
            success = service.delete_subject(id)
            if not success:
                return {'message': 'Sujet non trouvé'}, 404
            return {'message': 'Sujet supprimé avec succès'}, 200
        except Exception as e:
            return handle_tcf_oral_error(e), 500

# Nouvel endpoint pour la validation de l'agent
@tcf_oral_ns.route('/agent-validation')
class AgentValidationResource(Resource):
    @tcf_oral_ns.doc('validate_agent_readiness')
    @tcf_oral_ns.expect(agent_validation_model)
    def post(self):
        """Valide si l'utilisateur est prêt à commencer l'examen"""
        try:
            data = request.get_json()
            transcript = data.get('transcript', '').lower().strip()
            
            # Vérifier si la transcription contient "oui je suis prêt" ou une variante proche
            ready_phrases = ["oui je suis prêt", "oui je suis pret", "oui je suis prête", 
                            "oui je suis prete", "je suis prêt", "je suis pret", 
                            "je suis prête", "je suis prete","oui"]
            
            is_ready = any(phrase in transcript for phrase in ready_phrases)
            
            return {
                'success': True,
                'is_ready': 1 if is_ready else 0,
                'transcript': transcript
            }, 200
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }, 500

# Classe d'erreur personnalisée pour le service TCF Oral
class TCFOralCRUDError(Exception):
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []

# Fonction pour créer une instance du service TCF Oral
def create_tcf_oral_service(db_session):
    """Crée une instance du service TCF Oral"""
    return TCFOralCRUDService(db_session)

# Fonction pour gérer les erreurs du service TCF Oral
def handle_tcf_oral_error(error):
    """Gère les erreurs du service TCF Oral"""
    if isinstance(error, TCFOralCRUDError):
        return {
            'success': False,
            'message': error.message,
            'errors': error.errors
        }
    return {
        'success': False,
        'message': str(error)
    }

# Service CRUD pour les sujets oraux
class TCFOralCRUDService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_subjects(self) -> List[Any]:
        """Récupère tous les sujets oraux"""
        try:
            from models.tcf_model_oral import TCFOralSubject
            return TCFOralSubject.query.all()
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise TCFOralCRUDError(f"Erreur lors de la récupération des sujets: {str(e)}")

    def get_subject_by_id(self, subject_id: int) -> Any:
        """Récupère un sujet oral par son ID"""
        try:
            from models.tcf_model_oral import TCFOralSubject
            return TCFOralSubject.query.get(subject_id)
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise TCFOralCRUDError(f"Erreur lors de la récupération du sujet: {str(e)}")
            
    def create_subject(self, data: Dict[str, Any]) -> Any:
        """Crée un nouveau sujet oral"""
        try:
            # Validation des données
            self._validate_subject_data(data)
            
            from models.tcf_model_oral import TCFOralSubject, TCFOralTask
            
            # Création du sujet
            subject = TCFOralSubject(
                name=data.get('name'),
                description=data.get('description'),
                date=data.get('date'),
                status=data.get('status', 'Actif'),
                duration=data.get('duration'),
                subject_type='Oral',
                combination=data.get('combination')
            )
            
            # Ajout des tâches
            tasks_data = data.get('tasks', [])
            for task_data in tasks_data:
                self._validate_task_data(task_data)
                task = TCFOralTask(
                    title=task_data.get('title'),
                    task_type=task_data.get('task_type'),
                    objective=task_data.get('objective'),
                    trigger=task_data.get('trigger'),
                    evaluation_criteria=task_data.get('evaluation_criteria'),
                    duration=task_data.get('duration'),
                    points=task_data.get('points'),
                    preparation_time=task_data.get('preparation_time'),
                    roleplay_scenario=task_data.get('roleplay_scenario')
                )
                subject.oral_tasks.append(task)
            
            # Sauvegarde en base de données
            self.db_session.add(subject)
            self.db_session.commit()
            return subject
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise TCFOralCRUDError(f"Erreur lors de la création du sujet: {str(e)}")
    
    def update_subject(self, subject_id: int, data: Dict[str, Any]) -> Any:
        """Met à jour un sujet oral existant"""
        try:
            # Validation des données
            self._validate_subject_data(data)
            
            from models.tcf_model_oral import TCFOralSubject, TCFOralTask
            
            # Récupération du sujet
            subject = TCFOralSubject.query.get(subject_id)
            if not subject:
                return None
            
            # Mise à jour des champs du sujet
            subject.name = data.get('name')
            subject.description = data.get('description')
            subject.date = data.get('date')
            subject.status = data.get('status', 'Actif')
            subject.duration = data.get('duration')
            subject.combination = data.get('combination')
            
            # Suppression des tâches existantes
            for task in subject.oral_tasks:
                self.db_session.delete(task)
            
            # Ajout des nouvelles tâches
            tasks_data = data.get('tasks', [])
            for task_data in tasks_data:
                self._validate_task_data(task_data)
                task = TCFOralTask(
                    title=task_data.get('title'),
                    task_type=task_data.get('task_type'),
                    objective=task_data.get('objective'),
                    trigger=task_data.get('trigger'),
                    evaluation_criteria=task_data.get('evaluation_criteria'),
                    duration=task_data.get('duration'),
                    points=task_data.get('points'),
                    preparation_time=task_data.get('preparation_time'),
                    roleplay_scenario=task_data.get('roleplay_scenario')
                )
                subject.oral_tasks.append(task)
            
            # Sauvegarde en base de données
            self.db_session.commit()
            return subject
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise TCFOralCRUDError(f"Erreur lors de la mise à jour du sujet: {str(e)}")
    
    def delete_subject(self, subject_id: int) -> bool:
        """Supprime un sujet oral"""
        try:
            from models.tcf_model_oral import TCFOralSubject
            
            # Récupération du sujet
            subject = TCFOralSubject.query.get(subject_id)
            if not subject:
                return False
            
            # Suppression du sujet (les tâches seront supprimées en cascade)
            self.db_session.delete(subject)
            self.db_session.commit()
            return True
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise TCFOralCRUDError(f"Erreur lors de la suppression du sujet: {str(e)}")
    
    def _validate_subject_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'un sujet oral"""
        errors = []
        
        # Validation des champs obligatoires
        required_fields = ['name', 'date']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Le champ '{field}' est obligatoire")
        
        # Validation des tâches
        tasks = data.get('tasks', [])
        if not tasks:
            errors.append("Au moins une tâche est requise")
        
        if errors:
            raise TCFOralCRUDError("Validation du sujet échouée", errors)
    
    def _validate_task_data(self, data: Dict[str, Any]) -> None:
        """Valide les données d'une tâche orale"""
        errors = []
        
        # Validation des champs obligatoires
        required_fields = ['title', 'task_type']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Le champ '{field}' est obligatoire")
        
        # Validation du type de tâche
        valid_task_types = ['entretien', 'expression', 'questions']
        if data.get('task_type') and data.get('task_type') not in valid_task_types:
            errors.append(f"Le type de tâche doit être l'un des suivants: {', '.join(valid_task_types)}")
        
        # Validation spécifique pour le type 'questions'
        if data.get('task_type') == 'questions' and not data.get('preparation_time'):
            errors.append("Le temps de préparation est obligatoire pour le type 'questions'")
        
        if errors:
            raise TCFOralCRUDError("Validation de la tâche échouée", errors)
    
    def _serialize_subject(self, subject) -> Dict[str, Any]:
        """Sérialise un sujet oral pour l'API"""
        # Utiliser directement la méthode to_dict du modèle
        return subject.to_dict()