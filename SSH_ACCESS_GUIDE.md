# Guide d'Accès SSH au Container Docker

## Configuration

### 1. Lancement du container avec SSH

```bash
# Utiliser le fichier docker-compose avec SSH
docker-compose -f docker-compose.ssh.yml up -d

# Ou construire et lancer
docker build -f Dockerfile.dev.ssh -t tcf-backend-ssh .
docker run -d -p 5001:5001 -p 2222:22 -e SSH_PASSWORD=your_secure_password tcf-backend-ssh
```

### 2. Connexion SSH

```bash
# Connexion avec l'utilisateur sshuser
ssh sshuser@localhost -p 2222

# Mot de passe: admin123 (ou celui défini dans SSH_PASSWORD)
```

### 3. Accès root (si nécessaire)

```bash
# Une fois connecté en tant que sshuser
sudo su
# Mot de passe: même que sshuser
```

### 4. Commandes utiles dans le container

```bash
# Vérifier que Flask tourne
curl http://localhost:5001/

# Voir les logs
tail -f /app/logs/app.log

# Vérifier les processus
ps aux

# Explorer l'application
cd /app
ls -la
```

### 5. Sécurité

**IMPORTANT**: Changez le mot de passe par défaut !

```bash
# Dans le fichier .env ou docker-compose.ssh.yml
SSH_PASSWORD=votre_mot_de_passe_securise
```

### 6. Arrêt du container

```bash
docker-compose -f docker-compose.ssh.yml down
```

## Variables d'environnement

- `SSH_PASSWORD`: Mot de passe pour l'utilisateur sshuser (défaut: admin123)
- `FLASK_ENV`: Mode Flask (production/développement)
- `DATABASE_URL`: Connexion MySQL

## Ports exposés

- `5001`: Application Flask
- `2222`: SSH (utilisateur: sshuser)