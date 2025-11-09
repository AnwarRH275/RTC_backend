from flask import request, jsonify, make_response, g, current_app
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models.model import User
from werkzeug.security import generate_password_hash, check_password_hash
from models.exts import db
import random
import string
from services.email.email_service import EmailService, email_service
from services.moderator_permissions import ModeratorPermissions, validate_moderator_access
import logging
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


auth_ns = Namespace('auth', description='namespace for authentification')


# model (serializer)
signup_model = auth_ns.model(
    "SignUp",
    {
        "username": fields.String(),
        "email": fields.String(),
        "password": fields.String(),
        "tel": fields.String(),
        "nom": fields.String(),
        "prenom": fields.String(),
        "sexe": fields.String(),
        "date_naissance": fields.String(),
        "plan": fields.String(),
        "role": fields.String(),
        "sold": fields.Float(default=0.0),
        "total_sold": fields.Float(default=0.0)

    }
)

# model (serializer)
login_model = auth_ns.model(
    "Login",
    {
        "username": fields.String(),
        "password": fields.String(),
    }
)

# model (serializer) for forgot password
forgot_password_model = auth_ns.model(
    "ForgotPassword",
    {
        "email": fields.String(required=True, description="Email de l'utilisateur")
    }
)

# model (serializer) for reset password
reset_password_model = auth_ns.model(
    "ResetPassword",
    {
        "token": fields.String(required=True, description="Token de réinitialisation"),
        "new_password": fields.String(required=True, description="Nouveau mot de passe")
    }
)


@auth_ns.route('/signup')
class SignUp(Resource):

    @auth_ns.expect(signup_model)
    def put(self):
        data = request.get_json()
        username_to_update = User.query.filter_by(
            username=data.get('username')).first()
        
        if not username_to_update:
            return make_response(jsonify({"message": "User not found"}), 404)

        # Update all fields
        username_to_update.email = data.get('email', username_to_update.email)
        username_to_update.nom = data.get('nom', username_to_update.nom)
        username_to_update.prenom = data.get('prenom', username_to_update.prenom)
        username_to_update.tel = data.get('tel', username_to_update.tel)
        username_to_update.sexe = data.get('sexe', username_to_update.sexe)
        username_to_update.date_naissance = data.get('date_naissance', username_to_update.date_naissance)
        username_to_update.subscription_plan = data.get('plan', username_to_update.subscription_plan)
        username_to_update.role = data.get('role', username_to_update.role)
        username_to_update.sold = data.get('sold', username_to_update.sold)
        username_to_update.total_sold = data.get('total_sold', username_to_update.total_sold)
        
        # Update password only if provided
        if data.get('password'):
            username_to_update.password = generate_password_hash(data.get('password'))
        
        db.session.commit()
        
        return make_response(jsonify({"message": "User updated successfully", "status": "success"}), 200)

    @auth_ns.expect(signup_model)
    @jwt_required(optional=True)
    def post(self):
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['username', 'email', 'password', 'nom', 'prenom']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Champs manquants lors de l'inscription: {missing_fields}")
            return make_response(jsonify({
                "message": f"Champs requis manquants: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }), 422)
        
        username_find = User.query.filter_by(
            username=data.get('username')).first()
        # email_find = User.query.filter_by(email=data.get('email')).first()

        # print(email_find)
        if username_find is not None:
            return make_response(jsonify({"message": "User exist"}), 409)
        
        # Récupérer dynamiquement les usages du plan depuis la base de données
        from models.subscription_pack_model import SubscriptionPack
        
        plan_name = data.get('plan')
        subscription_pack = SubscriptionPack.query.filter_by(pack_id=plan_name, is_active=True).first()
        
        if subscription_pack:
            sold = float(subscription_pack.usages)
        else:
            # Valeur par défaut si le plan n'est pas trouvé
            sold = 0.0
        # Récupérer l'utilisateur connecté
        try:
            current_user = get_jwt_identity()
            logger.info(f"Utilisateur connecté identifié: {current_user}")
        except Exception as e:
            logger.warning(f"Impossible de récupérer l'identité JWT: {str(e)}")
            current_user = "public"
        # Créer un nouvel utilisateur
        new_user = User(
            username=data.get('username'),
            email=data.get('email'),
            password=generate_password_hash(data.get('password')),
            nom=data.get('nom'),
            prenom=data.get('prenom'),
            tel=data.get('tel'),
            sexe=data.get('sexe'),
            date_naissance=data.get('date_naissance'),
            subscription_plan=data.get('plan'),
            payment_status="paid",  # Considéré comme payé après redirection de Stripe
            role=data.get('role', 'client'),  # Assigner le rôle ou 'client' par défaut
            sold=sold,
            total_sold=sold,
            created_by=current_user
        )
        
        logger.info(f"Nouvel utilisateur créé: {new_user.username}, créé par: {current_user}")
        new_user.save()
        
        # L'email de bienvenue sera envoyé lors du paiement de la commande
        # pour inclure le numéro de commande (voir order_public.py)
        
        # Générer les tokens JWT après la création du compte
        access_token = create_access_token(identity=new_user.username)
        refresh_token = create_refresh_token(identity=new_user.username)
        
        return make_response(jsonify({
            "message": "User created successfully", 
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_info": new_user.to_dict()
        }), 201)


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        data = request.get_json()
        username_or_email = data.get('username')
        password = data.get('password')
        
        # Recherche par nom d'utilisateur ou email
        user = User.query.filter_by(username=username_or_email).first()
        
        # Si l'utilisateur n'est pas trouvé par nom d'utilisateur, essayer par email
        if user is None:
            user = User.query.filter_by(email=username_or_email).first()
            print(user)
            
        if user is None:
            return {"message": "Utilisateur non trouvé. Vérifiez votre nom d'utilisateur ou email."}, 404
            
        if check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(
                identity=user.username)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_info': user.to_dict()
            }
        else:
            return {"message": "Mot de passe invalide"}, 401


@auth_ns.route('/simulate-login')
class SimulateLogin(Resource):
    def post(self):
        """Émet un token JWT pour un utilisateur simulé (agentuser) si la simulation est activée.
        Protégé par un secret optionnel via SIMULATION_SECRET.
        """
        try:
            simulate_enabled = current_app.config.get('SIMULATE_AGENTUSER', False)
            if not simulate_enabled:
                return {"message": "Mode simulation désactivé côté serveur"}, 403

            data = request.get_json() or {}
            provided_secret = data.get('secret')
            required_secret = current_app.config.get('SIMULATION_SECRET', '')
            if required_secret and provided_secret != required_secret:
                return {"message": "Secret de simulation invalide"}, 403

            username = data.get('username') or current_app.config.get('SIMULATION_USERNAME', 'agentuser')

            # Rechercher ou créer l'utilisateur simulé
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(
                    username=username,
                    email=f"{username}@example.local",
                    password=generate_password_hash('password'),
                    nom='Agent',
                    prenom='User',
                    tel='',
                    sexe='',
                    date_naissance='',
                    subscription_plan='standard',
                    payment_status='paid',
                    role='client',
                    sold=0.0,
                    total_sold=0.0,
                    created_by='simulation'
                )
                db.session.add(user)
                db.session.commit()

            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(identity=user.username)
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_info': user.to_dict()
            }, 200
        except Exception as e:
            return {"message": f"Erreur lors de la simulation de connexion: {str(e)}"}, 500


@auth_ns.route('/counter')
class counter(Resource):
    def get(self):
        total_count = User.query.count()
        return jsonify({'total_count': total_count})


@auth_ns.route('/delete/<username>')
class DeleteUser(Resource):
    @jwt_required()
    def delete(self, username):
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                moderator_info = {
                    'username': current_user.username,
                    'role': current_user.role
                }
                
                can_delete, message, target_user_info = validate_moderator_access(
                    moderator_info, username, 'delete'
                )
                
                if not can_delete:
                    return {'message': message}, 403
            
            # Procéder à la suppression
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                return {'message': 'Utilisateur supprimé avec succès'}, 200
            else:
                return {'message': 'Utilisateur non trouvé'}, 404
                
        except Exception as e:
            db.session.rollback()
            return {'message': f'Erreur lors de la suppression: {str(e)}'}, 500

@auth_ns.route('/user-info')
class UserInfo(Resource):
    @jwt_required()
    def get(self):
        """Récupérer les informations de l'utilisateur connecté"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'message': 'Utilisateur non trouvé'}, 404
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nom': user.nom,
                'prenom': user.prenom,
                'subscription_plan': user.subscription_plan,
                'sold': user.sold,
                'total_sold': user.total_sold,
                'payment_status': user.payment_status,
                'role': user.role
            }, 200
            
        except Exception as e:
            return {'message': f'Erreur lors de la récupération des informations: {str(e)}'}, 500



# model (serializer) for user data
user_model = auth_ns.model(
    "User",
    {
        "id": fields.Integer(),
        "username": fields.String(),
        "email": fields.String(),
        "tel": fields.String(),
        "nom": fields.String(),
        "prenom": fields.String(),
        "sexe": fields.String(),
        "date_naissance": fields.String(),
        "subscription_plan": fields.String(),
        "payment_status": fields.String(),
        "role": fields.String(),
         "sold": fields.Float(default=0.0),
        "total_sold": fields.Float(default=0.0),
        "created_by": fields.String()
    }
)

# model (serializer) for updating sold
update_sold_model = auth_ns.model(
    "UpdateSold",
    {
        "username": fields.String(required=True),
        "new_sold_value": fields.Float(required=True)
    }
)

@auth_ns.route('/users')
class UserListResource(Resource):
    @jwt_required()
    @auth_ns.marshal_list_with(user_model)
    def get(self):
        '''Récupérer tous les utilisateurs'''
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, filtrer les utilisateurs
            if current_user.role == 'moderator':
                moderator_info = {
                    'username': current_user.username,
                    'role': current_user.role
                }
                
                all_users = User.query.all()
                accessible_users = ModeratorPermissions.get_accessible_users(
                    moderator_info, [user.to_dict() for user in all_users]
                )
                
                # Récupérer les objets User correspondants
                accessible_usernames = [user['username'] for user in accessible_users]
                users = User.query.filter(User.username.in_(accessible_usernames)).all()
                
                return users
            else:
                # Pour les administrateurs, retourner tous les utilisateurs
                users = User.query.all()
                return users
                
        except Exception as e:
            return {'message': f'Erreur lors de la récupération des utilisateurs: {str(e)}'}, 500

@auth_ns.route('/refresh')
class RefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)

        return make_response(jsonify({"access_token": new_access_token}), 200)

# model (serializer) for updating total sold
update_total_sold_model = auth_ns.model(
    "UpdateTotalSold",
    {
        "username": fields.String(required=True),
        "new_total_sold_value": fields.Float(required=True)
    }
)

@auth_ns.route('/update-sold')
class UpdateSoldResource(Resource):
    @jwt_required()
    @auth_ns.expect(update_sold_model)
    def put(self):
        try:
            data = request.get_json()
            username = data.get('username')
            new_sold_value = data.get('new_sold_value')
            
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                moderator_info = {
                    'username': current_user.username,
                    'role': current_user.role
                }
                
                can_manage, message, target_user_info = validate_moderator_access(
                    moderator_info, username, 'manage'
                )
                
                if not can_manage:
                    return {'message': message}, 403
            
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return {"message": "Utilisateur non trouvé"}, 404
            
            user.update_sold(new_sold_value)
            return {"message": "Solde utilisateur mis à jour avec succès", "sold": user.sold}, 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour du solde : {str(e)}")
            return {"message": f"Erreur lors de la mise à jour du solde : {str(e)}"}, 500

@auth_ns.route('/update-total-sold')
class UpdateTotalSoldResource(Resource):
    @jwt_required()
    @auth_ns.expect(update_total_sold_model)
    def put(self):
        try:
            data = request.get_json()
            username = data.get('username')
            new_total_sold_value = data.get('new_total_sold_value')
            
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                moderator_info = {
                    'username': current_user.username,
                    'role': current_user.role
                }
                
                can_manage, message, target_user_info = validate_moderator_access(
                    moderator_info, username, 'manage'
                )
                
                if not can_manage:
                    return {'message': message}, 403
            
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return {"message": "Utilisateur non trouvé"}, 404
            
            user.update_total_sold(new_total_sold_value)
            return {"message": "Solde total utilisateur mis à jour avec succès", "total_sold": user.total_sold}, 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la mise à jour du solde total : {str(e)}")
            return {"message": f"Erreur lors de la mise à jour du solde total : {str(e)}"}, 500

@auth_ns.route('/MyPlan')
class MyPlanResource(Resource):
    @jwt_required()
    def get(self):
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        if user:
            return jsonify({'subscription_plan': user.subscription_plan})
        else:
            return jsonify({'message': 'User not found'}), 404

@auth_ns.route('/me')
class CurrentUserResource(Resource):
    @jwt_required()
    def get(self):
        '''Récupérer les informations de l'utilisateur connecté'''
        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_user_identity).first()
        if user:
            return jsonify(user.to_dict())
        else:
            return jsonify({'message': 'User not found'}), 404


@auth_ns.route('/forgot-password')
class ForgotPassword(Resource):
    @auth_ns.expect(forgot_password_model)
    def post(self):
        """Demander une réinitialisation de mot de passe"""
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                return {'message': 'Email requis'}, 400
            
            # Vérifier si l'utilisateur existe
            user = User.query.filter_by(email=email).first()
            if not user:
                # Pour des raisons de sécurité, on retourne toujours le même message
                return {'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'}, 200
            
            # Générer le token de réinitialisation
            reset_token = user.generate_reset_token()
            
            # Envoyer l'email de réinitialisation
            email_service_instance = EmailService()
            email_sent = email_service_instance.send_password_reset_email(user.to_dict(), reset_token)
            
            return {'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'}, 200
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {str(e)}")
            return {'message': 'Erreur interne du serveur'}, 500


@auth_ns.route('/reset-password')
class ResetPassword(Resource):
    @auth_ns.expect(reset_password_model)
    def post(self):
        """Réinitialiser le mot de passe avec le token"""
        try:
            data = request.get_json()
            token = data.get('token')
            new_password = data.get('new_password')
            
            if not token or not new_password:
                return {'message': 'Token et nouveau mot de passe requis'}, 400
            
            if len(new_password) < 6:
                return {'message': 'Le mot de passe doit contenir au moins 6 caractères'}, 400
            
            # Vérifier le token
            user = User.verify_reset_token(token)
            if not user:
                return {'message': 'Token invalide ou expiré'}, 400
            
            # Mettre à jour le mot de passe
            user.password = generate_password_hash(new_password)
            user.clear_reset_token()
            
            return {'message': 'Mot de passe réinitialisé avec succès'}, 200
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")
            return {'message': 'Erreur interne du serveur'}, 500
