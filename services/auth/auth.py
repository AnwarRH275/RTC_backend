from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models.model import User
from werkzeug.security import generate_password_hash, check_password_hash
from models.exts import db
import random
import string


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
    def post(self):
        data = request.get_json()
        username_find = User.query.filter_by(
            username=data.get('username')).first()
        # email_find = User.query.filter_by(email=data.get('email')).first()

        # print(email_find)
        if username_find is not None:
            return jsonify({"message": "User exist"})
        
        # Récupérer dynamiquement les usages du plan depuis la base de données
        from models.subscription_pack_model import SubscriptionPack
        
        plan_name = data.get('plan')
        subscription_pack = SubscriptionPack.query.filter_by(pack_id=plan_name, is_active=True).first()
        
        if subscription_pack:
            sold = float(subscription_pack.usages)
        else:
            # Valeur par défaut si le plan n'est pas trouvé
            sold = 0.0

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
            sold=sold,
            total_sold=sold
        )

        new_user.save()
        return make_response(jsonify({"message": "User created successfully", "status": "success"}), 201)


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
            return jsonify({"message": "Utilisateur non trouvé. Vérifiez votre nom d'utilisateur ou email."}), 404
            
        if check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(
                identity=user.username)
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_info': user.to_dict()
            })
        else:
            return jsonify({"message": "Mot de passe invalide"}), 401


@auth_ns.route('/counter')
class counter(Resource):
    def get(self):
        total_count = User.query.count()
        return jsonify({'total_count': total_count})


@auth_ns.route('/delete/<username>')
class DeleteUser(Resource):
    def delete(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return {'message': 'User deleted successfully'}, 200
        else:
            return {'message': 'User not found'}, 404

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
        "total_sold": fields.Float(default=0.0)
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
    @auth_ns.marshal_list_with(user_model)
    def get(self):
        '''Récupérer tous les utilisateurs'''
        users = User.query.all()
        return users

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
    @auth_ns.expect(update_sold_model)
    def put(self):
        data = request.get_json()
        username = data.get('username')
        new_sold_value = data.get('new_sold_value')

        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        try:
            user.update_sold(new_sold_value)
            return make_response(jsonify({"message": "Solde utilisateur mis à jour avec succès", "sold": user.sold}), 200)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du solde : {str(e)}")
            return make_response(jsonify({"message": f"Erreur lors de la mise à jour du solde : {str(e)}"}), 500)

@auth_ns.route('/update-total-sold')
class UpdateTotalSoldResource(Resource):
    @auth_ns.expect(update_total_sold_model)
    def put(self):
        data = request.get_json()
        username = data.get('username')
        new_total_sold_value = data.get('new_total_sold_value')

        user = User.query.filter_by(username=username).first()

        if not user:
            return make_response(jsonify({"message": "Utilisateur non trouvé"}), 404)

        try:
            user.update_total_sold(new_total_sold_value)
            return make_response(jsonify({"message": "Solde total utilisateur mis à jour avec succès", "total_sold": user.total_sold}), 200)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du solde total : {str(e)}")
            return make_response(jsonify({"message": f"Erreur lors de la mise à jour du solde total : {str(e)}"}), 500)

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
