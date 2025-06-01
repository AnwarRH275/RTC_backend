from models.exts import db
from datetime import datetime

'''
Modèle pour suivre les tentatives d'examen par utilisateur et par sujet
'''

class TCFAttempt(db.Model):
    __tablename__ = 'tcf_attempt'
    
    id = db.Column(db.Integer(), primary_key=True)
    id_user = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    id_subject = db.Column(db.Integer(), db.ForeignKey('tcf_subject.id'), nullable=False)
    attempt_count = db.Column(db.Integer(), default=0, nullable=False)
    last_attempt_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='attempts')
    subject = db.relationship('TCFSubject', backref='attempts')

    # Contrainte unique pour éviter les doublons
    __table_args__ = (db.UniqueConstraint('id_user', 'id_subject', name='unique_user_subject_attempt'),)

    def __repr__(self):
        return f"<TCFAttempt User:{self.id_user} Subject:{self.id_subject} Count:{self.attempt_count}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def increment_attempt(self):
        """Incrémente le compteur de tentatives"""
        self.attempt_count += 1
        self.last_attempt_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'id_user': self.id_user,
            'id_subject': self.id_subject,
            'attempt_count': self.attempt_count,
            'last_attempt_date': self.last_attempt_date.isoformat() if self.last_attempt_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_or_create_attempt(user_id, subject_id):
        """Récupère ou crée une tentative pour un utilisateur et un sujet"""
        attempt = TCFAttempt.query.filter_by(id_user=user_id, id_subject=subject_id).first()
        if not attempt:
            attempt = TCFAttempt(
                id_user=user_id,
                id_subject=subject_id,
                attempt_count=0
            )
            attempt.save()
        return attempt