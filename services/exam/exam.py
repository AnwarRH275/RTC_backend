from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity # Added get_jwt_identity
from models.tcf_exam_model import TCFExam
from models.model import User # Added User model import
from models.tcf_model import TCFSubject, TCFTask # Added TCFSubject and TCFTask model imports
from models.exts import db

exam_ns = Namespace('exam', description='Gestion des examens TCF passés')

# Modèle pour les examens passés (basic)
exam_model = exam_ns.model(
    "TCFExam",
    {
        "id": fields.Integer(),
        "id_user": fields.Integer(required=True),
        "id_subject": fields.Integer(required=True),
        "id_task": fields.Integer(required=True),
        "reponse_utilisateur": fields.String(),
        "score": fields.String(),
        "reponse_ia": fields.String(),
        "points_fort": fields.String(),
        "point_faible": fields.String(),
        "traduction_reponse_ia": fields.String(),
        "date_passage": fields.DateTime()
    }
)

# Modèle pour la création/mise à jour d'un examen passé
exam_input_model = exam_ns.model(
    "TCFExamInput",
    {
        "id_user": fields.Integer(required=True),
        "id_subject": fields.Integer(required=True),
        "id_task": fields.Integer(required=True),
        "reponse_utilisateur": fields.String(),
        "score": fields.String(),
        "reponse_ia": fields.String(),
        "points_fort": fields.String(),
        "point_faible": fields.String(),
        "traduction_reponse_ia": fields.String(),
        # date_passage sera générée automatiquement par le modèle
    }
)

# Modèle pour les données utilisateur imbriquées
user_nested_model = exam_ns.model(
    "UserNested",
    {
        "id": fields.Integer(),
        "username": fields.String(),
        "email": fields.String(),
        "nom": fields.String(),
        "prenom": fields.String(),
        "tel": fields.String(),
        "subscription_plan": fields.String(),
    }
)

# Modèle pour les données sujet TCF imbriquées
tcf_subject_nested_model = exam_ns.model(
    "TCFSubjectNested",
    {
        "id": fields.Integer(),
        "name": fields.String(),
        "date": fields.String(),
        "subscription_plan": fields.String(),
        "status": fields.String(),
        "duration": fields.Integer(),
        "subject_type": fields.String(),
    }
)

# Modèle pour les données tâche TCF imbriquées
tcf_task_nested_model = exam_ns.model(
    "TCFTaskNested",
    {
        "id": fields.Integer(),
        "title": fields.String(),
        "description": fields.String(),
        "word_count": fields.Integer(),
        "audio_duration": fields.Integer(),
    }
)

# Modèle détaillé pour les examens passés incluant les relations
detailed_exam_model = exam_ns.model(
    "DetailedTCFExam",
    {
        "id": fields.Integer(),
        "reponse_utilisateur": fields.String(),
        "score": fields.String(),
        "reponse_ia": fields.String(),
        "points_fort": fields.String(),
        "point_faible": fields.String(),
        "traduction_reponse_ia": fields.String(),
        "date_passage": fields.DateTime(),
        "user": fields.Nested(user_nested_model), # Inclure les données utilisateur
        "subject": fields.Nested(tcf_subject_nested_model), # Inclure les données sujet
        "task": fields.Nested(tcf_task_nested_model), # Inclure les données tâche
    }
)

@exam_ns.route("/exams")
class TCFExamResource(Resource):
    
    @exam_ns.marshal_list_with(exam_model)
    @jwt_required() # Assurez-vous que l'utilisateur est authentifié
    def get(self):
        '''Récupérer tous les examens passés'''
        # Vous pourriez vouloir filtrer par utilisateur ici, par exemple:
        # current_user_id = get_jwt_identity() # Nécessite d'importer get_jwt_identity
        # exams = TCFExam.query.filter_by(id_user=current_user_id).all()
        exams = TCFExam.query.all()
        return exams

@exam_ns.route("/exams/user")
class TCFExamUserResource(Resource):
    
    @exam_ns.marshal_list_with(exam_model)
    @jwt_required()
    def get(self):
        '''Récupérer tous les examens passés de l'utilisateur connecté'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        
        if not user:
            return {'message': 'Utilisateur non trouvé'}, 404
            
        exams = TCFExam.query.filter_by(id_user=user.id).all()
        
        return exams

    
    @exam_ns.marshal_with(exam_model)
    @exam_ns.expect(exam_input_model)
    @jwt_required()
    def post(self):
        '''Créer un nouvel examen passé'''
        data = request.get_json()

        # Récupérer l'utilisateur
        username = data.get('id_user')
        user = User.query.filter_by(username=username).first()

        if not user:
            return {'error': 'Utilisateur non trouvé'}, 404

        try:
            # Création de l'examen
            new_exam = TCFExam(
                id_user=user.id,
                id_subject=data.get('id_subject'),
                id_task=data.get('id_task'),
                reponse_utilisateur=data.get('reponse_utilisateur'),
                score=data.get('score'),
                reponse_ia=data.get('reponse_ia'),
                points_fort=data.get('points_fort'),
                point_faible=data.get('point_faible'),
                traduction_reponse_ia=data.get('traduction_reponse_ia')
                # date_passage est définie par défaut dans le modèle
            )
            new_exam.save()

            # Retourner les données sérialisées
            return jsonify({
                'message': 'Examen enregistré avec succès',
                'exam_id': new_exam.id
            }), 201

        except Exception as e:
            # Gestion des erreurs
            return jsonify({'error': f"Erreur lors de l'enregistrement : {str(e)}"}), 500

@exam_ns.route("/exams/<int:id>")
class TCFExamDetailResource(Resource):
    
    @exam_ns.marshal_with(exam_model)
    @jwt_required()
    def get(self, id):
        '''Récupérer un examen passé par son ID'''
        exam = TCFExam.query.get_or_404(id)
        # Optionnel: Vérifier si l'examen appartient à l'utilisateur authentifié
        # current_user_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_user_identity).first()
        # if user and exam.id_user != user.id:
        #     return {'message': 'Accès non autorisé'}, 403
        return exam

    @exam_ns.expect(exam_input_model)
    @exam_ns.marshal_with(exam_model)
    @jwt_required()
    def put(self, id):
        '''Mettre à jour un examen passé'''
        exam = TCFExam.query.get_or_404(id)
        # Optionnel: Vérifier si l'examen appartient à l'utilisateur authentifié
        # current_user_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_user_identity).first()
        # if user and exam.id_user != user.id:
        #     return {'message': 'Accès non autorisé'}, 403
            
        data = request.get_json()
        exam.update(data)
        
        return exam

    @jwt_required()
    def delete(self, id):
        '''Supprimer un examen passé'''
        exam = TCFExam.query.get_or_404(id)
        # Optionnel: Vérifier si l'examen appartient à l'utilisateur authentifié
        # current_user_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_user_identity).first()
        # if user and exam.id_user != user.id:
        #     return {'message': 'Accès non autorisé'}, 403
            
        exam.delete()
        return {"message": f"Examen {id} supprimé"}, 200

# Nouvelle route pour récupérer les examens par sujet
@exam_ns.route("/exams/subject/<int:subject_id>")
class TCFExamBySubjectResource(Resource):
    
    @exam_ns.marshal_list_with(detailed_exam_model) # Utiliser le modèle détaillé
    @jwt_required()
    def get(self, subject_id):
        '''Récupérer tous les examens passés pour un sujet donné'''
        # Optionnel: Filtrer également par l'utilisateur authentifié
        # current_user_identity = get_jwt_identity()
        # user = User.query.filter_by(username=current_user_identity).first()
        # if user:
        #     exams = TCFExam.query.filter_by(id_subject=subject_id, id_user=user.id).all()
        # else:
        #     return {'message': 'Utilisateur non trouvé'}, 404

        # Récupérer les examens pour le sujet donné, en chargeant les relations
        exams = TCFExam.query.filter_by(id_subject=subject_id).all()
        
        if not exams:
            return {'message': 'Aucun examen trouvé pour ce sujet'}, 404
            
        return exams