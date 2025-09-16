# Guide de déploiement - Backend TCF Canada

## Construction de l'image Docker

### 1. Construction locale de l'image
```bash
# Se placer dans le dossier backend
cd /Users/user/Documents/reussir-tcfcanada/backend

# Construire l'image Docker
docker build -t tcf-backend:latest .

# Optionnel : Pousser vers Docker Hub
docker tag tcf-backend:latest your-dockerhub-username/tcf-backend:latest
docker push your-dockerhub-username/tcf-backend:latest
```

### 2. Sauvegarder l'image pour Plesk
```bash
# Sauvegarder l'image en fichier .tar
docker save tcf-backend:latest > tcf-backend.tar
```

## Configuration Plesk Amazon

### 1. Préparation du serveur
1. Connectez-vous à votre instance Amazon EC2 via SSH
2. Installez Docker si ce n'est pas déjà fait :
```bash
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
```

### 2. Importation de l'image
```bash
# Transférer le fichier .tar vers le serveur
scp tcf-backend.tar ec2-user@your-server-ip:/home/ec2-user/

# Sur le serveur, charger l'image
docker load < tcf-backend.tar
```

### 3. Configuration via Plesk

#### A. Créer un sous-domaine
1. Dans Plesk, allez dans "Websites & Domains"
2. Cliquez sur "Add Subdomain"
3. Créez : `api.yourdomain.com`

#### B. Configuration du reverse proxy
1. Allez dans "Apache & nginx Settings" pour votre sous-domaine
2. Activez "Proxy mode"
3. Configurez le reverse proxy :
   - Proxy mode : ON
   - Proxy pass : `http://localhost:5001`
   - Proxy pass reverse : `http://localhost:5001`

#### C. Configuration SSL/HTTPS
1. Dans Plesk, allez dans "SSL/TLS Certificates"
2. Obtenez un certificat Let's Encrypt gratuit :
   - Allez dans "Let's Encrypt"
   - Sélectionnez le sous-domaine
   - Cochez "Include www subdomain"
   - Cliquez sur "Get it free"

### 4. Configuration Docker avec volumes persistants

#### A. Créer les dossiers nécessaires
```bash
sudo mkdir -p /opt/tcf/data
sudo mkdir -p /opt/tcf/audio_responses
sudo chown -R 1000:1000 /opt/tcf
```

#### B. Lancer le conteneur
```bash
# Créer le fichier .env
sudo nano /opt/tcf/.env

# Contenu du fichier .env :
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=sqlite:///app/data/prod.db
STRIPE_MODE=live
STRIPE_LIVE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_LIVE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Lancer le conteneur
docker run -d \
  --name tcf-backend \
  --restart unless-stopped \
  -p 127.0.0.1:5001:5001 \
  -v /opt/tcf/data:/app/data \
  -v /opt/tcf/audio_responses:/app/audio_responses \
  --env-file /opt/tcf/.env \
  tcf-backend:latest
```

### 5. Vérification du déploiement

#### A. Vérifier que le conteneur tourne
```bash
docker ps
docker logs tcf-backend
```

#### B. Test de l'API
```bash
# Test local
curl http://localhost:5001/

# Test via HTTPS
curl https://api.yourdomain.com/
```

## Configuration DNS

### 1. Configuration DNS Route 53 (Amazon)
1. Connectez-vous à AWS Route 53
2. Créez ou modifiez une zone hébergée pour votre domaine
3. Ajoutez un enregistrement A :
   - Name : api.yourdomain.com
   - Type : A
   - Value : IP de votre instance EC2
   - TTL : 300

### 2. Configuration du nom de domaine
Assurez-vous que votre domaine pointe vers les serveurs DNS d'Amazon ou configurez les enregistrements appropriés.

## Maintenance et monitoring

### 1. Logs et monitoring
```bash
# Voir les logs en temps réel
docker logs -f tcf-backend

# Voir les métriques du conteneur
docker stats tcf-backend
```

### 2. Mise à jour de l'application
```bash
# Arrêter l'ancien conteneur
docker stop tcf-backend
docker rm tcf-backend

# Charger la nouvelle image
docker load < tcf-backend-new.tar

# Relancer avec la nouvelle image
docker run -d --name tcf-backend --restart unless-stopped -p 127.0.0.1:5001:5001 -v /opt/tcf/data:/app/data -v /opt/tcf/audio_responses:/app/audio_responses --env-file /opt/tcf/.env tcf-backend:latest
```

### 3. Sauvegardes automatiques
```bash
# Créer un script de sauvegarde
sudo nano /opt/tcf/backup.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec tcf-backend sqlite3 /app/data/prod.db ".backup /app/data/backup_$DATE.db"

# Rendre exécutable et ajouter aux crontab
sudo chmod +x /opt/tcf/backup.sh
echo "0 2 * * * /opt/tcf/backup.sh" | sudo crontab -
```

## Sécurité

### 1. Firewall et sécurité réseau
```bash
# Configurer le firewall (si UFW est installé)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Mise à jour régulière
```bash
# Mettre à jour Docker et le système
sudo yum update -y
sudo docker pull tcf-backend:latest
```

## Support et dépannage

### Problèmes courants :
1. **Port déjà utilisé** : Vérifiez qu'aucun autre service n'utilise le port 5001
2. **Permissions des fichiers** : Assurez-vous que Docker peut écrire dans les volumes montés
3. **Variables d'environnement manquantes** : Vérifiez que toutes les variables sont définies dans le fichier .env

Pour toute assistance, consultez les logs Docker : `docker logs tcf-backend`