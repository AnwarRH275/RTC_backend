from models.exts import db
from datetime import datetime, timedelta
import secrets




'''
Create users Model
'''


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.Text(), nullable=False)
    nom = db.Column(db.Text(), nullable=True)
    prenom = db.Column(db.Text(), nullable=True)
    tel = db.Column(db.Text(), nullable=True)
    sexe = db.Column(db.String(10), nullable=True)
    date_naissance = db.Column(db.String(20), nullable=True)
    date_create = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=True)
    subscription_plan = db.Column(db.String(50), nullable=True)  # standard, performance, pro
    payment_status = db.Column(db.String(20), default="pending", nullable=True)  # pending, paid
    payment_id = db.Column(db.String(100), nullable=True)  # ID de la transaction Stripe
    role = db.Column(db.String(20), default="client", nullable=False)
    sold = db.Column(db.Float(), default=0.0, nullable=True)
    total_sold = db.Column(db.Float(), default=0.0, nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(80), nullable=True)  # Username du modérateur qui a créé cet utilisateur

    def to_dict(self):
        return {
            'email': self.email,
            'role': self.role,
            'id': self.id,
            'date_create': self.date_create.isoformat() if self.date_create else None,
            'prenom': self.prenom,
            'username': self.username,
            'nom': self.nom,
            'tel': self.tel,
            'subscription_plan': self.subscription_plan,
            'payment_status': self.payment_status,
            'sold': self.sold,
            'total_sold': self.total_sold,
            'created_by': self.created_by
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
        
        # Mettre à jour automatiquement sold et total_sold selon le nouveau plan
        from models.subscription_pack_model import SubscriptionPack
        pack = SubscriptionPack.query.filter_by(pack_id=plan, isActive=True).first()
        if pack:
            # Calculer le ratio d'usage actuel pour préserver le progrès
            current_ratio = 0
            if self.total_sold and self.total_sold > 0:
                current_ratio = self.sold / self.total_sold
            
            # Mettre à jour total_sold avec les nouveaux usages du pack
            self.total_sold = float(pack.usages)
            
            # Mettre à jour sold en préservant le ratio d'usage
            self.sold = self.total_sold * current_ratio
            
            # S'assurer que sold ne dépasse pas total_sold
            if self.sold > self.total_sold:
                self.sold = self.total_sold
        
        db.session.commit()

    def update_sold(self, new_sold_value):
        self.sold = new_sold_value
        db.session.commit()

    def update_total_sold(self, new_total_sold_value):
        self.total_sold = new_total_sold_value
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def generate_reset_token(self):
        """Génère un token de réinitialisation de mot de passe"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Expire dans 1 heure
        db.session.commit()
        return self.reset_token
    
    @classmethod
    def verify_reset_token(cls, token):
        """Trouve et vérifie un utilisateur par son token de réinitialisation"""
        user = cls.query.filter_by(reset_token=token).first()
        if not user:
            return None
            
        if not user.reset_token_expires or datetime.utcnow() > user.reset_token_expires:
            return None
            
        return user
    
    def clear_reset_token(self):
        """Efface le token de réinitialisation après utilisation"""
        self.reset_token = None
        self.reset_token_expires = None
        db.session.commit()


'''
Create match 
'''
