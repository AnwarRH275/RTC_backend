# 📧 Service d'Email - Expression TCF

Ce module gère l'envoi d'emails automatiques pour l'application Expression TCF, notamment les emails de bienvenue lors de l'inscription des utilisateurs.

## 🚀 Fonctionnalités

- ✅ Envoi d'emails de bienvenue avec design moderne et responsive
- ✅ Templates HTML personnalisés avec informations utilisateur
- ✅ Support des plans d'abonnement avec descriptions dynamiques
- ✅ Configuration SMTP sécurisée
- ✅ Gestion d'erreurs robuste
- ✅ Logging détaillé pour le debugging

## 📁 Structure

```
services/email/
├── __init__.py
├── email_service.py    # Service principal d'envoi d'emails
└── README.md          # Cette documentation
```

## 🔧 Configuration

### Variables d'environnement

Ajoutez ces variables dans votre fichier `.env` :

```env
# Configuration SMTP
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
SMTP_USERNAME=support@reussir-tcfcanada.com
SMTP_PASSWORD=votre_mot_de_passe_smtp
FROM_EMAIL=support@reussir-tcfcanada.com
FROM_NAME=Réussir TCF Canada
```

### Paramètres SMTP recommandés

Pour `smtp.hostinger.com` :
- **Serveur SMTP** : `smtp.hostinger.com`
- **Port** : `465` (SSL/TLS)
- **Sécurité** : SSL/TLS
- **Authentification** : Requise

## 📧 Types d'emails

### Email de bienvenue

Envoyé automatiquement lors de la création d'un compte utilisateur.

**Contenu inclus :**
- Message de bienvenue personnalisé
- Informations sur le plan d'abonnement choisi
- Solde de crédits disponibles
- Liste des fonctionnalités accessibles
- Liens vers le tableau de bord
- Informations de contact

**Design :**
- Template HTML responsive
- Dégradés modernes
- Couleurs cohérentes avec l'identité visuelle
- Compatible mobile et desktop

## 🛠️ Utilisation

### Import du service

```python
from services.email.email_service import email_service
```

### Envoi d'un email de bienvenue

```python
user_data = {
    'username': 'john_doe',
    'email': 'john@example.com',
    'nom': 'Doe',
    'prenom': 'John',
    'subscription_plan': 'premium',
    'sold': 150.0
}

success = email_service.send_welcome_email(user_data)
if success:
    print("Email envoyé avec succès!")
else:
    print("Échec de l'envoi")
```

### Envoi d'un email personnalisé

```python
success = email_service.send_email(
    to_email="user@example.com",
    subject="Sujet de l'email",
    html_content="<h1>Contenu HTML</h1>",
    text_content="Contenu texte alternatif"
)
```

## 🧪 Tests

### Script de test

Utilisez le script de test fourni :

```bash
cd backend
python test_email.py
```

Ce script :
- Teste la connexion SMTP
- Envoie un email de test
- Affiche la configuration actuelle
- Fournit des conseils de dépannage

### Test manuel

```python
from services.email.email_service import email_service

# Données de test
test_user = {
    'username': 'test_user',
    'email': 'votre-email@example.com',
    'nom': 'Test',
    'prenom': 'Utilisateur',
    'subscription_plan': 'premium',
    'sold': 100.0
}

# Envoi de l'email de test
result = email_service.send_welcome_email(test_user)
print(f"Résultat: {result}")
```

## 🎨 Personnalisation

### Plans d'abonnement

Les plans sont définis dans `_get_plan_info()` :

```python
plans = {
    'basic': {
        'name': '🥉 Plan Basic',
        'description': 'Accès aux fonctionnalités essentielles...'
    },
    'premium': {
        'name': '🥈 Plan Premium', 
        'description': 'Accès complet avec corrections avancées...'
    },
    # ... autres plans
}
```

### Template HTML

Le template est dans `_generate_welcome_email_html()`. Vous pouvez :
- Modifier les couleurs et styles CSS
- Ajouter de nouveaux éléments
- Personnaliser le contenu
- Adapter le responsive design

## 🔍 Debugging

### Logs

Les logs sont configurés automatiquement :

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Messages de log typiques

- `Email envoyé avec succès à user@example.com`
- `Échec de l'envoi de l'email à user@example.com`
- `Erreur lors de l'envoi de l'email de bienvenue: [détails]`

### Problèmes courants

1. **Connexion SMTP échoue**
   - Vérifiez les paramètres SMTP
   - Testez les identifiants
   - Vérifiez les ports et la sécurité

2. **Email non reçu**
   - Vérifiez les spams
   - Validez l'adresse email
   - Contrôlez les logs serveur

3. **Template cassé**
   - Vérifiez la syntaxe Jinja2
   - Validez le HTML
   - Testez avec des données simples

## 🔒 Sécurité

- ✅ Mots de passe SMTP stockés dans variables d'environnement
- ✅ Connexions SSL/TLS sécurisées
- ✅ Validation des données utilisateur
- ✅ Gestion d'erreurs sans exposition d'informations sensibles
- ✅ Logs sécurisés (pas de mots de passe)

## 📈 Performance

- Connexions SMTP réutilisées dans le même contexte
- Templates compilés une seule fois
- Gestion d'erreurs non-bloquante pour l'inscription
- Timeouts configurés pour éviter les blocages

## 🚀 Déploiement

### Production

1. Configurez les vraies variables SMTP
2. Activez les logs en production
3. Testez avec de vrais emails
4. Surveillez les métriques d'envoi

### Variables d'environnement production

```env
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
SMTP_USERNAME=support@reussir-tcfcanada.com
SMTP_PASSWORD=mot_de_passe_production_securise
FROM_EMAIL=support@reussir-tcfcanada.com
FROM_NAME=Réussir TCF Canada
```

## 📞 Support

Pour toute question ou problème :
- 📧 Email : contact@expressiontcf.com
- 📝 Documentation : Ce README
- 🧪 Tests : `python test_email.py`

---

*Développé avec ❤️ pour Expression TCF*