#!/bin/bash

# Configuration SSH
echo "=== Configuration SSH ==="

# Installation d'OpenSSH si nécessaire
apt-get update && apt-get install -y openssh-server

# Configuration de SSH
sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
# Ajouter l'écoute sur le port 23 en plus du 22
grep -q '^Port 23' /etc/ssh/sshd_config || echo 'Port 23' >> /etc/ssh/sshd_config

# Préparer l'environnement pour sshd
mkdir -p /var/run/sshd
# Générer les clés hôte si absentes
ssh-keygen -A || true

# Création de l'utilisateur SSH
SSH_PASSWORD=${SSH_PASSWORD:-admin123}
useradd -m -s /bin/bash sshuser || true
echo "sshuser:$SSH_PASSWORD" | chpasswd

# Démarrage du service SSH (avec repli si le service échoue)
service ssh start || (
  echo "Le service ssh n'a pas démarré, lancement direct de sshd...";
  /usr/sbin/sshd -D &
)

echo "Utilisateur: sshuser"
echo "Mot de passe: $SSH_PASSWORD"
echo "Ports: 22, 23"
echo "========================="

# Lancement de l'application Flask
echo "Démarrage de l'application Flask..."
python app.py