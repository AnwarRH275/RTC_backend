#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Désactiver les logs SQLAlchemy
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from models.exts import db
from models.order_model import Order
from models.model import User
from app import app
from datetime import datetime, timedelta

def main():
    with app.app_context():
        print("=== DIAGNOSTIC ORDRES TCF CANADA ===")
        print()
        
        # 1. Compter les ordres
        total_orders = Order.query.count()
        print(f"📊 TOTAL ORDRES: {total_orders}")
        
        if total_orders == 0:
            print("❌ PROBLÈME IDENTIFIÉ: Aucun ordre dans la base de données")
        else:
            print(f"✅ {total_orders} ordre(s) trouvé(s)")
        
        print()
        
        # 2. Compter les utilisateurs
        total_users = User.query.count()
        print(f"👥 TOTAL UTILISATEURS: {total_users}")
        
        # 3. Utilisateurs récents (7 jours)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = User.query.filter(User.date_create >= week_ago).all()
        print(f"🆕 UTILISATEURS RÉCENTS (7 jours): {len(recent_users)}")
        
        print()
        
        # 4. Vérifier chaque utilisateur récent
        if recent_users:
            print("📋 DÉTAIL DES UTILISATEURS RÉCENTS:")
            for user in recent_users:
                user_orders = Order.query.filter_by(user_id=user.id).count()
                status = "❌ AUCUN ORDRE" if user_orders == 0 else f"✅ {user_orders} ordre(s)"
                print(f"   • {user.email} ({user.subscription_plan or 'Aucun plan'}): {status}")
        else:
            print("ℹ️  Aucun utilisateur créé récemment")
        
        print()
        
        # 5. Configuration Stripe
        print("🔧 CONFIGURATION STRIPE:")
        stripe_mode = app.config.get('STRIPE_MODE', 'non configuré')
        print(f"   • Mode: {stripe_mode}")
        
        webhook_secret = app.config.get('STRIPE_TEST_WEBHOOK_SECRET')
        if not webhook_secret or webhook_secret == 'whsec_test_webhook_secret':
            print("   • Webhook: ❌ SECRET PAR DÉFAUT (PROBLÈME!)")
        else:
            print("   • Webhook: ✅ Configuré")
        
        print()
        
        # 6. Diagnostic final
        print("🔍 DIAGNOSTIC:")
        if total_orders == 0 and len(recent_users) > 0:
            print("   ❌ PROBLÈME CONFIRMÉ: Des utilisateurs s'inscrivent mais aucun ordre n'est créé")
            print("   🔧 CAUSES POSSIBLES:")
            print("      1. Webhook Stripe mal configuré")
            print("      2. Erreurs dans le processus de paiement")
            print("      3. Problème dans create_order_and_update_user()")
            print("      4. Les utilisateurs ne complètent pas le paiement")
        elif total_orders == 0:
            print("   ℹ️  Aucun ordre et aucun utilisateur récent")
        else:
            print("   ✅ Les ordres sont créés normalement")

if __name__ == '__main__':
    main()