from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required
from models.tcf_model import TCFSubject, TCFTask
from models.exts import db

tcf_ns = Namespace('tcf', description='Gestion des sujets TCF')

# Modèle pour les tâches
task_model = tcf_ns.model(
    "TCFTask",
    {
        "id": fields.Integer(),
        "title": fields.String(required=True),
        "description": fields.String(),
        "audio_duration": fields.Integer(),
        "word_count": fields.Integer(),
        "instructions": fields.String(),
        "documents_de_reference": fields.String()
    }
)

# Modèle pour les sujets TCF
tcf_subject_model = tcf_ns.model(
    "TCFSubject",
    {
        "id": fields.Integer(),
        "name": fields.String(required=True),
        "date": fields.String(required=True),
        "subscription_plan": fields.String(required=True),
        "status": fields.String(required=True),
        "duration": fields.Integer(required=True),
        "combination": fields.String(required=False),
        "blog": fields.String(required=False),
        "subject_type": fields.String(required=True),
        "tasks": fields.List(fields.Nested(task_model))
    }
)

# Modèle pour la création/mise à jour de sujets TCF
tcf_subject_input_model = tcf_ns.model(
    "TCFSubjectInput",
    {
        "name": fields.String(required=True),
        "date": fields.String(required=True),
        "subscription_plan": fields.String(required=True),
        "status": fields.String(required=True),
        "duration": fields.Integer(required=True),
        "combination": fields.String(required=False),
        "blog": fields.String(required=False),
        "subject_type": fields.String(required=True),
        "tasks": fields.List(fields.Nested(task_model))
    }
)

@tcf_ns.route("/subjects")
class TCFSubjectResource(Resource):
    
    @tcf_ns.marshal_list_with(tcf_subject_model)
    def get(self):
        '''Récupérer tous les sujets TCF'''
        # Filtrer par type de sujet si spécifié
        subject_type = request.args.get('type')
        if subject_type:
            subjects = TCFSubject.query.filter_by(subject_type=subject_type).all()
        else:
            subjects = TCFSubject.query.all()
        return subjects

    @tcf_ns.expect(tcf_subject_input_model)
    @tcf_ns.marshal_with(tcf_subject_model)
    def post(self):
        '''Créer un nouveau sujet TCF'''
        data = request.get_json()
        
        # Créer le sujet
        new_subject = TCFSubject(
            name=data.get('name'),
            date=data.get('date'),
            subscription_plan=data.get('subscription_plan'),
            status=data.get('status'),
            duration=data.get('duration'),
            combination=data.get('combination'),
            blog=data.get('blog'),
            subject_type=data.get('subject_type')
        )
        new_subject.save()
        
        # Ajouter les tâches si présentes
        if 'tasks' in data and data['tasks']:
            for task_data in data['tasks']:
                new_task = TCFTask(
                    title=task_data.get('title'),
                    description=task_data.get('description'),
                    word_count=task_data.get('word_count'),
                    audio_duration=task_data.get('audio_duration'),
                    instructions=task_data.get('instructions'),
                    documents_de_reference=task_data.get('documents_de_reference'),
                    subject_id=new_subject.id
                )
                new_task.save()
        
        return new_subject, 201


@tcf_ns.route("/subjects/<int:id>")
class TCFSubjectDetailResource(Resource):
    
    @tcf_ns.marshal_with(tcf_subject_model)
    def get(self, id):
        '''Récupérer un sujet TCF par son ID'''
        subject = TCFSubject.query.get_or_404(id)
        return subject

    @tcf_ns.expect(tcf_subject_input_model)
    @tcf_ns.marshal_with(tcf_subject_model)
    def put(self, id):
        '''Mettre à jour un sujet TCF'''
        subject = TCFSubject.query.get_or_404(id)
        data = request.get_json()

        # Handle tasks separately
        tasks_data = data.pop('tasks', None) # Remove tasks from data before updating subject

        # Mettre à jour le sujet (excluding tasks)
        subject.update(data)

        # Supprimer les tâches existantes et ajouter les nouvelles
        if tasks_data is not None:
            # Supprimer les tâches existantes
            for task in subject.tasks:
                task.delete()

            # Ajouter les nouvelles tâches
            for task_data in tasks_data:
                new_task = TCFTask(
                    title=task_data.get('title'),
                    description=task_data.get('description'),
                    word_count=task_data.get('word_count'),
                    audio_duration=task_data.get('audio_duration'),
                    instructions=task_data.get('instructions'),
                    documents_de_reference=task_data.get('documents_de_reference'),
                    subject_id=subject.id
                )
                new_task.save()

        return subject

    def delete(self, id):
        '''Supprimer un sujet TCF'''
        subject = TCFSubject.query.get_or_404(id)
        subject.delete()
        return {"message": f"Sujet TCF {id} supprimé"}, 200


# Créer 3 sujets de test à l'initialisation
def create_test_subjects():
    # Vérifier si des sujets existent déjà
    if TCFSubject.query.count() == 0:
        # Sujet 1: Environnement et développement durable
        subject1 = TCFSubject(
            name="Environnement et développement durable",
            date="2023-10-15",
            subscription_plan="Intermédiaire",
            status="Actif",
            duration=60,
            combination="N5",
            blog="blog-env",
            subject_type="Écrit"
        )
        subject1.save()
        
        # Tâches pour le sujet 1
        task1 = TCFTask(
            title="Rédaction d'un essai",
            description="Rédigez un essai sur l'importance du développement durable",
            word_count=300,
            subject_id=subject1.id
        )
        task1.save()
        
        task2 = TCFTask(
            title="Analyse de document",
            description="Analysez le document fourni sur les énergies renouvelables",
            word_count=200,
            subject_id=subject1.id
        )
        task2.save()
        
        task3 = TCFTask(
            title="Questions à choix multiples",
            description="Répondez aux questions sur le texte",
            word_count=100,
            subject_id=subject1.id
        )
        task3.save()
        
        # Sujet 2: Technologie et société
        subject2 = TCFSubject(
            name="Technologie et société",
            date="2023-11-20",
            subscription_plan="Avancé",
            status="Actif",
            duration=60,
            combination="N6",
            blog="blog-tech",
            subject_type="Écrit"
        )
        subject2.save()
        
        # Tâches pour le sujet 2
        task4 = TCFTask(
            title="Dissertation",
            description="Rédigez une dissertation sur l'impact des technologies sur la société",
            word_count=350,
            subject_id=subject2.id
        )
        task4.save()
        
        task5 = TCFTask(
            title="Résumé de texte",
            description="Résumez le texte sur l'intelligence artificielle",
            word_count=150,
            subject_id=subject2.id
        )
        task5.save()
        
        task6 = TCFTask(
            title="Exercice de vocabulaire",
            description="Complétez les phrases avec le vocabulaire technique approprié",
            word_count=100,
            subject_id=subject2.id
        )
        task6.save()
        
        # Sujet 3: Culture et traditions
        subject3 = TCFSubject(
            name="Culture et traditions",
            date="2023-12-05",
            subscription_plan="Débutant",
            status="Inactif",
            duration=45,
            combination="O5",
            blog="blog-culture",
            subject_type="Écrit"
        )
        subject3.save()
        
        # Tâches pour le sujet 3
        task7 = TCFTask(
            title="Expression écrite",
            description="Décrivez une tradition culturelle de votre pays",
            word_count=200,
            subject_id=subject3.id
        )
        task7.save()
        
        task8 = TCFTask(
            title="Compréhension de texte",
            description="Lisez le texte sur les fêtes traditionnelles et répondez aux questions",
            word_count=150,
            subject_id=subject3.id
        )
        task8.save()
        
        return True
    
    return False