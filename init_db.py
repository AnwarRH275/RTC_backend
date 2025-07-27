import sys
import os

# Assurez-vous que le chemin du backend est dans sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.exts import db

# Importer explicitement tous les modèles pour s'assurer qu'ils sont enregistrés
from models.model import User
from models.tcf_model import TCFSubject, TCFTask, TCFDocument
from models.tcf_exam_model import TCFExam
from models.tcf_attempt_model import TCFAttempt
from models.tcf_model_oral import TCFOralSubject, TCFOralTask

with app.app_context():
    # Créer toutes les tables
    db.create_all()
    print("Base de données initialisée avec succès!")
    print("Tables créées:")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    for table_name in inspector.get_table_names():
        print(f"- {table_name}")