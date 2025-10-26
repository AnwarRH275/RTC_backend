#!/usr/bin/env python3
"""
Script d'initialisation et de migration automatique pour Docker Compose
Ce script :
1. Initialise la base de données MySQL
2. Migre automatiquement les données depuis SQLite (dev.db) vers MySQL
3. Exécute les migrations nécessaires
"""

import os
import sys
import time
import sqlite3
from contextlib import closing

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.exts import db as db_ext

# Import des scripts de migration existants
from migrate_sqlite_to_mariadb import main as migrate_sqlite_main
from migrate_add_created_by import migrate_add_created_by_field, verify_migration

def wait_for_mysql(max_retries=30, delay=2):
    """Attendre que MySQL soit disponible"""
    print("🔄 Attente de la disponibilité de MySQL...")
    
    for attempt in range(max_retries):
        try:
            with app.app_context():
                # Tenter une connexion simple
                db.engine.execute("SELECT 1")
                print("✅ MySQL est disponible!")
                return True
        except Exception as e:
            print(f"⏳ Tentative {attempt + 1}/{max_retries} - MySQL non disponible: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                print("❌ Impossible de se connecter à MySQL après plusieurs tentatives")
                return False
    
    return False

def initialize_database():
    """Initialiser la base de données MySQL"""
    print("🔧 Initialisation de la base de données MySQL...")
    
    try:
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables créées avec succès!")
            return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {str(e)}")
        return False

def check_sqlite_exists():
    """Vérifier si le fichier SQLite existe"""
    sqlite_path = os.path.join(os.path.dirname(__file__), 'dev.db')
    return os.path.exists(sqlite_path)

def is_database_empty():
    """Vérifier si la base de données MySQL est vide"""
    try:
        with app.app_context():
            # Vérifier si la table user existe et contient des données
            result = db.engine.execute("SELECT COUNT(*) FROM user")
            count = result.fetchone()[0]
            return count == 0
    except Exception:
        # Si la table n'existe pas ou autre erreur, considérer comme vide
        return True

def migrate_sqlite_to_mysql():
    """Migrer les données de SQLite vers MySQL"""
    print("📦 Migration des données SQLite vers MySQL...")
    
    if not check_sqlite_exists():
        print("⚠️  Fichier dev.db non trouvé, migration SQLite ignorée")
        return True
    
    if not is_database_empty():
        print("ℹ️  La base de données MySQL contient déjà des données, migration SQLite ignorée")
        return True
    
    try:
        # Exécuter la migration SQLite vers MySQL
        migrate_sqlite_main()
        print("✅ Migration SQLite vers MySQL terminée!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la migration SQLite: {str(e)}")
        return False

def run_additional_migrations():
    """Exécuter les migrations supplémentaires"""
    print("🔄 Exécution des migrations supplémentaires...")
    
    try:
        # Migration pour ajouter le champ created_by
        if migrate_add_created_by_field():
            print("✅ Migration 'created_by' terminée!")
            
            # Vérifier la migration
            if verify_migration():
                print("✅ Vérification de la migration réussie!")
            else:
                print("⚠️  Vérification de la migration échouée")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors des migrations supplémentaires: {str(e)}")
        return False

def main():
    """Fonction principale d'initialisation et migration"""
    print("🚀 === Initialisation et Migration Automatique ===")
    print("Ce script va :")
    print("1. Attendre que MySQL soit disponible")
    print("2. Initialiser la base de données MySQL")
    print("3. Migrer les données depuis SQLite (si disponible)")
    print("4. Exécuter les migrations supplémentaires")
    print()
    
    # Étape 1: Attendre MySQL
    if not wait_for_mysql():
        print("❌ Impossible de continuer sans MySQL")
        sys.exit(1)
    
    # Étape 2: Initialiser la base de données
    if not initialize_database():
        print("❌ Échec de l'initialisation de la base de données")
        sys.exit(1)
    
    # Étape 3: Migrer SQLite vers MySQL (si nécessaire)
    if not migrate_sqlite_to_mysql():
        print("❌ Échec de la migration SQLite")
        sys.exit(1)
    
    # Étape 4: Migrations supplémentaires
    if not run_additional_migrations():
        print("❌ Échec des migrations supplémentaires")
        sys.exit(1)
    
    print()
    print("🎉 === Initialisation et Migration Terminées avec Succès! ===")
    print("📊 phpMyAdmin est accessible sur: http://localhost:8080")
    print("🔗 Backend API sera disponible sur: http://localhost:5001")
    print("👤 Utilisateur MySQL: admin_tcf_canada_STZ")
    print("🔑 Mot de passe MySQL: admin_tcf_canada_STZ")
    print()

if __name__ == '__main__':
    main()