from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.tcf_attempt_model import TCFAttempt
from models.model import User
from models.tcf_model import TCFSubject
from models.exts import db

attempt_ns = Namespace('attempt', description='Gestion des tentatives d\'examen TCF')

# Modèle pour les tentatives
attempt_model = attempt_ns.model(
    "TCFAttempt",
    {
        "id": fields.Integer(),
        "id_user": fields.Integer(required=True),
        "id_subject": fields.Integer(required=True),
        "attempt_count": fields.Integer(),
        "last_attempt_date": fields.DateTime(),
        "created_at": fields.DateTime(),
        "updated_at": fields.DateTime()
    }
)

# Modèle pour la création/mise à jour d'une tentative
attempt_input_model = attempt_ns.model(
    "TCFAttemptInput",
    {
        "id_subject": fields.Integer(required=True)
    }
)

@attempt_ns.route("/attempts")
class TCFAttemptResource(Resource):
    
    @attempt_ns.marshal_list_with(attempt_model)
    @jwt_required()
    def get(self):
        '''Récupérer toutes les tentatives de l\'utilisateur connecté'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
            
        attempts = TCFAttempt.query.filter_by(id_user=user.id).all()
        return attempts

@attempt_ns.route("/attempts/subject/<int:subject_id>")
class TCFAttemptBySubjectResource(Resource):
    
    @attempt_ns.marshal_with(attempt_model)
    @jwt_required()
    def get(self, subject_id):
        '''Récupérer les tentatives pour un sujet spécifique'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
            
        # Vérifier si le sujet existe
        subject = TCFSubject.query.get_or_404(subject_id)
        
        # Récupérer ou créer la tentative
        attempt = TCFAttempt.get_or_create_attempt(user.id, subject_id)
        return attempt
    
    @attempt_ns.marshal_with(attempt_model)
    @jwt_required()
    def post(self, subject_id):
        '''Incrémenter le compteur de tentatives pour un sujet'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
            
        # Vérifier si le sujet existe
        subject = TCFSubject.query.get_or_404(subject_id)
        
        try:
            # Récupérer ou créer la tentative
            attempt = TCFAttempt.get_or_create_attempt(user.id, subject_id)
            
            # Incrémenter le compteur
            attempt.increment_attempt()
            
            return attempt, 200
            
        except Exception as e:
            return {'error': f"Erreur lors de l'incrémentation : {str(e)}"}, 500

@attempt_ns.route("/attempts/check/<int:subject_id>")
class TCFAttemptCheckResource(Resource):
    
    @jwt_required()
    def get(self, subject_id):
        '''Vérifier si l\'utilisateur peut passer l\'examen (max 2 tentatives)'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
            
        # Vérifier si le sujet existe
        subject = TCFSubject.query.get_or_404(subject_id)
        
        # Récupérer ou créer la tentative
        attempt = TCFAttempt.get_or_create_attempt(user.id, subject_id)
        
        can_attempt = attempt.attempt_count < 2
        remaining_attempts = max(0, 2 - attempt.attempt_count)
        
        return {
            'can_attempt': can_attempt,
            'current_attempts': attempt.attempt_count,
            'remaining_attempts': remaining_attempts,
            'max_attempts': 2
        }, 200