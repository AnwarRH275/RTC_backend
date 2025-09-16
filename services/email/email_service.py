import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List
from jinja2 import Template
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.hostinger.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '465'))
        self.smtp_username = os.getenv('SMTP_USERNAME', 'support@reussir-tcfcanada.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', 'W^0]Euh4z')
        self.from_email = os.getenv('FROM_EMAIL', 'support@reussir-tcfcanada.com')
        self.from_name = os.getenv('FROM_NAME', 'Réussir TCF Canada')
        
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envoie un email avec contenu HTML et texte optionnel
        
        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            text_content: Contenu texte alternatif (optionnel)
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            # Créer le message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Ajouter le contenu texte si fourni
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # Créer une connexion sécurisée et envoyer l'email
            context = ssl.create_default_context()
            
            # Utiliser SMTP avec STARTTLS pour Brevo (port 587) ou SMTP_SSL pour port 465
            if self.smtp_port == 587:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            else:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.from_email, to_email, message.as_string())
                
            logger.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, user_data: dict, order_number: str = None) -> bool:
        """
        Envoie un email de bienvenue à un nouvel utilisateur
        
        Args:
            user_data: Dictionnaire contenant les informations de l'utilisateur
                      (username, email, nom, prenom, subscription_plan, sold, etc.)
            order_number: Numéro de commande optionnel
                      
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            # Générer le contenu de l'email de bienvenue
            html_content = self._generate_welcome_email_html(user_data, order_number)
            text_content = self._generate_welcome_email_text(user_data, order_number)
            
            subject = f"🎉 Bienvenue chez Expression TCF, {user_data.get('prenom', user_data.get('username', ''))}!"
            
            return self.send_email(
                to_email=user_data['email'],
                subject=subject,
                html_content=html_content,  
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
            return False
    
    def send_password_reset_email(self, user_data: dict, reset_token: str) -> bool:
        """
        Envoie un email de réinitialisation de mot de passe
        
        Args:
            user_data: Dictionnaire contenant les informations de l'utilisateur (email, username, nom, prenom)
            reset_token: Token de réinitialisation généré
                      
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            # Générer le contenu de l'email de reset
            html_content = self._generate_reset_email_html(user_data, reset_token)
            text_content = self._generate_reset_email_text(user_data, reset_token)
            
            subject = "🔐 Réinitialisation de votre mot de passe - Expression TCF"
            
            return self.send_email(
                to_email=user_data['email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de reset: {str(e)}")
            return False
    
    def _generate_welcome_email_html(self, user_data: dict, order_number: str = None) -> str:
        """
        Génère le contenu HTML de l'email de bienvenue
        """
        # Déterminer le nom d'affichage
        display_name = f"{user_data.get('prenom', '')} {user_data.get('nom', '')}".strip()
        if not display_name:
            display_name = user_data.get('username', 'Cher utilisateur')
        
        # Informations sur le plan
        plan_info = self._get_plan_info(user_data.get('subscription_plan', ''))
        
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue chez Expression TCF</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8fafc;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px 30px;
        }
        
        .welcome-message {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .welcome-message h2 {
            color: #2d3748;
            font-size: 24px;
            margin-bottom: 15px;
        }
        
        .welcome-message p {
            color: #718096;
            font-size: 16px;
        }
        
        .plan-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 12px;
            padding: 25px;
            margin: 30px 0;
            color: white;
            text-align: center;
        }
        
        .plan-card h3 {
            font-size: 20px;
            margin-bottom: 10px;
        }
        
        .plan-card .plan-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .credits-info {
            background-color: #f7fafc;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #4299e1;
        }
        
        .credits-info h4 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .credits-amount {
            font-size: 24px;
            font-weight: 700;
            color: #4299e1;
        }
        
        .features {
            margin: 30px 0;
        }
        
        .features h3 {
            color: #2d3748;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .feature-list {
            list-style: none;
        }
        
        .feature-list li {
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
        }
        
        .feature-list li:last-child {
            border-bottom: none;
        }
        
        .feature-icon {
            width: 20px;
            height: 20px;
            background-color: #48bb78;
            border-radius: 50%;
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
        }
        
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            text-align: center;
            margin: 20px 0;
            transition: transform 0.2s;
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
        }
        
        .footer {
            background-color: #2d3748;
            color: #a0aec0;
            padding: 30px;
            text-align: center;
        }
        
        .footer p {
            margin-bottom: 10px;
        }
        
        .social-links {
            margin-top: 20px;
        }
        
        .social-links a {
            color: #a0aec0;
            text-decoration: none;
            margin: 0 10px;
        }
        
        @media (max-width: 600px) {
            .container {
                margin: 10px;
                border-radius: 8px;
            }
            
            .header, .content {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Expression TCF</h1>
            <p>Votre plateforme de préparation au TCF Canada</p>
        </div>
        
        <div class="content">
            <div class="welcome-message">
                <h2>Bienvenue {{ display_name }}! 🎉</h2>
                <p>Nous sommes ravis de vous accueillir dans la communauté Expression TCF. Votre compte a été créé avec succès et vous êtes maintenant prêt(e) à commencer votre préparation au TCF Canada.</p>
            </div>
            
            <div class="plan-card">
                <h3>🚀 Votre Plan d'Abonnement</h3>
                <div class="plan-name">{{ plan_info.name }}</div>
                <p>{{ plan_info.description }}</p>
            </div>
            
            <div class="credits-info">
                <h4>💰 Vos Crédits Disponibles</h4>
                <div class="credits-amount">{{ user_data.get('sold', 0) }} crédits</div>
                <p>Utilisez vos crédits pour accéder aux examens et corrections personnalisées.</p>
            </div>
            
            {% if order_number %}
            <div class="credits-info" style="border-left: 4px solid #48bb78;">
                <h4>📋 Numéro de Commande</h4>
                <div class="credits-amount" style="color: #48bb78;">{{ order_number }}</div>
                <p>Conservez ce numéro pour vos références et support client.</p>
            </div>
            {% endif %}
            
            <div class="features">
                <h3>🎯 Ce que vous pouvez faire maintenant</h3>
                <ul class="feature-list">
                    <li>
                        <div class="feature-icon">✓</div>
                       <span>Passer des examens TCF complets avec correction instantanée</span>
                    </li>
                    <li>
                        <div class="feature-icon">✓</div>
                        <span>Recevoir des feedbacks personnalisés sur vos performances</span>
                    </li>
                    <li>
                        <div class="feature-icon">✓</div>
                        <span>Suivre votre progression avec des statistiques détaillées</span>
                    </li>
                    <li>
                        <div class="feature-icon">✓</div>
                        <span>Accéder à des ressources pédagogiques exclusives</span>
                    </li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="https://expressiontcf.com/dashboard" class="cta-button">
                    🚀 Commencer maintenant
                </a>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background-color: #fff5f5; border-radius: 8px; border-left: 4px solid #f56565;">
                <h4 style="color: #c53030; margin-bottom: 10px;">📧 Informations importantes</h4>
                <p style="color: #742a2a; font-size: 14px;">
                    • Conservez cet email pour vos dossiers<br>
                    • Votre nom d'utilisateur: <strong>{{ user_data.get('username', '') }}</strong><br>
                    • Si vous rencontrez un problème avec votre connexion, n'hésitez pas à nous contacter à l'adresse info@reussir-tcfcanada.com
                </p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Expression TCF</strong> - Votre succès au TCF Canada</p>
            <p>📧 info@reussir-tcfcanada.com | 🌐 www.expressiontcf.com</p>
            <div class="social-links">
                <a href="#">Facebook</a>
                <a href="#">Twitter</a>
                <a href="#">LinkedIn</a>
            </div>
            <p style="margin-top: 20px; font-size: 12px; opacity: 0.7;">
                © 2025 Expression TCF. Tous droits réservés.
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        return template.render(
            display_name=display_name,
            user_data=user_data,
            plan_info=plan_info,
            order_number=order_number
        )
    
    def _generate_welcome_email_text(self, user_data: dict, order_number: str = None) -> str:
        """
        Génère le contenu texte de l'email de bienvenue
        """
        display_name = f"{user_data.get('prenom', '')} {user_data.get('nom', '')}".strip()
        if not display_name:
            display_name = user_data.get('username', 'Cher utilisateur')
        
        plan_info = self._get_plan_info(user_data.get('subscription_plan', ''))
        
        order_info = f"\n- Numéro de commande: {order_number}" if order_number else ""
        
        return f"""
Bienvenue {display_name}!

Nous sommes ravis de vous accueillir dans la communauté Expression TCF.

Votre compte a été créé avec succès avec les informations suivantes:
- Nom d'utilisateur: {user_data.get('username', '')}
- Plan d'abonnement: {plan_info['name']}
- Crédits disponibles: {user_data.get('sold', 0)} crédits{order_info}

Vous pouvez maintenant:
✓ Passer des examens TCF complets avec correction IA
✓ Recevoir des feedbacks personnalisés sur vos performances
✓ Suivre votre progression avec des statistiques détaillées
✓ Accéder à des ressources pédagogiques exclusives

Commencez dès maintenant: https://expressiontcf.com/dashboard

Si vous rencontrez un problème avec votre connexion, n'hésitez pas à nous contacter à l'adresse info@reussir-tcfcanada.com

Bonne préparation!
L'équipe Expression TCF
        """
    
    def _get_plan_info(self, plan_id: str) -> dict:
        """
        Retourne les informations sur le plan d'abonnement
        """
        plans = {
            'basic': {
                'name': '🥉 Plan Basic',
                'description': 'Accès aux fonctionnalités essentielles pour débuter votre préparation au TCF Canada.'
            },
            'premium': {
                'name': '🥈 Plan Premium',
                'description': 'Accès complet avec corrections avancées et suivi personnalisé de vos progrès.'
            },
            'pro': {
                'name': '🥇 Plan Pro',
                'description': 'L\'expérience ultime avec tous les outils et un accompagnement personnalisé.'
            },
            'enterprise': {
                'name': '💎 Plan Enterprise',
                'description': 'Solution complète pour les institutions et les groupes d\'étudiants.'
            }
        }
        
        return plans.get(plan_id.lower(), {
            'name': '📚 Plan Personnalisé',
            'description': 'Votre plan d\'abonnement personnalisé pour réussir le TCF Canada.'
        })
    
    def _generate_reset_email_html(self, user_data: dict, reset_token: str) -> str:
        """
        Génère le contenu HTML de l'email de réinitialisation de mot de passe
        """
        # Déterminer le nom d'affichage
        display_name = f"{user_data.get('prenom', '')} {user_data.get('nom', '')}".strip()
        if not display_name:
            display_name = user_data.get('username', 'Cher utilisateur')
        
        # URL de réinitialisation
        reset_url = f"https://expressiontcf.com/reset-password?token={reset_token}"
        
        html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Réinitialisation de mot de passe - Expression TCF</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8fafc;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px 30px;
        }
        
        .reset-message {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .reset-message h2 {
            color: #2d3748;
            font-size: 24px;
            margin-bottom: 15px;
        }
        
        .reset-message p {
            color: #718096;
            font-size: 16px;
            margin-bottom: 15px;
        }
        
        .reset-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 40px;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 16px;
            text-align: center;
            margin: 30px 0;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .reset-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
        
        .security-info {
            background-color: #fff5f5;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            border-left: 4px solid #f56565;
        }
        
        .security-info h4 {
            color: #c53030;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .security-info p {
            color: #742a2a;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .expiry-info {
            background-color: #f0fff4;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #48bb78;
            text-align: center;
        }
        
        .expiry-info h4 {
            color: #2f855a;
            margin-bottom: 10px;
        }
        
        .expiry-time {
            font-size: 18px;
            font-weight: 700;
            color: #2f855a;
        }
        
        .footer {
            background-color: #2d3748;
            color: #a0aec0;
            padding: 30px;
            text-align: center;
        }
        
        .footer p {
            margin-bottom: 10px;
        }
        
        .manual-link {
            background-color: #edf2f7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            word-break: break-all;
            font-family: monospace;
            font-size: 12px;
            color: #4a5568;
        }
        
        @media (max-width: 600px) {
            .container {
                margin: 10px;
                border-radius: 8px;
            }
            
            .header, .content {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 24px;
            }
            
            .reset-button {
                padding: 15px 30px;
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Expression TCF</h1>
            <p>Réinitialisation de mot de passe</p>
        </div>
        
        <div class="content">
            <div class="reset-message">
                <h2>Bonjour {{ display_name }}! 👋</h2>
                <p>Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte Expression TCF.</p>
                <p>Si vous êtes à l'origine de cette demande, cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
            </div>
            
            <div style="text-align: center;">
                <a href="{{ reset_url }}" class="reset-button">
                    🔑 Réinitialiser mon mot de passe
                </a>
            </div>
            
            <div class="expiry-info">
                <h4>⏰ Validité du lien</h4>
                <div class="expiry-time">1 heure</div>
                <p>Ce lien expirera automatiquement dans 1 heure pour votre sécurité.</p>
            </div>
            
            <div class="security-info">
                <h4>🛡️ Informations de sécurité importantes</h4>
                <p>• Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</p>
                <p>• Ne partagez jamais ce lien avec personne</p>
                <p>• Le lien ne peut être utilisé qu'une seule fois</p>
                <p>• Votre mot de passe actuel reste inchangé tant que vous n'en créez pas un nouveau</p>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background-color: #f7fafc; border-radius: 8px;">
                <h4 style="color: #2d3748; margin-bottom: 15px;">🔗 Lien alternatif</h4>
                <p style="color: #4a5568; font-size: 14px; margin-bottom: 10px;">Si le bouton ne fonctionne pas, copiez et collez ce lien dans votre navigateur :</p>
                <div class="manual-link">{{ reset_url }}</div>
            </div>
            
            <div style="margin-top: 30px; text-align: center; padding: 20px; background-color: #edf2f7; border-radius: 8px;">
                <p style="color: #4a5568; font-size: 14px;">Si vous rencontrez un problème avec votre connexion, n'hésitez pas à nous contacter à l'adresse <strong>info@reussir-tcfcanada.com</strong></p>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Expression TCF</strong> - Votre succès au TCF Canada</p>
            <p>📧 info@reussir-tcfcanada.com | 🌐 www.expressiontcf.com</p>
            <p style="margin-top: 20px; font-size: 12px; opacity: 0.7;">
                © 2024 Expression TCF. Tous droits réservés.
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        return template.render(
            display_name=display_name,
            reset_url=reset_url,
            user_data=user_data
        )
    
    def _generate_reset_email_text(self, user_data: dict, reset_token: str) -> str:
        """
        Génère le contenu texte de l'email de réinitialisation de mot de passe
        """
        display_name = f"{user_data.get('prenom', '')} {user_data.get('nom', '')}".strip()
        if not display_name:
            display_name = user_data.get('username', 'Cher utilisateur')
        
        reset_url = f"https://expressiontcf.com/reset-password?token={reset_token}"
        
        return f"""
Bonjour {display_name},

Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte Expression TCF.

Si vous êtes à l'origine de cette demande, cliquez sur le lien suivant pour créer un nouveau mot de passe :

{reset_url}

Ce lien expirera dans 1 heure pour votre sécurité.

Informations importantes :
• Si vous n'avez pas demandé cette réinitialisation, ignorez cet email
• Ne partagez jamais ce lien avec personne
• Le lien ne peut être utilisé qu'une seule fois
• Votre mot de passe actuel reste inchangé tant que vous n'en créez pas un nouveau

Si vous rencontrez un problème avec votre connexion, n'hésitez pas à nous contacter à l'adresse info@reussir-tcfcanada.com

Cordialement,
L'équipe Expression TCF
        """

# Instance globale du service email
email_service = EmailService()