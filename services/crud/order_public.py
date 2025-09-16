from flask import request, jsonify, make_response, current_app
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.model import User
from models.order_model import Order
from models.subscription_pack_model import SubscriptionPack
from models.exts import db
from datetime import datetime
import uuid

# Créer un namespace pour les routes publiques des commandes
order_public_ns = Namespace('orders', description='Gestion publique des commandes')

# Modèles pour la documentation API
order_create_model = order_public_ns.model(
    "OrderCreate",
    {
        "subscriptionPlan": fields.String(required=True, description="Plan d'abonnement"),
        "amount": fields.Float(required=True, description="Montant"),
        "currency": fields.String(required=True, description="Devise (ex: CAD)"),
        "customerEmail": fields.String(required=True, description="Email du client"),
        "customerName": fields.String(required=True, description="Nom du client"),
        "customerPhone": fields.String(description="Téléphone du client"),
        "paymentMethod": fields.String(description="Méthode de paiement")
    }
)

order_response_model = order_public_ns.model(
    "OrderResponse",
    {
        "id": fields.Integer(description="ID de la commande"),
        "orderNumber": fields.String(description="Numéro de commande"),
        "userId": fields.Integer(description="ID de l'utilisateur"),
        "subscriptionPlan": fields.String(description="Plan d'abonnement"),
        "amount": fields.Float(description="Montant"),
        "currency": fields.String(description="Devise"),
        "status": fields.String(description="Statut de la commande"),
        "paymentStatus": fields.String(description="Statut du paiement"),
        "customerEmail": fields.String(description="Email du client"),
        "customerName": fields.String(description="Nom du client"),
        "createdAt": fields.String(description="Date de création")
    }
)

@order_public_ns.route('/create')
class OrderCreate(Resource):
    @jwt_required()
    @order_public_ns.expect(order_create_model)
    def post(self):
        """Créer une nouvelle commande"""
        try:
            # Récupérer l'utilisateur connecté
            current_username = get_jwt_identity()
            user = User.query.filter_by(username=current_username).first()
            
            if not user:
                return make_response(jsonify({"error": "Utilisateur non trouvé"}), 404)
            
            # Récupérer les données de la requête
            data = request.get_json()
            
            if not data:
                return make_response(jsonify({"error": "Données manquantes"}), 400)
            
            # Validation des champs requis
            required_fields = ['subscriptionPlan', 'amount', 'currency', 'customerEmail', 'customerName']
            for field in required_fields:
                if field not in data or not data[field]:
                    return make_response(jsonify({"error": f"Le champ '{field}' est requis"}), 400)
            
            # Vérifier que le plan d'abonnement existe
            subscription_pack = SubscriptionPack.query.filter_by(pack_id=data['subscriptionPlan']).first()
            if not subscription_pack:
                return make_response(jsonify({"error": "Plan d'abonnement non trouvé"}), 400)
            
            # Vérifier s'il existe déjà une commande en attente pour cet utilisateur et ce plan
            existing_pending_order = Order.query.filter_by(
                user_id=user.id,
                subscription_plan=data['subscriptionPlan'],
                status='pending'
            ).first()
            
            if existing_pending_order:
                current_app.logger.info(f"Commande en attente existante trouvée: {existing_pending_order.order_number}")
                order = existing_pending_order
                # Mettre à jour les informations si nécessaire
                order.customer_email = data['customerEmail']
                order.customer_name = data['customerName']
                order.customer_phone = data.get('customerPhone')
                order.updated_at = datetime.utcnow()
                db.session.commit()
            else:
                # Créer une nouvelle commande
                # Convertir le montant de centimes en dollars si nécessaire
                amount = float(data['amount'])
                # Si le montant semble être en centimes (> 100), le convertir en dollars
                if amount > 100:
                    amount = amount / 100
                
                order = Order(
                    user_id=user.id,
                    subscription_plan=data['subscriptionPlan'],
                    amount=amount,
                    currency=data['currency'],
                    status='pending',  # Statut initial
                    payment_status='pending',
                    customer_email=data['customerEmail'],
                    customer_name=data['customerName'],
                    customer_phone=data.get('customerPhone'),
                    payment_method=data.get('paymentMethod', 'stripe'),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Générer le numéro de commande
                order.order_number = order.generate_order_number()
                current_app.logger.info(f"Numéro de commande généré: {order.order_number}")
                
                # Sauvegarder en base de données
                db.session.add(order)
                current_app.logger.info(f"Commande ajoutée à la session, tentative de commit...")
                db.session.commit()
                current_app.logger.info(f"Commit réussi, ID de commande: {order.id}")
                
                current_app.logger.info(f"Commande créée avec succès: {order.order_number} pour l'utilisateur {user.email}")
            
            return {
                "id": order.id,
                "orderNumber": order.order_number,
                "userId": order.user_id,
                "subscriptionPlan": order.subscription_plan,
                "amount": order.amount,
                "currency": order.currency,
                "status": order.status,
                "paymentStatus": order.payment_status,
                "customerEmail": order.customer_email,
                "customerName": order.customer_name,
                "createdAt": order.created_at.isoformat() if order.created_at else None,
                "message": "Commande créée avec succès"
            }, 201
            
        except ValueError as ve:
            current_app.logger.error(f"Erreur de validation lors de la création de commande: {str(ve)}")
            return make_response(jsonify({"error": f"Erreur de validation: {str(ve)}"}), 400)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de commande: {str(e)}")
            return make_response(jsonify({"error": "Erreur interne du serveur"}), 500)


@order_public_ns.route('/update-status')
class OrderUpdateStatus(Resource):
    @jwt_required()
    def post(self):
        """Mettre à jour le statut d'une commande après paiement réussi"""
        try:
            data = request.get_json()
            
            # Récupérer l'utilisateur actuel
            current_username = get_jwt_identity()
            user = User.query.filter_by(username=current_username).first()
            
            if not user:
                return make_response(jsonify({"error": "Utilisateur non trouvé"}), 404)
            
            # Récupérer les paramètres
            order_id = data.get('orderId')
            stripe_session_id = data.get('stripeSessionId')
            payment_intent_id = data.get('paymentIntentId')
            
            if not order_id and not stripe_session_id:
                return make_response(jsonify({"error": "ID de commande ou session Stripe requis"}), 400)
            
            # Trouver la commande
            if order_id:
                order = Order.query.filter_by(id=order_id, user_id=user.id).first()
            else:
                order = Order.query.filter_by(stripe_session_id=stripe_session_id, user_id=user.id).first()
            
            if not order:
                return make_response(jsonify({"error": "Commande non trouvée"}), 404)
            
            # Mettre à jour le statut si la commande est en attente
            if order.status == 'pending':
                order.status = 'paid'
                order.payment_status = 'completed'
                order.paid_at = datetime.utcnow()
                order.updated_at = datetime.utcnow()
                
                # Ajouter les informations Stripe si fournies
                if stripe_session_id:
                    order.stripe_session_id = stripe_session_id
                if payment_intent_id:
                    order.stripe_payment_intent_id = payment_intent_id
                
                # Mettre à jour le plan d'abonnement de l'utilisateur
                subscription_pack = SubscriptionPack.query.filter_by(
                    pack_id=order.subscription_plan, 
                    is_active=True
                ).first()
                
                if subscription_pack:
                    # Sauvegarder l'ancien plan pour le log
                    old_plan = user.subscription_plan
                    old_sold = user.sold
                    old_total_sold = user.total_sold
                    
                    # Vérifier si l'utilisateur a déjà ce plan actif pour éviter les doublons de crédits
                    user_has_active_plan = user.subscription_plan is not None and user.subscription_plan != ''
                    should_add_credits = not user_has_active_plan or old_plan != order.subscription_plan
                    
                    # Mettre à jour le plan d'abonnement
                    user.subscription_plan = order.subscription_plan
                    user.payment_status = "paid"
                    user.payment_id = stripe_session_id or str(order.id)
                    
                    # Ajouter les nouveaux usages seulement si nécessaire
                    if should_add_credits:
                        new_usages = float(subscription_pack.usages)
                        user.sold += new_usages
                        user.total_sold += new_usages
                        current_app.logger.info(
                            f"Nouveaux crédits ajoutés: {new_usages} pour le plan {order.subscription_plan}"
                        )
                    else:
                        current_app.logger.info(
                            f"Utilisateur a déjà le plan {order.subscription_plan}, aucun crédit supplémentaire ajouté"
                        )
                    
                    current_app.logger.info(
                        f"Plan mis à jour pour l'utilisateur {user.id}: "
                        f"{old_plan} -> {order.subscription_plan}, "
                        f"Sold: {old_sold} -> {user.sold}, "
                        f"Total: {old_total_sold} -> {user.total_sold}"
                    )
                
                db.session.commit()
                
                current_app.logger.info(f"Commande {order.order_number} mise à jour: statut -> paid")
                
                # Note: L'email de bienvenue est maintenant envoyé automatiquement
                # via le webhook Stripe dans stripe.py lors du paiement réussi
                current_app.logger.info(f"Statut de commande mis à jour: {order.order_number} -> {new_status}")
                
                return {
                    "message": "Statut de commande mis à jour avec succès",
                    "order": {
                        "id": order.id,
                        "orderNumber": order.order_number,
                        "status": order.status,
                        "paymentStatus": order.payment_status,
                        "amount": order.amount,
                        "currency": order.currency,
                        "paidAt": order.paid_at.isoformat() if order.paid_at else None
                    }
                }, 200
            else:
                return {
                    "message": "Commande déjà traitée",
                    "status": order.status
                }, 200
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}")
            return make_response(jsonify({"error": "Erreur interne du serveur"}), 500)

@order_public_ns.route('/my-orders')
class MyOrders(Resource):
    @jwt_required()
    def get(self):
        """Récupérer les commandes de l'utilisateur connecté"""
        try:
            current_username = get_jwt_identity()
            user = User.query.filter_by(username=current_username).first()
            
            if not user:
                return make_response(jsonify({"error": "Utilisateur non trouvé"}), 404)
            
            # Paramètres de pagination
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            
            # Récupérer les commandes de l'utilisateur
            orders_query = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc())
            
            # Pagination
            orders = orders_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return make_response(jsonify({
                "orders": [order.to_dict() for order in orders.items],
                "pagination": {
                    "page": orders.page,
                    "pages": orders.pages,
                    "perPage": orders.per_page,
                    "total": orders.total
                }
            }), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des commandes utilisateur: {str(e)}")
            return make_response(jsonify({"error": "Erreur interne du serveur"}), 500)

@order_public_ns.route('/<int:order_id>')
class OrderDetail(Resource):
    @jwt_required()
    def get(self, order_id):
        """Récupérer les détails d'une commande (seulement si elle appartient à l'utilisateur)"""
        try:
            current_username = get_jwt_identity()
            user = User.query.filter_by(username=current_username).first()
            
            if not user:
                return make_response(jsonify({"error": "Utilisateur non trouvé"}), 404)
            
            # Récupérer la commande seulement si elle appartient à l'utilisateur
            order = Order.query.filter_by(id=order_id, user_id=user.id).first()
            
            if not order:
                return make_response(jsonify({"error": "Commande non trouvée"}), 404)
            
            return make_response(jsonify(order.to_dict()), 200)
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération de la commande: {str(e)}")
            return make_response(jsonify({"error": "Erreur interne du serveur"}), 500)