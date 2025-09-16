from flask import Flask
from flask_restx import Api, Resource
from config import DevConfig, ProdConfig
import os
from models.exts import db
from models.subscription_pack_model import SubscriptionPack, PackFeature
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from services.auth.auth import auth_ns
from services.auth.stripe import stripe_ns
from services.auth.sync_usages import sync_ns

from services.crud.tcf_admin import tcf_ns, create_test_subjects
from services.crud.tcf_admin_oral import tcf_oral_ns
from services.exam.exam import exam_ns
from services.exam.attempt import attempt_ns
from services.exam.synthesis import synthesis_ns
from services.exam.dashboard import dashboard_ns
from services.crud.subscription_pack_admin import pack_ns, create_default_packs
from services.crud.order_admin import order_admin_ns
from services.crud.order_public import order_public_ns
from services.proxy.correction_proxy import proxy_ns
from services.proxy.translation_proxy import proxy_translation_ns
from services.proxy.note_moyenne_proxy import proxy_note_moyenne_ns
from services.proxy.task2_proxy import proxy_task2_ns
from services.proxy.task1_proxy import proxy_task1_ns
from services.proxy.oral_proxy import oral_proxy_ns


app = Flask(__name__)

# Configuration basée sur l'environnement
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProdConfig)
else:
    app.config.from_object(DevConfig)

# Configuration CORS adaptée pour la production
if os.environ.get('FLASK_ENV') == 'production':
    # Configuration CORS pour la production - domaines spécifiques
    CORS(app, resources={r"/*": {
        "origins": ["https://expressiontcf.com", "https://www.expressiontcf.com", "https://api.expressiontcf.com"],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        "supports_credentials": True,
        "expose_headers": ["Content-Range", "X-Content-Range"]
    }})
else:
    # Configuration CORS pour le développement - permissive
    CORS(app, resources={r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": False
    }})
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
jwt = JWTManager(app)

# Gestion des erreurs JWT
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'msg': 'Token invalide'}, 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'msg': 'Token expiré'}, 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {'msg': 'Token d\'autorisation requis'}, 422

# Gestionnaire d'erreur global pour les erreurs JWT
@app.errorhandler(422)
def handle_jwt_exceptions(error):
    if 'Not enough segments' in str(error):
        return {'msg': 'Token JWT malformé'}, 422
    return {'msg': 'Erreur de validation'}, 422

db.init_app(app)

migrate = Migrate(app, db)
# Désactiver l'authentification par défaut pour tous les endpoints
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(app, doc='/docs', authorizations=authorizations, security=None)

'''
    Create Migration repository
    $ flask db init 
    Apply Frist Migration
    $ flask db migrate  -m "add table"  
    Apply current revision db 'commit'
    $ flask db upgrade
'''


api.add_namespace(auth_ns)
api.add_namespace(stripe_ns)
api.add_namespace(sync_ns)
api.add_namespace(tcf_ns)
api.add_namespace(tcf_oral_ns)
api.add_namespace(exam_ns)
api.add_namespace(attempt_ns)
api.add_namespace(synthesis_ns)
api.add_namespace(dashboard_ns)
api.add_namespace(pack_ns)
api.add_namespace(order_admin_ns)
api.add_namespace(order_public_ns)
api.add_namespace(proxy_ns)
api.add_namespace(proxy_translation_ns)
api.add_namespace(proxy_note_moyenne_ns)
api.add_namespace(proxy_task2_ns)
api.add_namespace(proxy_task1_ns)
api.add_namespace(oral_proxy_ns)


@app.before_first_request
def initialize_data():
    # Créer les sujets de test TCF
    create_test_subjects()
    # Créer les packs d'abonnement par défaut
    create_default_packs()

if __name__ == '__main__':
    # Activer le threading pour permettre le traitement concurrent des requêtes
    app.run(debug=True, port=5002, threaded=True)
else:
    application = app
#docker build --platform linux/amd64 -f Dockerfile.dev -t reussir-tcf-backend-dev-linux . 
#ls -lh reussir-tcf-backend-dev-linux.tar && file reussir-tcf-backend-dev-linux.tar