from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import jwt_required
from models.subscription_pack_model import SubscriptionPack, PackFeature
from models.exts import db

pack_ns = Namespace('subscription-packs', description='Gestion des packs d\'abonnement')

# Modèle pour les fonctionnalités
feature_model = pack_ns.model(
    "PackFeature",
    {
        "id": fields.Integer(),
        "featureText": fields.String(required=True),
        "orderIndex": fields.Integer(default=0),
        "isActive": fields.Boolean(default=True)
    }
)

# Modèle pour les gradients
gradient_model = pack_ns.model(
    "Gradient",
    {
        "start": fields.String(required=True, description="Couleur de début (hex)"),
        "end": fields.String(required=True, description="Couleur de fin (hex)")
    }
)

# Modèle pour les packs d'abonnement
subscription_pack_model = pack_ns.model(
    "SubscriptionPack",
    {
        "id": fields.Integer(),
        "pack_id": fields.String(required=True),
        "name": fields.String(required=True),
        "price": fields.String(required=True),
        "priceInCents": fields.Integer(required=True),
        "usages": fields.Integer(required=True),
        "color": fields.String(required=True),
        "isPopular": fields.Boolean(default=False),
        "stripeProductId": fields.String(required=True),
        "headerGradient": fields.Nested(gradient_model),
        "buttonGradient": fields.Nested(gradient_model),
        "buttonHoverGradient": fields.Nested(gradient_model),
        "buttonText": fields.String(),
        "isActive": fields.Boolean(default=True),
        "features": fields.List(fields.Nested(feature_model)),
        "createdAt": fields.String(),
        "updatedAt": fields.String()
    }
)

# Modèle pour la création/mise à jour
subscription_pack_input_model = pack_ns.model(
    "SubscriptionPackInput",
    {
        "pack_id": fields.String(required=True),
        "name": fields.String(required=True),
        "price": fields.String(required=True),
        "priceInCents": fields.Integer(required=True),
        "usages": fields.Integer(required=True),
        "color": fields.String(required=True),
        "isPopular": fields.Boolean(default=False),
        "stripeProductId": fields.String(required=True),
        "headerGradient": fields.Nested(gradient_model, required=True),
        "buttonGradient": fields.Nested(gradient_model, required=True),
        "buttonHoverGradient": fields.Nested(gradient_model, required=True),
        "buttonText": fields.String(required=True, default="Payer maintenant"),
        "isActive": fields.Boolean(default=True),
        "features": fields.List(fields.String(), required=True)
    }
)

@pack_ns.route("/packs")
class SubscriptionPackResource(Resource):
    
    @jwt_required()
    def get(self):
        '''Récupérer tous les packs d\'abonnement'''
        try:
            # Filtrer par statut actif si spécifié
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            if active_only:
                packs = SubscriptionPack.query.filter_by(is_active=True).all()
            else:
                packs = SubscriptionPack.query.all()
            
            # Sérialiser manuellement pour garantir la structure correcte
            packs_data = [pack.to_dict() for pack in packs]
            return make_response(jsonify(packs_data), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Erreur lors de la récupération des packs: {str(e)}"}), 500)

    @pack_ns.expect(subscription_pack_input_model)
    @jwt_required()
    def post(self):
        '''Créer un nouveau pack d\'abonnement'''
        try:
            data = request.get_json()
            
            # Validation des données requises
            required_fields = ['pack_id', 'name', 'price', 'priceInCents', 'usages', 'color', 'stripeProductId']
            for field in required_fields:
                if not data.get(field):
                    return make_response(jsonify({"error": f"Le champ {field} est requis"}), 400)
            
            # Vérifier si le pack_id existe déjà
            existing_pack = SubscriptionPack.query.filter_by(pack_id=data.get('pack_id')).first()
            if existing_pack:
                return make_response(jsonify({"error": "Un pack avec cet ID existe déjà"}), 400)
            
            # Validation des gradients
            for gradient_name in ['headerGradient', 'buttonGradient', 'buttonHoverGradient']:
                gradient = data.get(gradient_name, {})
                if not gradient.get('start') or not gradient.get('end'):
                    return make_response(jsonify({"error": f"Les couleurs du gradient {gradient_name} sont requises"}), 400)
            
            # Créer le pack
            new_pack = SubscriptionPack(
                pack_id=data.get('pack_id'),
                name=data.get('name'),
                price=data.get('price'),
                price_in_cents=int(data.get('priceInCents')),
                usages=int(data.get('usages')),
                color=data.get('color'),
                is_popular=data.get('isPopular', False),
                stripe_product_id=data.get('stripeProductId'),
                header_gradient_start=data.get('headerGradient', {}).get('start'),
                header_gradient_end=data.get('headerGradient', {}).get('end'),
                button_gradient_start=data.get('buttonGradient', {}).get('start'),
                button_gradient_end=data.get('buttonGradient', {}).get('end'),
                button_hover_gradient_start=data.get('buttonHoverGradient', {}).get('start'),
                button_hover_gradient_end=data.get('buttonHoverGradient', {}).get('end'),
                button_text=data.get('buttonText', 'Payer maintenant'),
                is_active=data.get('isActive', True)
            )
            new_pack.save()
            
            # Ajouter les fonctionnalités
            if 'features' in data and data['features']:
                for index, feature_text in enumerate(data['features']):
                    if feature_text.strip():  # Ignorer les fonctionnalités vides
                        new_feature = PackFeature(
                            pack_id=new_pack.id,
                            feature_text=feature_text.strip(),
                            order_index=index
                        )
                        new_feature.save()
            
            # Retourner le pack créé avec la structure correcte
            return make_response(jsonify(new_pack.to_dict()), 201)
            
        except ValueError as e:
            return make_response(jsonify({"error": f"Erreur de validation: {str(e)}"}), 400)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": f"Erreur lors de la création du pack: {str(e)}"}), 500)


@pack_ns.route("/packs/<int:id>")
class SubscriptionPackDetailResource(Resource):
    
    @jwt_required()
    def get(self, id):
        '''Récupérer un pack par son ID'''
        try:
            pack = SubscriptionPack.query.get_or_404(id)
            return make_response(jsonify(pack.to_dict()), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Pack non trouvé: {str(e)}"}), 404)

    @pack_ns.expect(subscription_pack_input_model)
    @jwt_required()
    def put(self, id):
        '''Mettre à jour un pack d\'abonnement'''
        try:
            pack = SubscriptionPack.query.get_or_404(id)
            data = request.get_json()
            
            print(f"PUT request data: {data}")
            
            # Validation des données requises
            required_fields = ['pack_id', 'name', 'price', 'priceInCents', 'usages', 'color', 'stripeProductId']
            missing_fields = []
            for field in required_fields:
                if field not in data or data.get(field) is None or (isinstance(data.get(field), str) and not data.get(field).strip()):
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Champs requis manquants: {', '.join(missing_fields)}"
                print(f"Validation error: {error_msg}")
                return make_response(jsonify({"error": error_msg}), 422)

            # Vérifier si le pack_id existe déjà (sauf pour le pack actuel)
            requested_pack_id = data.get('pack_id').strip()
            
            if requested_pack_id != pack.pack_id:
                existing_pack = SubscriptionPack.query.filter_by(pack_id=requested_pack_id).first()
                if existing_pack:
                    return make_response(jsonify({"error": "Un pack avec cet ID existe déjà"}), 422)
            
            # Validation des gradients
            for gradient_name in ['headerGradient', 'buttonGradient', 'buttonHoverGradient']:
                gradient = data.get(gradient_name, {})
                if not isinstance(gradient, dict) or not gradient.get('start') or not gradient.get('end'):
                    error_msg = f"Les couleurs du gradient {gradient_name} sont requises et doivent être un objet avec start et end"
                    print(f"Gradient validation error: {error_msg}")
                    return make_response(jsonify({"error": error_msg}), 422)
            
            # Validation des types numériques
            try:
                price = float(data.get('price'))
                price_in_cents = int(data.get('priceInCents'))
                usages = int(data.get('usages'))
            except (ValueError, TypeError) as e:
                error_msg = f"Erreur de conversion des valeurs numériques: {str(e)}"
                print(f"Numeric validation error: {error_msg}")
                return make_response(jsonify({"error": error_msg}), 422)

            # Supprimer les anciennes fonctionnalités
            for feature in pack.features:
                feature.delete()

            # Mettre à jour le pack
            pack.update(
                pack_id=requested_pack_id,
                name=data.get('name'),
                price=price,
                price_in_cents=price_in_cents,
                usages=usages,
                color=data.get('color'),
                is_popular=data.get('isPopular', False),
                stripe_product_id=data.get('stripeProductId'),
                header_gradient_start=data.get('headerGradient', {}).get('start'),
                header_gradient_end=data.get('headerGradient', {}).get('end'),
                button_gradient_start=data.get('buttonGradient', {}).get('start'),
                button_gradient_end=data.get('buttonGradient', {}).get('end'),
                button_hover_gradient_start=data.get('buttonHoverGradient', {}).get('start'),
                button_hover_gradient_end=data.get('buttonHoverGradient', {}).get('end'),
                button_text=data.get('buttonText', 'Payer maintenant'),
                is_active=data.get('isActive', True)
            )

            # Ajouter les nouvelles fonctionnalités
            if 'features' in data and data['features']:
                print(f"Processing features: {data['features']}")
                for index, feature_data in enumerate(data['features']):
                    # Gérer les features qui peuvent être des objets ou des chaînes
                    feature_text = ''
                    if isinstance(feature_data, dict):
                        feature_text = feature_data.get('featureText', '')
                        print(f"Feature object: {feature_data} -> text: {feature_text}")
                    elif isinstance(feature_data, str):
                        feature_text = feature_data
                        print(f"Feature string: {feature_text}")
                    else:
                        feature_text = str(feature_data) if feature_data is not None else ''
                        print(f"Feature other type: {type(feature_data)} -> {feature_text}")
                    
                    if feature_text and feature_text.strip():  # Ignorer les fonctionnalités vides
                        new_feature = PackFeature(
                            pack_id=pack.id,
                            feature_text=feature_text.strip(),
                            order_index=index
                        )
                        new_feature.save()
                        print(f"Saved feature: {feature_text.strip()}")

            # Retourner le pack mis à jour avec la structure correcte
            result = pack.to_dict()
            print(f"PUT response: {result}")
            return make_response(jsonify(result), 200)
            
        except ValueError as e:
            error_msg = f"Erreur de validation: {str(e)}"
            print(f"ValueError: {error_msg}")
            return make_response(jsonify({"error": error_msg}), 422)
        except Exception as e:
            db.session.rollback()
            error_msg = f"Erreur lors de la mise à jour du pack: {str(e)}"
            print(f"Exception: {error_msg}")
            return make_response(jsonify({"error": error_msg}), 500)

    @jwt_required()
    def delete(self, id):
        '''Supprimer un pack d\'abonnement'''
        pack = SubscriptionPack.query.get_or_404(id)
        pack.delete()
        return {"message": f"Pack {pack.name} supprimé avec succès"}, 200


@pack_ns.route("/packs/<int:id>/toggle-status")
class SubscriptionPackToggleStatusResource(Resource):
    
    @jwt_required()
    def patch(self, id):
        '''Activer/désactiver un pack'''
        try:
            pack = SubscriptionPack.query.get_or_404(id)
            pack.update(is_active=not pack.is_active)
            return make_response(jsonify(pack.to_dict()), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Erreur lors du changement de statut: {str(e)}"}), 500)


@pack_ns.route("/packs/active")
class ActiveSubscriptionPacksResource(Resource):
    
    def get(self):
        '''Récupérer uniquement les packs actifs (pour l\'affichage public)'''
        try:
            packs = SubscriptionPack.query.filter_by(is_active=True).order_by(SubscriptionPack.price_in_cents).all()
            packs_data = [pack.to_dict() for pack in packs]
            return make_response(jsonify(packs_data), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Erreur lors de la récupération des packs actifs: {str(e)}"}), 500)


@pack_ns.route("/active-packs")
class ActivePacksResource(Resource):
    
    def get(self):
        '''Récupérer uniquement les packs actifs (endpoint alternatif pour compatibilité)'''
        try:
            packs = SubscriptionPack.query.filter_by(is_active=True).order_by(SubscriptionPack.price_in_cents).all()
            packs_data = [pack.to_dict() for pack in packs]
            return make_response(jsonify(packs_data), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Erreur lors de la récupération des packs actifs: {str(e)}"}), 500)


# Fonction pour créer des packs par défaut
def create_default_packs():
    """Créer les packs par défaut si aucun n'existe"""
    if SubscriptionPack.query.count() == 0:
        # Pack Standard
        standard_pack = SubscriptionPack(
            pack_id='standard',
            name='Pack Écrit Standard',
            price='14',
            price_in_cents=1499,
            usages=5,
            color='standard',
            is_popular=False,
            stripe_product_id='prod_SMeQcS5gdyO7Nh',
            header_gradient_start='#0062E6',
            header_gradient_end='#33AEFF',
            button_gradient_start='#0062E6',
            button_gradient_end='#33AEFF',
            button_hover_gradient_start='#0062E6',
            button_hover_gradient_end='#0062E6'
        )
        standard_pack.save()
        
        # Fonctionnalités du pack standard
        standard_features = [
            "5 examens réels basés sur les sujets d'actualité 2025",
            "Remarques personnalisées sur chaque production",
            "Modèles corrigés pour chaque tâche",
            "Accès complet au Coach d'Expression Écrite",
            "Simulation en conditions réelles",
            "Note estimée selon le CECR"
        ]
        
        for index, feature_text in enumerate(standard_features):
            feature = PackFeature(
                pack_id=standard_pack.id,
                feature_text=feature_text,
                order_index=index
            )
            feature.save()
        
        # Pack Performance
        performance_pack = SubscriptionPack(
            pack_id='performance',
            name='Pack Écrit Performance',
            price='29',
            price_in_cents=2999,
            usages=15,
            color='performance',
            is_popular=True,
            stripe_product_id='prod_SMePWWnxhhQXZJ',
            header_gradient_start='#FF512F',
            header_gradient_end='#DD2476',
            button_gradient_start='#FF512F',
            button_gradient_end='#DD2476',
            button_hover_gradient_start='#DD2476',
            button_hover_gradient_end='#DD2476'
        )
        performance_pack.save()
        
        # Fonctionnalités du pack performance
        performance_features = [
            "15 examens réels basés sur les sujets d'actualité 2025",
            "Remarques personnalisées sur chaque production",
            "Modèles corrigés pour chaque tâche",
            "Accès complet au Coach d'Expression Écrite",
            "Simulation en conditions réelles",
            "Note estimée selon le CECR"
        ]
        
        for index, feature_text in enumerate(performance_features):
            feature = PackFeature(
                pack_id=performance_pack.id,
                feature_text=feature_text,
                order_index=index
            )
            feature.save()
        
        # Pack Pro
        pro_pack = SubscriptionPack(
            pack_id='pro',
            name='Pack Écrit Pro',
            price='49',
            price_in_cents=4999,
            usages=30,
            color='pro',
            is_popular=False,
            stripe_product_id='prod_SMeQ8tIJeu8sHA',
            header_gradient_start='#11998e',
            header_gradient_end='#38ef7d',
            button_gradient_start='#11998e',
            button_gradient_end='#38ef7d',
            button_hover_gradient_start='#11998e',
            button_hover_gradient_end='#11998e'
        )
        pro_pack.save()
        
        # Fonctionnalités du pack pro
        pro_features = [
            "30 examens réels basés sur les sujets d'actualité 2025",
            "Remarques personnalisées sur chaque production",
            "Modèles corrigés pour chaque tâche",
            "Accès complet au Coach d'Expression Écrite",
            "Simulation en conditions réelles",
            "Note estimée selon le CECR"
        ]
        
        for index, feature_text in enumerate(pro_features):
            feature = PackFeature(
                pack_id=pro_pack.id,
                feature_text=feature_text,
                order_index=index
            )
            feature.save()
        
        print("Packs d'abonnement par défaut créés avec succès!")