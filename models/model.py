from models.exts import db
from datetime import datetime
'''
    create Recipie

'''


class Recipie(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"<Recipie {self.title} >"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, title, description):
        self.title = title
        self.description = description
        db.session.commit()


'''
Create users Model
'''


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), nullable=False, unique=True)
    email = db.Column(db.String(), nullable=False)
    password = db.Column(db.Text(), nullable=False)
    nom = db.Column(db.Text(), nullable=True)
    prenom = db.Column(db.Text(), nullable=True)
    tel = db.Column(db.Text(), nullable=True)
    sexe = db.Column(db.Text(), nullable=True)
    date_naissance = db.Column(db.Text(), nullable=True)
    date_create = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=True)
    subscription_plan = db.Column(db.String(), nullable=True)  # standard, performance, pro
    payment_status = db.Column(db.String(), default="pending", nullable=True)  # pending, paid
    payment_id = db.Column(db.String(), nullable=True)  # ID de la transaction Stripe
    role = db.Column(db.String(), default="client", nullable=False)
    sold = db.Column(db.Float(), default=0.0, nullable=True)

    def to_dict(self):
        return {
            'email': self.email,
            'username': self.username,
            'nom': self.nom,
            'tel': self.tel,
            'subscription_plan': self.subscription_plan,
            'payment_status': self.payment_status,
            'sold': self.sold
        }

    def __repr__(self) -> str:
        return f"<username {self.username}"

    def update(self, email, nom, tel, sexe, date_naissance):
        self.email = email
        self.nom = nom
        self.tel = tel
        self.date_naissance = date_naissance
        self.sexe = sexe
        db.session.commit()

    def update_subscription(self, plan, payment_status, payment_id):
        self.subscription_plan = plan
        self.payment_status = payment_status
        self.payment_id = payment_id
        db.session.commit()

    def update_sold(self, new_sold_value):
        self.sold = new_sold_value
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()


'''
Create match 
'''
