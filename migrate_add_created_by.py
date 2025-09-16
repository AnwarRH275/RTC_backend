#!/usr/bin/env python3
"""
Script de migration pour ajouter le champ 'created_by' à la table User
À exécuter une seule fois après le déploiement des nouvelles fonctionnalités modérateur
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.model import User
from sqlalchemy import text

def migrate_add_created_by_field():
    """Ajoute le champ created_by à la table User si il n'existe pas déjà"""
    
    with app.app_context():
        try:
            # Vérifier si la colonne existe déjà
            result = db.engine.execute(text(
                "PRAGMA table_info(user);"
            ))
            
            columns = [row[1] for row in result]
            
            if 'created_by' not in columns:
                print("Ajout de la colonne 'created_by' à la table User...")
                
                # Ajouter la colonne created_by
                db.engine.execute(text(
                    "ALTER TABLE user ADD COLUMN created_by VARCHAR(80);"
                ))
                
                print("✅ Colonne 'created_by' ajoutée avec succès!")
                
                # Optionnel: Mettre à jour les utilisateurs existants
                # Tous les utilisateurs existants n'ont pas été créés par un modérateur
                # donc on laisse created_by à NULL
                
                print("Migration terminée avec succès!")
            else:
                print("✅ La colonne 'created_by' existe déjà dans la table User.")
                
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {str(e)}")
            db.session.rollback()
            return False
            
    return True

def verify_migration():
    """Vérifie que la migration s'est bien déroulée"""
    
    with app.app_context():
        try:
            # Tester la création d'un utilisateur avec created_by
            test_user = User(
                username='test_migration_user',
                email='test@migration.com',
                password='test_password',
                created_by='test_moderator'
            )
            
            # Ne pas sauvegarder, juste vérifier que l'objet peut être créé
            user_dict = test_user.to_dict()
            
            if 'created_by' in user_dict:
                print("✅ Vérification réussie: Le champ 'created_by' est fonctionnel.")
                return True
            else:
                print("❌ Erreur: Le champ 'created_by' n'apparaît pas dans to_dict().")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {str(e)}")
            return False

if __name__ == '__main__':
    print("=== Migration: Ajout du champ 'created_by' ===")
    print("Cette migration ajoute le champ 'created_by' à la table User")
    print("pour permettre le suivi des utilisateurs créés par les modérateurs.\n")
    
    # Exécuter la migration
    if migrate_add_created_by_field():
        print("\n=== Vérification de la migration ===")
        if verify_migration():
            print("\n🎉 Migration complète et vérifiée avec succès!")
            print("\nLes modérateurs peuvent maintenant:")
            print("- Créer des comptes utilisateurs (rôle 'client' uniquement)")
            print("- Gérer uniquement les comptes qu'ils ont créés")
            print("- Accéder uniquement aux sections 'Gestion de compte' et 'Profil'")
        else:
            print("\n⚠️  Migration effectuée mais la vérification a échoué.")
            print("Veuillez vérifier manuellement la base de données.")
    else:
        print("\n❌ Échec de la migration. Veuillez vérifier les erreurs ci-dessus.")
        sys.exit(1)