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

        username_to_update.update(
            nom=data.get('nom'),
            tel=data.get('tel'),
            email=data.get('email'),
            sexe=data.get('sexe'),
            date_naissance=data.get('date_naissance')
        )

        return data

    @auth_ns.expect(signup_model)
    def post(self):
        data = request.get_json()
        username_find = User.query.filter_by(
            username=data.get('username')).first()
        # email_find = User.query.filter_by(email=data.get('email')).first()

        # print(email_find)
        if username_find is not None:
            return jsonify({"message": "User exist"})
        
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
            payment_status="paid"  # Considéré comme payé après redirection de Stripe
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
            
        if user is None:
            return jsonify({"message": "Utilisateur non trouvé. Vérifiez votre nom d'utilisateur ou email."})
            
        if check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(
                identity=user.username)
            return jsonify({
                'acces_token': access_token,
                'refresh_token': refresh_token
            })
        else:
            return jsonify({"message": "password invalid"})


@auth_ns.route('/counter')
class counter(Resource):
    def get(self):
        total_count = User.query.count()
        return jsonify({'total_count': total_count})


@auth_ns.route('/delete/<string:username>', methods=['DELETE'])
class deleteUsers(Resource):
    def delete(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': f'User {username} deleted.'})
        else:
            return jsonify({'message': f'User {username} not found.'})



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
