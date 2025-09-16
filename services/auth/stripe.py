import stripe
from flask import request, jsonify, make_response, current_app
import traceback
from flask_restx import Resource, Namespace, fields
from models.model import User
from models.order_model import Order
from models.exts import db
from datetime import datetime

# La clé API Stripe sera configurée dynamiquement lors de l'initialisation de l'application
# Voir la fonction init_stripe() ci-dessous

def init_stripe():
    """Initialise Stripe avec la clé API appropriée selon le mode configuré"""
    mode = current_app.config.get('STRIPE_MODE', 'test')
    
    if mode == 'live':
        stripe.api_key = current_app.config.get('STRIPE_LIVE_SECRET_KEY')
        webhook_secret = current_app.config.get('STRIPE_LIVE_WEBHOOK_SECRET')
    else:  # mode test par défaut
        stripe.api_key = current_app.config.get('STRIPE_TEST_SECRET_KEY')
        webhook_secret = current_app.config.get('STRIPE_TEST_WEBHOOK_SECRET')
    
    return webhook_secret

# Créer un namespace pour les routes Stripe
stripe_ns = Namespace('stripe', description='namespace pour les opérations Stripe')

# Modèle pour la création d'une session de paiement
payment_session_model = stripe_ns.model(
    "PaymentSession",
    {
        "productId": fields.String(required=True, description="ID du produit Stripe"),
        "planName": fields.String(required=True, description="Nom du plan d'abonnement"),
        "priceInCents": fields.Integer(required=True, description="Prix en centimes"),
        "email": fields.String(required=True, description="Email de l'utilisateur"),
        "userId": fields.String(required=True, description="ID de l'utilisateur"),
        "successUrl": fields.String(required=True, description="URL de redirection en cas de succès"),
        "cancelUrl": fields.String(required=True, description="URL de redirection en cas d'annulation"),
        "couponCode": fields.String(required=False, description="Code de coupon Stripe (optionnel)"),
    }
)

# Modèle pour la vérification du paiement
payment_verify_model = stripe_ns.model(
    "PaymentVerify",
    {
        "session_id": fields.String(required=True, description="ID de la session de paiement Stripe"),
    }
)



@stripe_ns.route('/create-checkout-session')
class StripeCheckoutSession(Resource):
    @stripe_ns.expect(payment_session_model)
    @stripe_ns.doc(security=None)  # Désactive la sécurité pour cet endpoint
    def post(self):
        """Créer une session de paiement Stripe avec un produit existant"""
        # Initialiser Stripe avec la bonne clé API
        init_stripe()
        
        data = request.get_json()
        product_id = data.get('productId')
        plan_name = data.get('planName')
        price_in_cents = data.get('priceInCents')
        user_email = data.get('email')
        user_id = data.get('userId')
        success_url = data.get('successUrl')
        cancel_url = data.get('cancelUrl')
        coupon_code = data.get('couponCode')

        if not user_email:
            return make_response(jsonify({"error": "Email de l'utilisateur manquant"}), 400)

        # Optionnel: Ajouter une validation basique du format de l'email si nécessaire
        # Exemple simple (peut être amélioré avec une regex plus robuste):
        if '@' not in user_email or '.' not in user_email:
             return make_response(jsonify({"error": "Format d'email invalide"}), 400)

        try:
            # Toujours créer un nouveau prix one-time pour éviter les erreurs de prix récurrents
            price = stripe.Price.create(
                product=product_id,
                unit_amount=price_in_cents,
                currency=current_app.config.get('STRIPE_CURRENCY', 'usd'),
                # S'assurer que c'est un prix one-time (pas récurrent)
                recurring=None
            )
            price_id = price.id
            
            # Préparer les paramètres de la session de paiement
            session_params = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'customer_email': user_email,
                'allow_promotion_codes': True,
                'metadata': {
                    'user_id': user_id,
                    'product_id': product_id,
                    'plan_name': plan_name
                }
            }
            
            # Ajouter le coupon si fourni
            if coupon_code:
                try:
                    # Vérifier que le coupon existe dans Stripe
                    coupon = stripe.Coupon.retrieve(coupon_code)
                    session_params['discounts'] = [{
                        'coupon': coupon_code
                    }]
                    current_app.logger.info(f"Coupon {coupon_code} appliqué à la session")
                except stripe.error.InvalidRequestError as e:
                    current_app.logger.warning(f"Coupon {coupon_code} invalide: {str(e)}")
                    # Continuer sans le coupon si invalide
                except Exception as e:
                    current_app.logger.error(f"Erreur lors de la vérification du coupon {coupon_code}: {str(e)}")
                    # Continuer sans le coupon en cas d'erreur
            
            # Créer la session de paiement Stripe
            checkout_session = stripe.checkout.Session.create(**session_params)
            
            return make_response(jsonify({
                "sessionId": checkout_session.id,
                "url": checkout_session.url
            }), 200)
            
        except Exception as e:
            current_app.logger.error("Erreur lors de la création de la session de paiement Stripe:", exc_info=True)
            return make_response(jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500)

@stripe_ns.route('/verify-payment')
class StripeVerifyPayment(Resource):
    @stripe_ns.expect(payment_verify_model)
    def post(self):
        """Vérifier le statut d'un paiement Stripe et mettre à jour l'utilisateur si nécessaire"""
        # Initialiser Stripe avec la bonne clé API
        init_stripe()
        
        data = request.get_json()
        session_id = data.get('session_id')
        
        try:
            # Récupérer la session de paiement
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # Vérifier si le paiement a été effectué
            if checkout_session.payment_status == 'paid':
                # Récupérer les métadonnées pour mettre à jour l'utilisateur et la commande
                user_id = checkout_session.metadata.get('user_id')
                plan_name = checkout_session.metadata.get('plan_name')
                
                # Synchroniser le statut de paiement avec la base de données
                order_updated = update_order_payment_status(checkout_session)
                
                return make_response(jsonify({
                    "status": "success",
                    "message": "Paiement réussi. Commande et utilisateur mis à jour.",
                    "order_updated": order_updated,
                    "user_updated": True
                }), 200)
            else:
                # Mettre à jour le statut de la commande même si le paiement est en attente
                update_order_payment_status(checkout_session)
                return make_response(jsonify({
                    "status": "pending",
                    "message": "Paiement en attente"
                }), 200)
                
        except Exception as e:
            current_app.logger.error("Erreur lors de la vérification du paiement Stripe:", exc_info=True)
            return make_response(jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500)

# Webhook pour recevoir les événements Stripe
@stripe_ns.route('/webhook')
class StripeWebhook(Resource):
    def post(self):
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        # Récupérer la clé secrète du webhook selon le mode
        webhook_secret = init_stripe()
        
        try:
            # Vérifier la signature de l'événement
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Gérer l'événement
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                
                # Récupérer les métadonnées de la session
                metadata = session.get('metadata', {})
                user_id = metadata.get('user_id')
                plan_name = metadata.get('plan_name')
                product_id = metadata.get('product_id')
                customer_email = session.get('customer_email')
                
                current_app.logger.info(
                    f"Webhook reçu - Session: {session.get('id')}, "
                    f"User ID: {user_id}, Plan: {plan_name}, Email: {customer_email}"
                )
                
                if user_id and plan_name:
                    # Synchroniser le statut de paiement via la nouvelle fonction
                    order_updated = update_order_payment_status(session)
                    if order_updated:
                        current_app.logger.info(f"Commande synchronisée et utilisateur {user_id} mis à jour avec succès")
                    else:
                        # Fallback vers l'ancienne méthode si nécessaire
                        success = create_order_and_update_user(session, user_id, plan_name, product_id)
                        if success:
                            current_app.logger.info(f"Commande créée et utilisateur {user_id} mis à jour avec succès (fallback)")
                        else:
                            current_app.logger.error(f"Échec de la création/synchronisation de commande pour l'utilisateur {user_id}")
                else:
                    current_app.logger.warning(
                        f"Métadonnées manquantes - User ID: {user_id}, Plan: {plan_name}"
                    )
                
                return make_response(jsonify({"status": "success"}), 200)
                
        except Exception as e:
            current_app.logger.error(f"Erreur webhook Stripe: {str(e)}")
            return make_response(jsonify({"error": str(e)}), 400)
        
        return make_response(jsonify({"status": "success"}), 200)


def create_order_and_update_user(session, user_id, plan_name, product_id):
    """Crée une commande et met à jour l'utilisateur après un paiement réussi"""
    try:
        # Vérifier si une commande existe déjà pour cette session Stripe
        existing_order = Order.query.filter_by(stripe_session_id=session.get('id')).first()
        if existing_order:
            current_app.logger.info(f"Commande déjà existante pour la session {session.get('id')}, mise à jour seulement")
            # Ne mettre à jour que le statut si nécessaire
            if existing_order.status != 'paid':
                existing_order.status = 'paid'
                existing_order.payment_status = 'completed'
                existing_order.paid_at = datetime.utcnow()
                db.session.commit()
            return True
        
        # Récupérer l'utilisateur
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Utilisateur avec l'ID {user_id} non trouvé")
            return False
        
        # Récupérer les informations du plan depuis la base de données
        from models.subscription_pack_model import SubscriptionPack
        subscription_pack = SubscriptionPack.query.filter_by(pack_id=plan_name, is_active=True).first()
        
        if not subscription_pack:
            current_app.logger.error(f"Plan {plan_name} non trouvé dans la base de données")
            return False
        
        # Récupérer les informations de paiement depuis Stripe
        payment_intent_id = session.get('payment_intent')
        amount_total = session.get('amount_total', 0) / 100  # Convertir de centimes en unité principale
        currency = session.get('currency', 'usd').upper()
        
        # Vérifier si l'utilisateur a déjà un plan actif pour éviter les doublons de crédits
        user_has_active_plan = user.subscription_plan is not None and user.subscription_plan != ''
        
        # Créer la commande
        order = Order(
            user_id=int(user_id),
            subscription_plan=plan_name,
            amount=amount_total,
            currency=currency,
            status='paid',
            payment_status='completed',
            payment_method='card',
            stripe_session_id=session.get('id'),
            stripe_payment_intent_id=payment_intent_id,
            customer_email=session.get('customer_email') or user.email,
            customer_name=f"{user.prenom or ''} {user.nom or ''}".strip() or user.username,
            customer_phone=user.tel,
            paid_at=datetime.utcnow()
        )
        
        # Sauvegarder l'ancien plan pour le log
        old_plan = user.subscription_plan
        old_sold = user.sold
        old_total_sold = user.total_sold
        
        # Mettre à jour le plan d'abonnement
        user.subscription_plan = plan_name
        user.payment_status = "paid"
        user.payment_id = session.get('id')
        
        # Ajouter les nouveaux usages seulement si c'est un nouveau paiement
        # (ne pas ajouter si l'utilisateur a déjà ce plan actif)
        if not user_has_active_plan or old_plan != plan_name:
            new_usages = float(subscription_pack.usages)
            user.sold += new_usages
            user.total_sold += new_usages
            current_app.logger.info(
                f"Nouveaux crédits ajoutés: {new_usages} pour le plan {plan_name}"
            )
        else:
            current_app.logger.info(
                f"Utilisateur a déjà le plan {plan_name}, aucun crédit supplémentaire ajouté"
            )
        
        # Sauvegarder la commande et l'utilisateur
        db.session.add(order)
        db.session.commit()
        
        current_app.logger.info(
            f"Commande {order.order_number} créée et plan mis à jour pour l'utilisateur {user_id}: "
            f"{old_plan} -> {plan_name}, "
            f"Sold: {old_sold} -> {user.sold}, "
            f"Total: {old_total_sold} -> {user.total_sold}"
        )
        
        # Envoyer l'email de bienvenue immédiatement après la création de la commande
        try:
            from services.email.email_service import email_service
            
            user_email_data = {
                'username': user.username,
                'email': user.email,
                'nom': user.nom,
                'prenom': user.prenom,
                'subscription_plan': user.subscription_plan,
                'sold': user.sold
            }
            
            email_sent = email_service.send_welcome_email(user_email_data, order.order_number)
            if email_sent:
                current_app.logger.info(f"Email de bienvenue envoyé avec succès pour la commande {order.order_number}")
            else:
                current_app.logger.warning(f"Échec de l'envoi de l'email de bienvenue pour la commande {order.order_number}")
                
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
        
        return True
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la création de commande et mise à jour: {str(e)}")
        db.session.rollback()
        return False


def update_order_payment_status(checkout_session):
    """Met à jour le statut de paiement dans la table Order de manière sécurisée et synchronisée avec Stripe"""
    try:
        # Récupérer les métadonnées de la session
        metadata = checkout_session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_name = metadata.get('plan_name')
        
        if not user_id or not plan_name:
            current_app.logger.error("Métadonnées manquantes pour la mise à jour de la commande")
            return False
            
        # Rechercher la commande existante par session_id
        order = Order.query.filter_by(stripe_session_id=checkout_session.get('id')).first()
        
        if not order:
            # Si aucune commande n'existe, en créer une nouvelle
            current_app.logger.info(f"Création d'une nouvelle commande pour la session {checkout_session.get('id')}")
            return create_order_and_update_user(checkout_session, user_id, plan_name, None)
        
        # Utiliser la nouvelle méthode du modèle pour une synchronisation sécurisée
        success, message = order.sync_with_stripe_session(checkout_session)
        
        if success:
            current_app.logger.info(message)
            return True
        else:
            current_app.logger.warning(message)
            return False
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la synchronisation du statut de paiement: {str(e)}")
        db.session.rollback()
        return False


def update_user_subscription(user_id, plan_name):
    """Met à jour le plan d'abonnement et le solde de l'utilisateur après un paiement réussi (fonction de compatibilité)"""
    try:
        # Récupérer l'utilisateur
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Utilisateur avec l'ID {user_id} non trouvé")
            return False
        
        # Récupérer les informations du plan depuis la base de données
        from models.subscription_pack_model import SubscriptionPack
        subscription_pack = SubscriptionPack.query.filter_by(pack_id=plan_name, is_active=True).first()
        
        if subscription_pack:
            # Sauvegarder l'ancien plan pour le log
            old_plan = user.subscription_plan
            old_sold = user.sold
            old_total_sold = user.total_sold
            
            # Mettre à jour le plan d'abonnement
            user.subscription_plan = plan_name
            user.payment_status = "paid"
            
            # Ajouter les nouveaux usages au solde existant
            new_usages = float(subscription_pack.usages)
            user.sold += new_usages
            user.total_sold += new_usages
            
            # Sauvegarder les changements
            db.session.commit()
            
            current_app.logger.info(
                f"Plan mis à jour pour l'utilisateur {user_id}: "
                f"{old_plan} -> {plan_name}, "
                f"Sold: {old_sold} -> {user.sold} (+{new_usages}), "
                f"Total: {old_total_sold} -> {user.total_sold}"
            )
            return True
        else:
            current_app.logger.error(f"Plan {plan_name} non trouvé dans la base de données")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour de l'abonnement: {str(e)}")
        db.session.rollback()
        return False