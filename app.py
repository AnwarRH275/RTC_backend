from flask import Flask
from flask_restx import Api, Resource
from config import DevConfig
from models.exts import db
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from services.auth.auth import auth_ns
from services.auth.stripe import stripe_ns
from services.crud.manage import recipie_ns
from services.crud.tcf_admin import tcf_ns, create_test_subjects
from services.exam.exam import exam_ns
from services.exam.attempt import attempt_ns


app = Flask(__name__)


app.config.from_object(DevConfig)

# Configuration CORS pour permettre les requêtes cross-origin
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"], "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]}}, supports_credentials=False)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
JWTManager(app)

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
api.add_namespace(tcf_ns)
api.add_namespace(exam_ns)
api.add_namespace(attempt_ns)


@app.before_first_request
def initialize_data():
    # Créer les sujets de test TCF
    create_test_subjects()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
