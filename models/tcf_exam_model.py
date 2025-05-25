from models.exts import db
from datetime import datetime

'''
Modèle pour stocker les informations des examens passés par les utilisateurs
'''

class TCFExam(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    id_user = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    id_subject = db.Column(db.Integer(), db.ForeignKey('tcf_subject.id'), nullable=False)
    id_task = db.Column(db.Integer(), db.ForeignKey('tcf_task.id'), nullable=False)
    reponse_utilisateur = db.Column(db.Text(), nullable=True)
    score = db.Column(db.String(), nullable=True) # Score peut être un texte (ex: B2, C1) ou un nombre
    reponse_ia = db.Column(db.Text(), nullable=True)
    points_fort = db.Column(db.Text(), nullable=True)
    point_faible = db.Column(db.Text(), nullable=True)
    traduction_reponse_ia = db.Column(db.Text(), nullable=True)
    date_passage = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='exams')
    subject = db.relationship('TCFSubject', backref='exams')
    task = db.relationship('TCFTask', backref='exams')

    def __repr__(self):
        return f"<TCFExam User:{self.id_user} Subject:{self.id_subject} Task:{self.id_task}>"

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
            'id_user': self.id_user,
            'id_subject': self.id_subject,
            'id_task': self.id_task,
            'reponse_utilisateur': self.reponse_utilisateur,
            'score': self.score,
            'reponse_ia': self.reponse_ia,
            'points_fort': self.points_fort,
            'point_faible': self.point_faible,
            'traduction_reponse_ia': self.traduction_reponse_ia,
            'date_passage': self.date_passage.isoformat() if self.date_passage else None
        }