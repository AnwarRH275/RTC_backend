from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.subscription_pack import SubscriptionPack
from app import db
from services.moderator_permissions import ModeratorPermissions, validate_moderator_access
from werkzeug.security import generate_password_hash
import logging

class UserManagementService:
    """Service pour la gestion des utilisateurs avec validation des permissions modérateur"""
    
    @staticmethod
    @jwt_required()
    def create_user(user_data):
        """Créer un nouvel utilisateur avec validation des permissions"""
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'success': False, 'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Vérifier si l'utilisateur existe déjà
            existing_user = User.query.filter(
                (User.username == user_data.get('username')) | 
                (User.email == user_data.get('email'))
            ).first()
            
            if existing_user:
                return {'success': False, 'message': 'Un utilisateur avec ce nom d\'utilisateur ou email existe déjà'}, 400
            
            # Si l'utilisateur connecté est un modérateur, vérifier les restrictions
            if current_user.role == 'moderator':
                # Les modérateurs ne peuvent créer que des clients
                if user_data.get('role') not in ['client', None]:
                    return {'success': False, 'message': 'Les modérateurs ne peuvent créer que des comptes clients'}, 403
                
                # Forcer le rôle à 'client' pour les créations par modérateur
                user_data['role'] = 'client'
            
            # Récupérer le plan d'abonnement
            subscription_pack = None
            if user_data.get('subscription_plan_id'):
                subscription_pack = SubscriptionPack.query.get(user_data.get('subscription_plan_id'))
                if not subscription_pack:
                    return {'success': False, 'message': 'Plan d\'abonnement non trouvé'}, 404
            
            # Créer le nouvel utilisateur
            new_user = User(
                username=user_data.get('username'),
                email=user_data.get('email'),
                password=generate_password_hash(user_data.get('password')),
                name=user_data.get('name', ''),
                phone=user_data.get('phone', ''),
                role=user_data.get('role', 'client'),
                subscription_pack_id=user_data.get('subscription_plan_id'),
                created_by=current_user.username if current_user.role == 'moderator' else None
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return {'success': True, 'message': 'Utilisateur créé avec succès', 'user_id': new_user.id}, 201
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            return {'success': False, 'message': f'Erreur lors de la création: {str(e)}'}, 500
    
    @staticmethod
    @jwt_required()
    def update_user(username, user_data):
        """Mettre à jour un utilisateur avec validation des permissions"""
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'success': False, 'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                # Vérifier si le modérateur peut modifier cet utilisateur
                can_manage, message, target_user_info = validate_moderator_access(
                    {'username': current_user.username, 'role': current_user.role},
                    username,
                    'manage'
                )
                
                if not can_manage:
                    return {'success': False, 'message': message}, 403
                
                # Vérifier si le modérateur essaie de changer le mot de passe d'un admin
                if target_user_info and target_user_info.get('role') == 'admin' and 'password' in user_data:
                    return {'success': False, 'message': 'Les modérateurs ne peuvent pas modifier les mots de passe des administrateurs'}, 403
                
                # Les modérateurs ne peuvent pas changer les rôles
                if 'role' in user_data and user_data['role'] != target_user_info.get('role'):
                    return {'success': False, 'message': 'Les modérateurs ne peuvent pas modifier les rôles des utilisateurs'}, 403
            
            # Récupérer l'utilisateur à modifier
            user = User.query.filter_by(username=username).first()
            if not user:
                return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
            
            # Mettre à jour les champs autorisés
            if 'email' in user_data:
                # Vérifier que l'email n'est pas déjà utilisé
                existing_email = User.query.filter(
                    User.email == user_data['email'],
                    User.id != user.id
                ).first()
                if existing_email:
                    return {'success': False, 'message': 'Cet email est déjà utilisé'}, 400
                user.email = user_data['email']
            
            if 'name' in user_data:
                user.name = user_data['name']
            
            if 'phone' in user_data:
                user.phone = user_data['phone']
            
            if 'password' in user_data and user_data['password']:
                user.password = generate_password_hash(user_data['password'])
            
            if 'role' in user_data and current_user.role == 'admin':
                user.role = user_data['role']
            
            if 'subscription_plan_id' in user_data:
                if user_data['subscription_plan_id']:
                    subscription_pack = SubscriptionPack.query.get(user_data['subscription_plan_id'])
                    if not subscription_pack:
                        return {'success': False, 'message': 'Plan d\'abonnement non trouvé'}, 404
                user.subscription_pack_id = user_data['subscription_plan_id']
            
            db.session.commit()
            
            return {'success': True, 'message': 'Utilisateur mis à jour avec succès'}, 200
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
            return {'success': False, 'message': f'Erreur lors de la mise à jour: {str(e)}'}, 500
    
    @staticmethod
    @jwt_required()
    def delete_user(username):
        """Supprimer un utilisateur avec validation des permissions"""
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'success': False, 'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                can_delete, message, target_user_info = validate_moderator_access(
                    {'username': current_user.username, 'role': current_user.role},
                    username,
                    'delete'
                )
                
                if not can_delete:
                    return {'success': False, 'message': message}, 403
            
            # Récupérer et supprimer l'utilisateur
            user = User.query.filter_by(username=username).first()
            if not user:
                return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
            
            db.session.delete(user)
            db.session.commit()
            
            return {'success': True, 'message': 'Utilisateur supprimé avec succès'}, 200
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
            return {'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'}, 500
    
    @staticmethod
    @jwt_required()
    def get_users():
        """Récupérer la liste des utilisateurs avec filtrage pour les modérateurs"""
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'success': False, 'message': 'Utilisateur connecté non trouvé'}, 404
            
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
                
                return {'success': True, 'users': accessible_users}, 200
            else:
                # Pour les administrateurs, retourner tous les utilisateurs
                users = User.query.all()
                users_data = [user.to_dict() for user in users]
                return {'success': True, 'users': users_data}, 200
                
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
            return {'success': False, 'message': f'Erreur lors de la récupération: {str(e)}'}, 500
    
    @staticmethod
    @jwt_required()
    def get_user(username):
        """Récupérer un utilisateur spécifique avec validation des permissions"""
        try:
            # Récupérer l'utilisateur connecté
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(username=current_user_id).first()
            
            if not current_user:
                return {'success': False, 'message': 'Utilisateur connecté non trouvé'}, 404
            
            # Si l'utilisateur connecté est un modérateur, vérifier les permissions
            if current_user.role == 'moderator':
                can_manage, message, target_user_info = validate_moderator_access(
                    {'username': current_user.username, 'role': current_user.role},
                    username,
                    'manage'
                )
                
                if not can_manage:
                    return {'success': False, 'message': message}, 403
                
                return {'success': True, 'user': target_user_info}, 200
            else:
                # Pour les administrateurs, récupérer n'importe quel utilisateur
                user = User.query.filter_by(username=username).first()
                if not user:
                    return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
                
                return {'success': True, 'user': user.to_dict()}, 200
                
        except Exception as e:
            logging.error(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
            return {'success': False, 'message': f'Erreur lors de la récupération: {str(e)}'}, 500