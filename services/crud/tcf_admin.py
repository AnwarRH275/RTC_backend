from flask import request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required
from models.tcf_model import TCFSubject, TCFTask, TCFDocument
from models.exts import db

tcf_ns = Namespace('tcf', description='Gestion des sujets TCF')

# Modèle pour les documents
document_model = tcf_ns.model(
    "TCFDocument",
    {
        "id": fields.Integer(),
        "content": fields.String(required=True)
    }
)

# Modèle pour les tâches
task_model = tcf_ns.model(
    "TCFTask",
    {
        "id": fields.Integer(),
        "title": fields.String(required=True),
        "structure": fields.String(),
        "instructions": fields.String(),
        "min_word_count": fields.Integer(),
        "max_word_count": fields.Integer(),
        "duration": fields.Integer(),
        "documents": fields.List(fields.Nested(document_model))
    }
)

# Modèle pour les sujets TCF
tcf_subject_model = tcf_ns.model(
    "TCFSubject",
    {
        "id": fields.Integer(),
        "name": fields.String(required=True),
        "date": fields.String(required=True),
        "status": fields.String(required=True),
        "duration": fields.Integer(required=True),
        "combination": fields.String(required=False),
        "subject_type": fields.String(required=True),
        "description": fields.String(required=False),
        "tasks": fields.List(fields.Nested(task_model))
    }
)

# Modèle pour la création/mise à jour de sujets TCF
tcf_subject_input_model = tcf_ns.model(
    "TCFSubjectInput",
    {
        "name": fields.String(required=True),
        "date": fields.String(required=True),
        "status": fields.String(required=True),
        "duration": fields.Integer(required=True),
        "combination": fields.String(required=False),
        "subject_type": fields.String(required=True),
        "description": fields.String(required=False),
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
            status=data.get('status'),
            duration=data.get('duration'),
            combination=data.get('combination'),
            subject_type=data.get('subject_type'),
            description=data.get('description')
        )
        new_subject.save()
        
        # Ajouter les tâches si présentes
        if 'tasks' in data and data['tasks']:
            for task_data in data['tasks']:
                new_task = TCFTask(
                    title=task_data.get('title'),
                    structure=task_data.get('structure'),
                    instructions=task_data.get('instructions'),
                    min_word_count=task_data.get('min_word_count'),
                    max_word_count=task_data.get('max_word_count'),
                    duration=task_data.get('duration'),
                    subject_id=new_subject.id
                )
                new_task.save()
                
                # Ajouter les documents si présents
                if 'documents' in task_data and task_data['documents']:
                    for doc_data in task_data['documents']:
                        new_document = TCFDocument(
                            content=doc_data.get('content'),
                            task_id=new_task.id
                        )
                        new_document.save()
        
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

        # Mettre à jour les tâches de manière intelligente
        if tasks_data is not None:
            # Créer un dictionnaire des tâches existantes par ID
            existing_tasks = {task.id: task for task in subject.tasks}
            updated_task_ids = set()
            
            # Traiter chaque tâche dans les données reçues
            for task_data in tasks_data:
                task_id = task_data.get('id')
                
                # Ignorer les IDs temporaires (qui commencent par 'temp_')
                if task_id and isinstance(task_id, str) and task_id.startswith('temp_'):
                    task_id = None
                
                if task_id and task_id in existing_tasks:
                    # Mettre à jour la tâche existante
                    existing_task = existing_tasks[task_id]
                    existing_task.update({
                        'title': task_data.get('title'),
                        'structure': task_data.get('structure'),
                        'instructions': task_data.get('instructions'),
                        'min_word_count': task_data.get('min_word_count'),
                        'max_word_count': task_data.get('max_word_count'),
                        'duration': task_data.get('duration')
                    })
                    updated_task_ids.add(task_id)
                    
                    # Mettre à jour les documents de cette tâche
                    if 'documents' in task_data:
                        # Supprimer les anciens documents
                        for doc in existing_task.documents:
                            doc.delete()
                        # Ajouter les nouveaux documents
                        for doc_data in task_data['documents']:
                            new_document = TCFDocument(
                                content=doc_data.get('content'),
                                task_id=existing_task.id
                            )
                            new_document.save()
                else:
                    # Créer une nouvelle tâche
                    new_task = TCFTask(
                        title=task_data.get('title'),
                        structure=task_data.get('structure'),
                        instructions=task_data.get('instructions'),
                        min_word_count=task_data.get('min_word_count'),
                        max_word_count=task_data.get('max_word_count'),
                        duration=task_data.get('duration'),
                        subject_id=subject.id
                    )
                    new_task.save()
                    
                    # Ajouter les documents si présents
                    if 'documents' in task_data and task_data['documents']:
                        for doc_data in task_data['documents']:
                            new_document = TCFDocument(
                                content=doc_data.get('content'),
                                task_id=new_task.id
                            )
                            new_document.save()
            
            # Supprimer les tâches qui ne sont plus dans les données reçues
            for task_id, task in existing_tasks.items():
                if task_id not in updated_task_ids:
                    task.delete()

        return subject

    def delete(self, id):
        '''Supprimer un sujet TCF'''
        from models.tcf_attempt_model import TCFAttempt
        from models.tcf_exam_model import TCFExam
        
        subject = TCFSubject.query.get_or_404(id)
        
        # Supprimer d'abord tous les examens liés à ce sujet
        TCFExam.query.filter_by(id_subject=id).delete()
        
        # Supprimer toutes les tentatives liées à ce sujet
        TCFAttempt.query.filter_by(id_subject=id).delete()
        
        # Maintenant supprimer le sujet
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
            status="Actif",
            duration=60,
            combination="N5",
            subject_type="Écrit",
            description="Sujet sur l'environnement et le développement durable"
        )
        subject1.save()
        
        # Tâches pour le sujet 1
        task1 = TCFTask(
            title="Rédaction d'un essai",
            structure="Introduction, développement, conclusion",
            instructions="Rédigez un essai sur l'importance du développement durable",
            min_word_count=250,
            max_word_count=350,
            subject_id=subject1.id
        )
        task1.save()
        
        # Document pour la tâche 1
        doc1 = TCFDocument(
            content="Document de référence sur le développement durable et ses enjeux actuels.",
            task_id=task1.id
        )
        doc1.save()
        
        task2 = TCFTask(
            title="Analyse de document",
            structure="Analyse structurée avec arguments",
            instructions="Analysez le document fourni sur les énergies renouvelables",
            min_word_count=150,
            max_word_count=250,
            subject_id=subject1.id
        )
        task2.save()
        
        task3 = TCFTask(
            title="Questions à choix multiples",
            structure="Réponses courtes et précises",
            instructions="Répondez aux questions sur le texte",
            min_word_count=50,
            max_word_count=150,
            subject_id=subject1.id
        )
        task3.save()
        
        # Sujet 2: Technologie et société
        subject2 = TCFSubject(
            name="Technologie et société",
            date="2023-11-20",
            status="Actif",
            duration=60,
            combination="N6",
            subject_type="Écrit",
            description="Sujet sur l'impact des technologies sur la société"
        )
        subject2.save()
        
        # Tâches pour le sujet 2
        task4 = TCFTask(
            title="Dissertation",
            structure="Introduction, développement en 3 parties, conclusion",
            instructions="Rédigez une dissertation sur l'impact des technologies sur la société",
            min_word_count=300,
            max_word_count=400,
            subject_id=subject2.id
        )
        task4.save()
        
        task5 = TCFTask(
            title="Résumé de texte",
            structure="Résumé structuré et synthétique",
            instructions="Résumez le texte sur l'intelligence artificielle",
            min_word_count=100,
            max_word_count=200,
            subject_id=subject2.id
        )
        task5.save()
        
        task6 = TCFTask(
            title="Exercice de vocabulaire",
            structure="Réponses précises et justifiées",
            instructions="Complétez les phrases avec le vocabulaire technique approprié",
            min_word_count=50,
            max_word_count=150,
            subject_id=subject2.id
        )
        task6.save()
        
        # Sujet 3: Culture et traditions
        subject3 = TCFSubject(
            name="Culture et traditions",
            date="2023-12-05",
            status="Inactif",
            duration=45,
            combination="O5",
            subject_type="Écrit",
            description="Sujet sur les cultures et traditions"
        )
        subject3.save()
        
        # Tâches pour le sujet 3
        task7 = TCFTask(
            title="Expression écrite",
            structure="Description détaillée et personnelle",
            instructions="Décrivez une tradition culturelle de votre pays",
            min_word_count=150,
            max_word_count=250,
            subject_id=subject3.id
        )
        task7.save()
        
        task8 = TCFTask(
            title="Compréhension de texte",
            structure="Questions-réponses structurées",
            instructions="Lisez le texte sur les fêtes traditionnelles et répondez aux questions",
            min_word_count=100,
            max_word_count=200,
            subject_id=subject3.id
        )
        task8.save()
        
        # Ajouter des documents d'exemple pour certaines tâches
        doc1 = TCFDocument(
            content="Texte de référence sur les technologies émergentes et leur impact sur la société moderne.",
            task_id=task4.id
        )
        doc1.save()
        
        doc2 = TCFDocument(
            content="Article sur l'intelligence artificielle et ses applications dans différents domaines.",
            task_id=task5.id
        )
        doc2.save()
        
        doc3 = TCFDocument(
            content="Texte descriptif sur les fêtes traditionnelles du monde entier.",
            task_id=task8.id
        )
        doc3.save()
        
        return True
    
    return False