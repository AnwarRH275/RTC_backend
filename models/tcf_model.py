from models.exts import db
from datetime import datetime

'''
Modèle pour les sujets TCF (Test de Connaissance du Français)
'''

class TCFSubject(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    date = db.Column(db.String(), nullable=False)  # Date de création au format YYYY-MM-DD
    status = db.Column(db.String(), nullable=False, default="Actif")  # Actif, Inactif
    duration = db.Column(db.Integer(), nullable=False)  # Durée en minutes
    subject_type = db.Column(db.String(), nullable=False)  # Écrit, Oral
    description = db.Column(db.Text(), nullable=True)  # Description du sujet
    
    combination = db.Column(db.String(), nullable=True)
    tasks = db.relationship('TCFTask', backref='subject', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TCFSubject {self.name}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        # Supprimer d'abord tous les examens liés à cette tâche
        from .tcf_exam_model import TCFExam
        TCFExam.query.filter_by(id_task=self.id).delete()
        
        db.session.delete(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'status': self.status,
            'duration': self.duration,
            'combination': self.combination,
            'subject_type': self.subject_type,
            'description': self.description,
            'tasks': [task.to_dict() for task in self.tasks]
        }


class TCFTask(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    structure = db.Column(db.Text(), nullable=True)  # Structure à respecter
    instructions = db.Column(db.Text(), nullable=True)  # Instructions spécifiques
    min_word_count = db.Column(db.Integer(), nullable=True)  # Nombre de mots minimum
    max_word_count = db.Column(db.Integer(), nullable=True)  # Nombre de mots maximum
    duration = db.Column(db.Integer(), nullable=True)  # Durée en minutes
    
    # Clé étrangère vers le sujet parent
    subject_id = db.Column(db.Integer(), db.ForeignKey('tcf_subject.id'), nullable=False)
    
    # Relation avec les documents
    documents = db.relationship('TCFDocument', backref='task', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TCFTask {self.title}>"

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        # Supprimer d'abord tous les examens liés à cette tâche
        from .tcf_exam_model import TCFExam
        TCFExam.query.filter_by(id_task=self.id).delete()
        
        db.session.delete(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'structure': self.structure,
            'instructions': self.instructions,
            'min_word_count': self.min_word_count,
            'max_word_count': self.max_word_count,
            'duration': self.duration,
            'documents': [doc.to_dict() for doc in self.documents]
        }


class TCFDocument(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    content = db.Column(db.Text(), nullable=False)  # Contenu textuel du document
    
    # Clé étrangère vers la tâche parent
    task_id = db.Column(db.Integer(), db.ForeignKey('tcf_task.id'), nullable=False)

    def __repr__(self):
        return f"<TCFDocument {self.id}>"

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        # Supprimer d'abord tous les examens liés à cette tâche
        from .tcf_exam_model import TCFExam
        TCFExam.query.filter_by(id_task=self.id).delete()
        
        db.session.delete(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content
        }
