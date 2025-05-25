import stripe
from flask import request, jsonify, make_response, current_app
import traceback
from flask_restx import Resource, Namespace, fields
from models.model import User
from models.exts import db

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
    }
)

# Modèle pour la vérification du paiement
payment_verify_model = stripe_ns.model(
    "PaymentVerify",
    {
        "session_id": fields.String(required=True, description="ID de la session de paiement Stripe"),
    }
)

# Plans disponibles avec leurs IDs de produits Stripe
PLANS = {
    "standard": {
        "name": "Pack Écrit Standard",
        "price": 1499,  # 14.99 CAD
        "usages": 5,
        "product_id": "prod_SMeQcS5gdyO7Nh",
    },
    "performance": {
        "name": "Pack Écrit Performance",
        "price": 2999,  # 29.99 CAD
        "usages": 15,
        "product_id": "prod_SMePWWnxhhQXZJ",
    },
    "pro": {
        "name": "Pack Écrit Pro",
        "price": 4999,  # 49.99 CAD
        "usages": 30,
        "product_id": "prod_SMeQ8tIJeu8sHA",
    },
}

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

        if not user_email:
            return make_response(jsonify({"error": "Email de l'utilisateur manquant"}), 400)

        # Optionnel: Ajouter une validation basique du format de l'email si nécessaire
        # Exemple simple (peut être amélioré avec une regex plus robuste):
        if '@' not in user_email or '.' not in user_email:
             return make_response(jsonify({"error": "Format d'email invalide"}), 400)

        try:
            # Récupérer ou créer un prix pour le produit
            prices = stripe.Price.list(product=product_id, limit=1)
            
            if prices.data:
                # Utiliser le prix existant
                price_id = prices.data[0].id
            else:
                # Créer un nouveau prix pour le produit
                price = stripe.Price.create(
                    product=product_id,
                    unit_amount=price_in_cents,
                    currency='cad',
                )
                price_id = price.id
            
            # Créer une session de paiement Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    'user_id': user_id,
                    'product_id': product_id,
                    'plan_name': plan_name
                }
            )
            
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
        """Vérifier le statut d'un paiement Stripe"""
        # Initialiser Stripe avec la bonne clé API
        init_stripe()
        
        data = request.get_json()
        session_id = data.get('session_id')
        
        try:
            # Récupérer la session de paiement
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # Vérifier si le paiement a été effectué
            if checkout_session.payment_status == 'paid':
                return make_response(jsonify({
                    "status": "success",
                    "message": "Paiement réussi"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "pending",
                    "message": "Paiement en attente"
                }), 200)
                
        except Exception as e:
            current_app.logger.error("Erreur lors de la création de la session de paiement Stripe:", exc_info=True)
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
                
                # Mettre à jour le statut de l'utilisateur dans la base de données
                # Ici, vous pouvez ajouter votre logique pour mettre à jour l'utilisateur
                
                return make_response(jsonify({"status": "success"}), 200)
                
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 400)
        
        return make_response(jsonify({"status": "success"}), 200)