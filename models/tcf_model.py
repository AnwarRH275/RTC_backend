from models.exts import db
from datetime import datetime

'''
Modèle pour les sujets TCF (Test de Connaissance du Français)
'''

class TCFSubject(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    date = db.Column(db.String(), nullable=False)  # Date de création au format YYYY-MM-DD
    subscription_plan = db.Column(db.String(), nullable=False)  # Pack Écrit Performance, Pack Écrit Pro, etc.
    status = db.Column(db.String(), nullable=False, default="Actif")  # Actif, Inactif
    duration = db.Column(db.Integer(), nullable=False)  # Durée en minutes
    subject_type = db.Column(db.String(), nullable=False)  # Écrit, Oral
    
    combination = db.Column(db.String(), nullable=True)
    blog = db.Column(db.String(), nullable=True)
    tasks = db.relationship('TCFTask', backref='subject', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TCFSubject {self.name}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
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
            'date': self.date.isoformat() if self.date else None,
            'subscription_plan': self.subscription_plan,
            'status': self.status,
            'duration': self.duration,
            'combination': self.combination,
            'blog': self.blog,
            'subject_type': self.subject_type,
            'tasks': [task.to_dict() for task in self.tasks]
        }


class TCFTask(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    word_count = db.Column(db.Integer(), nullable=True)  # Pour les tâches écrites
    audio_duration = db.Column(db.Integer(), nullable=True)  # Pour les tâches orales (en secondes)
    instructions = db.Column(db.Text(), nullable=True)
    documents_de_reference = db.Column(db.Text(), nullable=True)
    
    # Clé étrangère vers le sujet parent
    subject_id = db.Column(db.Integer(), db.ForeignKey('tcf_subject.id'), nullable=False)

    def __repr__(self):
        return f"<TCFTask {self.title}>"

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, title, description, instructions=None, word_count=None, audio_duration=None):
        self.title = title
        self.description = description
        if instructions is not None:
            self.instructions = instructions
        if word_count is not None:
            self.word_count = word_count
        if audio_duration is not None:
            self.audio_duration = audio_duration
        db.session.commit()
        return self

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
        }
        
        # Ajouter les champs spécifiques selon le type de tâche
        if self.word_count is not None:
            data['word_count'] = self.word_count
        if self.audio_duration is not None:
            data['audio_duration'] = self.audio_duration
            
        return data
