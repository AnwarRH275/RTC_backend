#!/bin/bash
set -e

echo "=== Démarrage du conteneur Ubuntu avec migration automatique ==="
echo "Timestamp: $(date)"

# Fonction pour vérifier la disponibilité de la base de données
check_database() {
    echo "Vérification de la disponibilité de la base de données..."
    
    python3 -c "
import time
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

database_url = os.getenv('DATABASE_URL')
if not database_url:
    print('ERREUR: DATABASE_URL non définie')
    sys.exit(1)

print(f'Connexion à: {database_url}')
engine = create_engine(database_url)
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        with engine.connect() as conn:
            conn.execute('SELECT 1')
        print('✓ Base de données disponible!')
        break
    except OperationalError as e:
        retry_count += 1
        print(f'Tentative {retry_count}/{max_retries} - Base de données non disponible: {e}')
        time.sleep(2)
else:
    print('ERREUR: Impossible de se connecter à la base de données après 30 tentatives')
    sys.exit(1)
"
}

# Fonction pour initialiser les tables
init_tables() {
    echo "Initialisation des tables..."
    python3 init_db.py
    if [ $? -eq 0 ]; then
        echo "✓ Tables initialisées avec succès"
    else
        echo "✗ Erreur lors de l'initialisation des tables"
        exit 1
    fi
}

# Fonction pour vérifier si la migration est nécessaire
check_migration_needed() {
    echo "Vérification de la nécessité de migration..."
    
    python3 -c "
from app import app
from models.exts import db
from models.model import User

with app.app_context():
    try:
        user_count = User.query.count()
        print(f'Nombre d\'utilisateurs existants: {user_count}')
        if user_count == 0:
            print('MIGRATION_NEEDED')
        else:
            print('MIGRATION_NOT_NEEDED')
    except Exception as e:
        print(f'Erreur lors de la vérification: {e}')
        print('MIGRATION_NEEDED')
"
}

# Fonction pour effectuer la migration
perform_migration() {
    echo "🔄 Migration des données depuis dev.db vers MariaDB..."
    
    # Vérifier que dev.db existe
    if [ ! -f "dev.db" ]; then
        echo "✗ ERREUR: Fichier dev.db non trouvé!"
        exit 1
    fi
    
    echo "📁 Fichier dev.db trouvé ($(du -h dev.db | cut -f1))"
    
    # Effectuer la migration
    python3 migrate_sqlite_to_mariadb.py
    
    if [ $? -eq 0 ]; then
        echo "✓ Migration terminée avec succès!"
    else
        echo "✗ Erreur lors de la migration"
        exit 1
    fi
}

# Fonction principale
main() {
    # Vérifier les variables d'environnement
    if [ -z "$DATABASE_URL" ]; then
        echo "✗ ERREUR: Variable DATABASE_URL non définie"
        exit 1
    fi
    
    echo "📊 Configuration:"
    echo "  - DATABASE_URL: ${DATABASE_URL}"
    echo "  - FLASK_ENV: ${FLASK_ENV:-development}"
    echo "  - Working Directory: $(pwd)"
    
    # Étapes de démarrage
    check_database
    init_tables
    
    # Vérifier si migration nécessaire
    MIGRATION_STATUS=$(check_migration_needed)
    
    if echo "$MIGRATION_STATUS" | grep -q "MIGRATION_NEEDED"; then
        perform_migration
    else
        echo "ℹ️  Migration non nécessaire - données déjà présentes"
    fi
    
    # Afficher un résumé final
    echo "📈 Résumé final des données:"
    python3 -c "
from app import app
from models.exts import db
from models.model import User
from models.subscription_pack_model import SubscriptionPack
from models.order_model import Order

with app.app_context():
    try:
        users = User.query.count()
        packs = SubscriptionPack.query.count()
        orders = Order.query.count()
        print(f'  - Utilisateurs: {users}')
        print(f'  - Packs: {packs}')
        print(f'  - Commandes: {orders}')
    except Exception as e:
        print(f'  - Erreur lors du résumé: {e}')
"
    
    # Démarrer l'application Flask
    echo "🚀 Démarrage de l'application Flask sur le port 5001..."
    exec python3 -m flask run --host=0.0.0.0 --port=5001
}

# Gestion des signaux pour un arrêt propre
trap 'echo "Signal reçu, arrêt en cours..."; exit 0' SIGTERM SIGINT

# Exécuter la fonction principale
main "$@"