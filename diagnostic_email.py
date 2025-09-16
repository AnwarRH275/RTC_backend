#!/usr/bin/env python3
"""
Script de diagnostic pour les problèmes de réception d'emails

Usage:
    python diagnostic_email.py votre-email@example.com
"""

import sys
import os
from dotenv import load_dotenv
from services.email.email_service import email_service
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Charger les variables d'environnement
load_dotenv()

def test_simple_email(destination_email):
    """
    Teste l'envoi d'un email simple
    """
    print(f"📧 Test d'envoi d'email simple vers: {destination_email}")
    
    try:
        # Créer un message simple
        message = MIMEMultipart("alternative")
        message["Subject"] = "🧪 Test de diagnostic - Réussir TCF Canada"
        message["From"] = f"{email_service.from_name} <{email_service.from_email}>"
        message["To"] = destination_email
        
        # Contenu simple
        html_content = """
        <html>
        <body>
            <h2>🧪 Test de diagnostic</h2>
            <p>Si vous recevez cet email, la configuration SMTP fonctionne correctement.</p>
            <p><strong>Serveur:</strong> {}</p>
            <p><strong>Expéditeur:</strong> {}</p>
            <p><strong>Heure:</strong> {}</p>
        </body>
        </html>
        """.format(email_service.smtp_server, email_service.from_email, 
                   __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        text_content = f"""
        Test de diagnostic
        
        Si vous recevez cet email, la configuration SMTP fonctionne correctement.
        
        Serveur: {email_service.smtp_server}
        Expéditeur: {email_service.from_email}
        Heure: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Ajouter les contenus
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(text_part)
        message.attach(html_part)
        
        # Envoyer l'email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(email_service.smtp_server, email_service.smtp_port, context=context) as server:
            server.login(email_service.smtp_username, email_service.smtp_password)
            server.sendmail(email_service.from_email, destination_email, message.as_string())
            
        print("✅ Email de diagnostic envoyé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {str(e)}")
        return False

def print_diagnostic_info():
    """
    Affiche les informations de diagnostic
    """
    print("\n🔍 DIAGNOSTIC EMAIL - Réussir TCF Canada")
    print("=" * 50)
    
    print("\n📋 Configuration SMTP actuelle:")
    print(f"   - Serveur: {email_service.smtp_server}")
    print(f"   - Port: {email_service.smtp_port}")
    print(f"   - Username: {email_service.smtp_username}")
    print(f"   - Expéditeur: {email_service.from_email}")
    print(f"   - Nom: {email_service.from_name}")
    
    print("\n🔧 Vérifications à effectuer:")
    print("   1. ✉️  Vérifiez votre dossier SPAM/Courrier indésirable")
    print("   2. 📧 Vérifiez que l'adresse email est correcte")
    print("   3. ⏰ Attendez quelques minutes (délai de livraison)")
    print("   4. 🔒 Vérifiez les filtres de votre messagerie")
    print("   5. 📱 Vérifiez sur différents clients email (web, mobile, desktop)")
    
    print("\n⚠️  Causes possibles de non-réception:")
    print("   • L'email est dans le dossier spam")
    print("   • Délai de livraison (peut prendre jusqu'à 15 minutes)")
    print("   • Filtres anti-spam du fournisseur email")
    print("   • Adresse email incorrecte ou inexistante")
    print("   • Boîte de réception pleine")
    
    print("\n💡 Solutions recommandées:")
    print("   1. Ajoutez support@reussir-tcfcanada.com à vos contacts")
    print("   2. Vérifiez les paramètres anti-spam de votre messagerie")
    print("   3. Testez avec une autre adresse email")
    print("   4. Contactez votre fournisseur email si le problème persiste")

def main():
    if len(sys.argv) != 2:
        print("Usage: python diagnostic_email.py votre-email@example.com")
        sys.exit(1)
    
    destination_email = sys.argv[1]
    
    # Validation basique de l'email
    if '@' not in destination_email or '.' not in destination_email:
        print("❌ Format d'email invalide")
        sys.exit(1)
    
    print_diagnostic_info()
    
    print("\n🧪 TESTS DE DIAGNOSTIC")
    print("=" * 30)
    
    # Test de connexion SMTP
    print("\n1. Test de connexion SMTP...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(email_service.smtp_server, email_service.smtp_port, context=context) as server:
            server.login(email_service.smtp_username, email_service.smtp_password)
            print("   ✅ Connexion SMTP réussie")
    except Exception as e:
        print(f"   ❌ Échec connexion SMTP: {e}")
        return
    
    # Test d'envoi d'email simple
    print("\n2. Test d'envoi d'email de diagnostic...")
    success = test_simple_email(destination_email)
    
    if success:
        print("\n✅ RÉSULTAT: Email envoyé avec succès!")
        print(f"📬 Vérifiez votre boîte de réception: {destination_email}")
        print("⏰ Si vous ne recevez pas l'email dans les 5-10 minutes:")
        print("   • Vérifiez le dossier spam")
        print("   • Testez avec une autre adresse email")
        print("   • Contactez le support technique")
    else:
        print("\n❌ RÉSULTAT: Échec de l'envoi")
        print("🔧 Vérifiez la configuration SMTP dans le fichier .env")

if __name__ == "__main__":
    main()