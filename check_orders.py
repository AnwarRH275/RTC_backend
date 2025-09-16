#!/usr/bin/env python3
"""
Script simple pour vérifier les ordres dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.exts import db
from models.order_model import Order
from models.model import User
from app import app
from datetime import datetime, timedelta

def main():
    with app.app_context():
        print("=== Vérification des Ordres TCF Canada ===")
        
        # Compter les ordres
        total_orders = Order.query.count()
        print(f"Total des ordres: {total_orders}")
        
        if total_orders == 0:
            print("❌ PROBLÈME: Aucun ordre trouvé dans la base de données")
        else:
            print(f"✅ {total_orders} ordre(s) trouvé(s)")
            
            # Afficher quelques ordres
            orders = Order.query.limit(5).all()
            for order in orders:
                print(f"  - {order.order_number}: {order.amount} {order.currency} ({order.status})")
        
        # Compter les utilisateurs
        total_users = User.query.count()
        print(f"\nTotal des utilisateurs: {total_users}")
        
        # Utilisateurs récents
        yesterday = datetime.utcnow() - timedelta(days=7)  # 7 jours
        recent_users = User.query.filter(User.date_create >= yesterday).all()
        print(f"Utilisateurs créés dans les 7 derniers jours: {len(recent_users)}")
        
        for user in recent_users:
            user_orders = Order.query.filter_by(user_id=user.id).count()
            print(f"  - {user.email}: {user_orders} ordre(s)")
        
        # Configuration Stripe
        print(f"\nConfiguration Stripe:")
        print(f"  Mode: {app.config.get('STRIPE_MODE')}")
        webhook_secret = app.config.get('STRIPE_TEST_WEBHOOK_SECRET')
        print(f"  Webhook secret: {'Configuré' if webhook_secret and webhook_secret != 'whsec_test_webhook_secret' else 'Par défaut (problème!)'}")

if __name__ == '__main__':
    main()