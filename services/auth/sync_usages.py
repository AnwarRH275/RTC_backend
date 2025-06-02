from flask import jsonify, make_response
from flask_restx import Resource, Namespace
from models.model import User
from models.subscription_pack_model import SubscriptionPack
from models.exts import db

# Créer un namespace pour la synchronisation des usages
sync_ns = Namespace('sync', description='Synchronisation des usages utilisateurs')

@sync_ns.route('/sync-user-usages')
class SyncUserUsages(Resource):
    def post(self):
        """
        Synchronise les usages (sold/total_sold) de tous les utilisateurs 
        avec les valeurs actuelles de leurs plans d'abonnement
        """
        try:
            updated_users = []
            
            # Récupérer tous les utilisateurs
            users = User.query.all()
            
            for user in users:
                if user.subscription_plan:
                    # Trouver le pack correspondant au plan de l'utilisateur
                    pack = SubscriptionPack.query.filter_by(
                        pack_id=user.subscription_plan, 
                        isActive=True
                    ).first()
                    
                    if pack:
                        # Calculer le ratio d'usage actuel pour préserver le progrès
                        current_ratio = 0
                        if user.total_sold and user.total_sold > 0:
                            current_ratio = user.sold / user.total_sold
                        
                        # Sauvegarder les anciennes valeurs pour le log
                        old_sold = user.sold
                        old_total_sold = user.total_sold
                        
                        # Mettre à jour total_sold avec les nouveaux usages du pack
                        user.total_sold = float(pack.usages)
                        
                        # Mettre à jour sold en préservant le ratio d'usage
                        user.sold = user.total_sold * current_ratio
                        
                        # S'assurer que sold ne dépasse pas total_sold
                        if user.sold > user.total_sold:
                            user.sold = user.total_sold
                        
                        updated_users.append({
                            'username': user.username,
                            'plan': user.subscription_plan,
                            'old_sold': old_sold,
                            'new_sold': user.sold,
                            'old_total_sold': old_total_sold,
                            'new_total_sold': user.total_sold,
                            'pack_usages': pack.usages
                        })
            
            # Sauvegarder toutes les modifications
            db.session.commit()
            
            return make_response(jsonify({
                "message": f"Synchronisation terminée. {len(updated_users)} utilisateurs mis à jour.",
                "updated_users": updated_users,
                "status": "success"
            }), 200)
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la synchronisation des usages : {str(e)}")
            return make_response(jsonify({
                "message": f"Erreur lors de la synchronisation : {str(e)}",
                "status": "error"
            }), 500)

@sync_ns.route('/sync-user-usage/<string:username>')
class SyncSingleUserUsage(Resource):
    def post(self, username):
        """
        Synchronise les usages d'un utilisateur spécifique avec son plan d'abonnement
        """
        try:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return make_response(jsonify({
                    "message": "Utilisateur non trouvé",
                    "status": "error"
                }), 404)
            
            if not user.subscription_plan:
                return make_response(jsonify({
                    "message": "Aucun plan d'abonnement trouvé pour cet utilisateur",
                    "status": "error"
                }), 400)
            
            # Trouver le pack correspondant
            pack = SubscriptionPack.query.filter_by(
                pack_id=user.subscription_plan, 
                isActive=True
            ).first()
            
            if not pack:
                return make_response(jsonify({
                    "message": f"Pack d'abonnement '{user.subscription_plan}' non trouvé ou inactif",
                    "status": "error"
                }), 404)
            
            # Calculer le ratio d'usage actuel
            current_ratio = 0
            if user.total_sold and user.total_sold > 0:
                current_ratio = user.sold / user.total_sold
            
            # Sauvegarder les anciennes valeurs
            old_sold = user.sold
            old_total_sold = user.total_sold
            
            # Mettre à jour les valeurs
            user.total_sold = float(pack.usages)
            user.sold = user.total_sold * current_ratio
            
            # S'assurer que sold ne dépasse pas total_sold
            if user.sold > user.total_sold:
                user.sold = user.total_sold
            
            db.session.commit()
            
            return make_response(jsonify({
                "message": "Synchronisation réussie",
                "user_info": {
                    'username': user.username,
                    'plan': user.subscription_plan,
                    'old_sold': old_sold,
                    'new_sold': user.sold,
                    'old_total_sold': old_total_sold,
                    'new_total_sold': user.total_sold,
                    'pack_usages': pack.usages
                },
                "status": "success"
            }), 200)
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la synchronisation de l'utilisateur {username} : {str(e)}")
            return make_response(jsonify({
                "message": f"Erreur lors de la synchronisation : {str(e)}",
                "status": "error"
            }), 500)