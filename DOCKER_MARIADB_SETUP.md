# Configuration Backend avec MariaDB via Docker

Ce guide explique comment connecter le backend à la base de données MariaDB configurée via Docker.

## Configuration actuelle

### Base de données MariaDB
- **Hôte**: localhost
- **Port**: 3306
- **Utilisateur**: tcf_canada_STZ
- **Mot de passe**: STZue3jm#4s3ttl#
- **Base de données**: admin_tcf_canada_STZ

### Fichiers modifiés

1. **config.py**: Configuration DevConfig mise à jour pour utiliser MariaDB
2. **requirements.txt**: Ajout de PyMySQL pour la connexion MySQL
3. **.env.docker**: Configuration Docker mise à jour avec MariaDB

## Instructions d'installation

### 1. Démarrer les conteneurs Docker
```bash
cd ../DB
docker-compose up -d
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer l'environnement

#### Option A: Utiliser la configuration Docker
```bash
cp .env.docker .env
```

#### Option B: Modifier directement .env
Ajoutez la variable DATABASE_URL:
```bash
DATABASE_URL=mysql+pymysql://tcf_canada_STZ:STZue3jm#4s3ttl#@localhost:3306/admin_tcf_canada_STZ
```

### 4. Initialiser la base de données
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Lancer le serveur
```bash
python app.py
```

## Accès phpMyAdmin

- **URL**: http://localhost:8080
- **Serveur**: db
- **Utilisateur**: root
- **Mot de passe**: STZue3jm#4s3ttl#

## Configuration alternative (SQLite)

Pour revenir à la configuration SQLite originale:

1. Dans config.py, décommentez la ligne:
```python
SQLALCHEMY_DATABASE_URI = "sqlite:///"+os.path.join(BASE_DIR, 'dev.db')
```

2. Commentez la ligne MariaDB:
```python
# SQLALCHEMY_DATABASE_URI = "mysql+pymysql://tcf_canada_STZ:STZue3jm#4s3ttl#@localhost:3306/admin_tcf_canada_STZ"
```

## Vérification

Testez la connexion avec:
```python
from app import app
from models.exts import db

with app.app_context():
    db.engine.execute("SELECT 1")
    print("Connexion réussie!")
```