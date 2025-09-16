from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import get_jwt_identity, jwt_required
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModeratorPermissions:
    """
    Service de validation des permissions pour les modérateurs.
    Implémente une validation robuste des règles d'accès.
    """
    
    @staticmethod
    def can_manage_user(moderator_info, target_user):
        """
        Vérifie si un modérateur peut gérer un utilisateur spécifique.
        
        Args:
            moderator_info (dict): Informations du modérateur connecté
            target_user (dict): Informations de l'utilisateur cible
            
        Returns:
            tuple: (bool, str) - (autorisation, message d'erreur si applicable)
        """
        try:
            # Vérifier que l'utilisateur connecté est bien un modérateur
            if moderator_info.get('role') != 'moderator':
                return False, "Accès refusé : rôle modérateur requis"
            
            # Les modérateurs ne peuvent pas gérer les administrateurs
            if target_user.get('role') == 'admin':
                return False, "Accès refusé : impossible de gérer un administrateur"
            
            # Les modérateurs ne peuvent gérer que leur propre compte modérateur
            if target_user.get('role') == 'moderator':
                if target_user.get('username') != moderator_info.get('username'):
                    return False, "Accès refusé : impossible de gérer un autre modérateur"
            
            # Pour les clients, vérifier qu'ils ont été créés par ce modérateur
            if target_user.get('role') == 'client':
                if (target_user.get('created_by') != moderator_info.get('username') and 
                    target_user.get('username') != moderator_info.get('username')):
                    return False, "Accès refusé : vous ne pouvez gérer que les utilisateurs que vous avez créés"
            
            return True, "Autorisation accordée"
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des permissions : {str(e)}")
            return False, "Erreur interne lors de la vérification des permissions"
    
    @staticmethod
    def can_delete_user(moderator_info, target_user):
        """
        Vérifie si un modérateur peut supprimer un utilisateur.
        
        Args:
            moderator_info (dict): Informations du modérateur connecté
            target_user (dict): Informations de l'utilisateur à supprimer
            
        Returns:
            tuple: (bool, str) - (autorisation, message d'erreur si applicable)
        """
        try:
            # Vérifier que l'utilisateur connecté est bien un modérateur
            if moderator_info.get('role') != 'moderator':
                return False, "Accès refusé : rôle modérateur requis"
            
            # Les modérateurs ne peuvent supprimer ni les admins ni les autres modérateurs
            if target_user.get('role') in ['admin', 'moderator']:
                return False, "Accès refusé : impossible de supprimer un administrateur ou un modérateur"
            
            # Pour les clients, vérifier qu'ils ont été créés par ce modérateur
            if target_user.get('role') == 'client':
                if target_user.get('created_by') != moderator_info.get('username'):
                    return False, "Accès refusé : vous ne pouvez supprimer que les utilisateurs que vous avez créés"
            
            return True, "Suppression autorisée"
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des permissions de suppression : {str(e)}")
            return False, "Erreur interne lors de la vérification des permissions"
    
    @staticmethod
    def can_modify_password(moderator_info, target_user):
        """
        Vérifie si un modérateur peut modifier le mot de passe d'un utilisateur.
        
        Args:
            moderator_info (dict): Informations du modérateur connecté
            target_user (dict): Informations de l'utilisateur cible
            
        Returns:
            tuple: (bool, str) - (autorisation, message d'erreur si applicable)
        """
        try:
            # Vérifier que l'utilisateur connecté est bien un modérateur
            if moderator_info.get('role') != 'moderator':
                return False, "Accès refusé : rôle modérateur requis"
            
            # Les modérateurs ne peuvent pas modifier les mots de passe des administrateurs
            if target_user.get('role') == 'admin':
                return False, "Accès refusé : impossible de modifier le mot de passe d'un administrateur"
            
            # Les modérateurs peuvent modifier leur propre mot de passe
            if (target_user.get('role') == 'moderator' and 
                target_user.get('username') == moderator_info.get('username')):
                return True, "Modification de mot de passe autorisée"
            
            # Pour les autres modérateurs, accès refusé
            if (target_user.get('role') == 'moderator' and 
                target_user.get('username') != moderator_info.get('username')):
                return False, "Accès refusé : impossible de modifier le mot de passe d'un autre modérateur"
            
            # Pour les clients, vérifier qu'ils ont été créés par ce modérateur
            if target_user.get('role') == 'client':
                if target_user.get('created_by') != moderator_info.get('username'):
                    return False, "Accès refusé : vous ne pouvez modifier que les mots de passe des utilisateurs que vous avez créés"
            
            return True, "Modification de mot de passe autorisée"
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des permissions de modification de mot de passe : {str(e)}")
            return False, "Erreur interne lors de la vérification des permissions"
    
    @staticmethod
    def get_accessible_users(moderator_info, all_users):
        """
        Filtre la liste des utilisateurs accessibles pour un modérateur.
        
        Args:
            moderator_info (dict): Informations du modérateur connecté
            all_users (list): Liste de tous les utilisateurs
            
        Returns:
            list: Liste des utilisateurs accessibles au modérateur
        """
        try:
            if moderator_info.get('role') != 'moderator':
                return []
            
            accessible_users = []
            
            for user in all_users:
                # Inclure son propre compte
                if user.get('username') == moderator_info.get('username'):
                    accessible_users.append(user)
                    continue
                
                # Inclure les clients créés par ce modérateur
                if (user.get('role') == 'client' and 
                    user.get('created_by') == moderator_info.get('username')):
                    accessible_users.append(user)
                    continue
            
            return accessible_users
            
        except Exception as e:
            logger.error(f"Erreur lors du filtrage des utilisateurs accessibles : {str(e)}")
            return []

def require_moderator_permission(permission_type):
    """
    Décorateur pour vérifier les permissions des modérateurs.
    
    Args:
        permission_type (str): Type de permission à vérifier ('manage', 'delete', 'modify_password')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Récupérer l'identité de l'utilisateur connecté
                current_user_id = get_jwt_identity()
                
                # Récupérer les informations de l'utilisateur connecté depuis la base de données
                # (Cette partie doit être adaptée selon votre modèle de données)
                from app import db
                from models.user import User
                
                current_user = User.query.filter_by(username=current_user_id).first()
                if not current_user:
                    return jsonify({'error': 'Utilisateur non trouvé'}), 404
                
                moderator_info = {
                    'username': current_user.username,
                    'role': current_user.role
                }
                
                # Stocker les informations du modérateur dans g pour utilisation dans la route
                g.moderator_info = moderator_info
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Erreur dans le décorateur de permissions : {str(e)}")
                return jsonify({'error': 'Erreur interne du serveur'}), 500
        
        return decorated_function
    return decorator

def validate_moderator_access(moderator_info, target_username, permission_type):
    """
    Fonction utilitaire pour valider l'accès d'un modérateur.
    
    Args:
        moderator_info (dict): Informations du modérateur
        target_username (str): Nom d'utilisateur cible
        permission_type (str): Type de permission ('manage', 'delete', 'modify_password')
        
    Returns:
        tuple: (bool, str, dict) - (autorisation, message, informations utilisateur cible)
    """
    try:
        # Récupérer les informations de l'utilisateur cible
        from app import db
        from models.user import User
        
        target_user = User.query.filter_by(username=target_username).first()
        if not target_user:
            return False, "Utilisateur cible non trouvé", None
        
        target_user_info = {
            'username': target_user.username,
            'role': target_user.role,
            'created_by': getattr(target_user, 'created_by', None)
        }
        
        # Vérifier les permissions selon le type
        if permission_type == 'manage':
            can_access, message = ModeratorPermissions.can_manage_user(moderator_info, target_user_info)
        elif permission_type == 'delete':
            can_access, message = ModeratorPermissions.can_delete_user(moderator_info, target_user_info)
        elif permission_type == 'modify_password':
            can_access, message = ModeratorPermissions.can_modify_password(moderator_info, target_user_info)
        else:
            return False, "Type de permission non reconnu", None
        
        return can_access, message, target_user_info
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation de l'accès modérateur : {str(e)}")
        return False, "Erreur interne lors de la validation", None