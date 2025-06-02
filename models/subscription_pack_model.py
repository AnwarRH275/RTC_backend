from models.exts import db
from datetime import datetime


class SubscriptionPack(db.Model):
    """Modèle pour les packs d'abonnement"""
    __tablename__ = 'subscription_packs'
    
    id = db.Column(db.Integer(), primary_key=True)
    pack_id = db.Column(db.String(50), unique=True, nullable=False)  # 'standard', 'performance', 'pro'
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(10), nullable=False)  # Prix affiché (ex: "14")
    price_in_cents = db.Column(db.Integer(), nullable=False)  # Prix en centimes pour Stripe
    usages = db.Column(db.Integer(), nullable=False)  # Nombre d'examens
    color = db.Column(db.String(20), nullable=False)  # Couleur du thème
    is_popular = db.Column(db.Boolean(), default=False)  # Pack populaire
    stripe_product_id = db.Column(db.String(100), nullable=False)  # ID produit Stripe
    
    # Gradients pour les styles
    header_gradient_start = db.Column(db.String(7), nullable=False)  # Couleur de début du gradient header
    header_gradient_end = db.Column(db.String(7), nullable=False)    # Couleur de fin du gradient header
    button_gradient_start = db.Column(db.String(7), nullable=False)  # Couleur de début du gradient bouton
    button_gradient_end = db.Column(db.String(7), nullable=False)    # Couleur de fin du gradient bouton
    button_hover_gradient_start = db.Column(db.String(7), nullable=False)  # Couleur de début du gradient bouton hover
    button_hover_gradient_end = db.Column(db.String(7), nullable=False)    # Couleur de fin du gradient bouton hover
    
    # Métadonnées
    is_active = db.Column(db.Boolean(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    features = db.relationship('PackFeature', backref='pack', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'pack_id': self.pack_id,
            'name': self.name,
            'price': self.price,
            'priceInCents': self.price_in_cents,
            'usages': self.usages,
            'color': self.color,
            'isPopular': self.is_popular,
            'stripeProductId': self.stripe_product_id,
            'headerGradient': {
                'start': self.header_gradient_start,
                'end': self.header_gradient_end
            },
            'buttonGradient': {
                'start': self.button_gradient_start,
                'end': self.button_gradient_end
            },
            'buttonHoverGradient': {
                'start': self.button_hover_gradient_start,
                'end': self.button_hover_gradient_end
            },
            'isActive': self.is_active,
            'features': [feature.to_dict() for feature in self.features],
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f"<SubscriptionPack {self.name}>"


class PackFeature(db.Model):
    """Modèle pour les fonctionnalités des packs"""
    __tablename__ = 'pack_features'
    
    id = db.Column(db.Integer(), primary_key=True)
    pack_id = db.Column(db.Integer(), db.ForeignKey('subscription_packs.id'), nullable=False)
    feature_text = db.Column(db.Text(), nullable=False)
    order_index = db.Column(db.Integer(), default=0)  # Pour l'ordre d'affichage
    is_active = db.Column(db.Boolean(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'featureText': self.feature_text,
            'orderIndex': self.order_index,
            'isActive': self.is_active
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f"<PackFeature {self.feature_text[:50]}>"