from models.exts import db
from datetime import datetime
import uuid
from models.model import User  # Ajout de l'import manquant
from flask import current_app


class Order(db.Model):
    """Modèle pour les commandes/transactions financières"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer(), primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    
    # Informations sur la commande
    subscription_plan = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Statut de la commande
    status = db.Column(db.String(20), default='pending', nullable=False)
    payment_status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Informations de paiement
    payment_method = db.Column(db.String(50), nullable=True)
    stripe_session_id = db.Column(db.String(200), nullable=True)
    stripe_payment_intent_id = db.Column(db.String(200), nullable=True)
    stripe_charge_id = db.Column(db.String(200), nullable=True)
    
    # Informations client
    customer_email = db.Column(db.String(120), nullable=False)
    customer_name = db.Column(db.String(200), nullable=True)
    customer_phone = db.Column(db.String(50), nullable=True)
    
    # Métadonnées
    notes = db.Column(db.Text(), nullable=True)
    refund_reason = db.Column(db.Text(), nullable=True)
    cancelled_by = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by], backref='cancelled_orders')
    
    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @staticmethod
    def generate_order_number():
        """Génère un numéro de commande unique au format Ordre#0001000"""
        from models.exts import db
        
        # Trouver le dernier numéro de commande pour déterminer le prochain
        last_order = db.session.query(Order).filter(
            Order.order_number.like('Ordre#%')
        ).order_by(Order.id.desc()).first()
        
        if last_order and last_order.order_number:
            # Extraire le numéro de la dernière commande
            try:
                last_number = int(last_order.order_number.split('#')[1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                # En cas d'erreur, commencer à 1000
                next_number = 1000
        else:
            # Première commande, commencer à 1000
            next_number = 1000
        
        # Formater avec des zéros à gauche (7 chiffres)
        return f"Ordre#{next_number:07d}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'orderNumber': self.order_number,
            'userId': self.user_id,
            'subscriptionPlan': self.subscription_plan,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'paymentStatus': self.payment_status,
            'paymentMethod': self.payment_method,
            'stripeSessionId': self.stripe_session_id,
            'stripePaymentIntentId': self.stripe_payment_intent_id,
            'stripeChargeId': self.stripe_charge_id,
            'customerEmail': self.customer_email,
            'customerName': self.customer_name,
            'customerPhone': self.customer_phone,
            'notes': self.notes,
            'refundReason': self.refund_reason,
            'cancelledBy': self.cancelled_by,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'paidAt': self.paid_at.isoformat() if self.paid_at else None,
            'cancelledAt': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'refundedAt': self.refunded_at.isoformat() if self.refunded_at else None
        }
    
    def save(self):
        """Sauvegarde l'ordre dans la base de données"""
        db.session.add(self)
        db.session.commit()
    
    def update_status(self, new_status, admin_user_id=None):
        """Met à jour le statut de la commande"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == 'paid':
            self.payment_status = 'completed'
            self.paid_at = datetime.utcnow()
        elif new_status == 'cancelled':
            self.cancelled_at = datetime.utcnow()
            if admin_user_id:
                self.cancelled_by = admin_user_id
        elif new_status == 'refunded':
            self.payment_status = 'refunded'
            self.refunded_at = datetime.utcnow()
        
        db.session.commit()
    
    def update_payment_status_from_stripe(self, stripe_session, validate_amount=True):
        """Met à jour le statut de paiement de manière sécurisée à partir des données Stripe"""
        try:
            # Validation des données Stripe
            if not stripe_session or 'payment_status' not in stripe_session:
                raise ValueError("Données Stripe invalides")
            
            payment_status = stripe_session.get('payment_status')
            
            # Validation du montant si demandé
            if validate_amount:
                stripe_amount = stripe_session.get('amount_total', 0) / 100
                if abs(self.amount - stripe_amount) > 0.01:  # Tolérance de 0.01
                    current_app.logger.warning(
                        f"Montant Stripe ({stripe_amount}) différent du montant commande ({self.amount}) "
                        f"pour la commande {self.order_number}"
                    )
            
            # Mise à jour sécurisée du statut
            if payment_status == 'paid':
                # Éviter les mises à jour redondantes
                if self.status == 'paid' and self.payment_status == 'completed':
                    return False, "Commande déjà marquée comme payée"
                
                self.status = 'paid'
                self.payment_status = 'completed'
                self.paid_at = datetime.utcnow()
                
                # Mise à jour des identifiants Stripe
                if stripe_session.get('payment_intent'):
                    self.stripe_payment_intent_id = stripe_session['payment_intent']
                    self.stripe_charge_id = stripe_session['payment_intent']
                
                # Synchronisation des informations client
                customer_email = stripe_session.get('customer_email')
                if customer_email and customer_email != self.customer_email:
                    self.customer_email = customer_email
                
                self.updated_at = datetime.utcnow()
                db.session.commit()
                
                return True, f"Statut de paiement mis à jour pour la commande {self.order_number}"
                
            elif payment_status == 'unpaid':
                if self.status == 'pending' and self.payment_status == 'pending':
                    return False, "Commande déjà marquée comme en attente"
                
                self.status = 'pending'
                self.payment_status = 'pending'
                self.updated_at = datetime.utcnow()
                db.session.commit()
                
                return True, f"Statut de paiement mis à jour comme en attente pour la commande {self.order_number}"
                
            else:
                return False, f"Statut de paiement Stripe inconnu: {payment_status}"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la mise à jour du statut: {str(e)}"
    
    def sync_with_stripe_session(self, stripe_session):
        """Synchronise complètement la commande avec les données Stripe"""
        try:
            success, message = self.update_payment_status_from_stripe(stripe_session)
            
            if success:
                current_app.logger.info(message)
            else:
                current_app.logger.warning(message)
                
            return success, message
            
        except Exception as e:
            return False, f"Erreur de synchronisation: {str(e)}"
    
    def cancel_order(self, cancelled_by_user_id, reason=None, reset_user_balance=False):
        """Annule une commande"""
        try:
            if self.status == 'cancelled':
                return False, "Cette commande est déjà annulée"
            
            if self.status == 'completed':
                return False, "Impossible d'annuler une commande terminée"
            
            # Mettre à jour le statut de la commande
            self.status = 'cancelled'
            self.payment_status = 'cancelled'
            self.cancelled_by = cancelled_by_user_id
            self.cancelled_at = datetime.utcnow()
            
            if reason:
                self.refund_reason = reason
            
            # Remettre le solde utilisateur à zéro si demandé
            if reset_user_balance and self.user:
                from models.model import User
                user = User.query.get(self.user_id)
                if user:
                    user.balance = 0.0
                    db.session.add(user)
            
            db.session.add(self)
            db.session.commit()
            
            return True, "Commande annulée avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'annulation: {str(e)}"
    
    @classmethod
    def get_by_order_number(cls, order_number):
        """Récupère une commande par son numéro"""
        return cls.query.filter_by(order_number=order_number).first()
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """Récupère toutes les commandes d'un utilisateur"""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_by_status(cls, status):
        """Récupère toutes les commandes par statut"""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def get_orders_by_date_range(cls, start_date, end_date):
        """Récupère les commandes dans une plage de dates"""
        return cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).all()
    
    @classmethod
    def get_revenue_stats(cls, start_date=None, end_date=None):
        """Calcule les statistiques de revenus"""
        query = cls.query.filter(cls.status.in_(['paid', 'completed']))
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        orders = query.all()
        
        total_revenue = sum(order.amount for order in orders)
        total_orders = len(orders)
        
        plans_stats = {}
        for order in orders:
            plan = order.subscription_plan
            if plan not in plans_stats:
                plans_stats[plan] = {'count': 0, 'revenue': 0}
            plans_stats[plan]['count'] += 1
            plans_stats[plan]['revenue'] += order.amount
        
        return {
            'totalRevenue': total_revenue,
            'totalOrders': total_orders,
            'averageOrderValue': total_revenue / total_orders if total_orders > 0 else 0,
            'planStats': plans_stats
        }

    @classmethod
    def get_plan_statistics(cls):
        """Statistiques par plan d'abonnement"""
        from sqlalchemy import func
        from models.model import User
        
        # Jointure avec la table User pour obtenir les plans
        plan_stats = db.session.query(
            User.subscription_plan,
            func.count(cls.id).label('order_count'),
            func.sum(cls.amount).label('total_revenue')
        ).join(User, cls.user_id == User.id).filter(
            cls.status == 'paid'
        ).group_by(User.subscription_plan).all()
        
        result = {}
        for plan, count, revenue in plan_stats:
            result[plan or 'unknown'] = {
                'order_count': count,
                'total_revenue': float(revenue or 0)
            }
        
        return result
    
    def __repr__(self):
        return f"<Order {self.order_number}>"