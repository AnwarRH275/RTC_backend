from models.exts import db
from datetime import datetime
import json

'''
Modèles pour les sujets TCF Expression Orale
'''

class TCFOralSubject(db.Model):
    __tablename__ = 'tcf_oral_subject'
    
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Date de création au format YYYY-MM-DD
    status = db.Column(db.String(20), nullable=False, default="Actif")  # Actif, Inactif
    duration = db.Column(db.Integer(), nullable=True)  # Durée totale en minutes
    subject_type = db.Column(db.String(20), nullable=False, default="Oral")  # Toujours "Oral"
    description = db.Column(db.Text(), nullable=True)  # Description du sujet
    combination = db.Column(db.String(50), nullable=True)
    
    # Relations avec les tâches orales
    oral_tasks = db.relationship('TCFOralTask', backref='subject', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TCFOralSubject {self.name}>"

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        # Supprimer d'abord tous les examens liés à ce sujet
        from .tcf_exam_model import TCFExam
        TCFExam.query.filter_by(id_subject=self.id).delete()
        
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
            'name': self.name,
            'date': self.date,
            'status': self.status,
            'duration': self.duration,
            'combination': self.combination,
            'subject_type': self.subject_type,
            'description': self.description,
            'tasks': [task.to_dict() for task in self.oral_tasks]
        }


class TCFOralTask(db.Model):
    """Table pour les tâches d'examen oral"""
    __tablename__ = 'tcf_oral_task'
    
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # Titre de la tâche
    task_type = db.Column(db.String(50), nullable=False)  # entretien, questions, expression
    objective = db.Column(db.Text(), nullable=True)  # Objectif de la tâche
    trigger = db.Column(db.Text(), nullable=True)  # Déclencheur/consigne
    evaluation_criteria = db.Column(db.Text(), nullable=True)  # Critères d'évaluation
    duration = db.Column(db.Integer(), nullable=False, default=10)  # Durée en minutes
    points = db.Column(db.Integer(), nullable=False, default=25)  # Points attribués
    preparation_time = db.Column(db.Integer(), nullable=False, default=0)  # Temps de préparation en minutes
    roleplay_scenario = db.Column(db.Text(), nullable=True)  # Scénario de jeu de rôle
    
    # Clé étrangère vers le sujet parent
    subject_id = db.Column(db.Integer(), db.ForeignKey('tcf_oral_subject.id'), nullable=False)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TCFOralTask {self.id} - {self.title}>"

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self

    def to_dict(self):
        result = {
            'id': self.id,
            'title': self.title,
            'task_type': self.task_type,
            'objective': self.objective,
            'trigger': self.trigger,
            'evaluation_criteria': self.evaluation_criteria,
            'duration': self.duration,
            'points': self.points,
            'preparation_time': self.preparation_time,
            'roleplay_scenario': self.roleplay_scenario,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        return result