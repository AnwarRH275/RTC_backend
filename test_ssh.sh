#!/bin/bash

# Script de test d'accès SSH au container Docker

echo "=== Test d'accès SSH au container TCF Backend ==="
echo

# Vérifier si le container tourne
if docker ps | grep -q "tcf-backend-ssh"; then
    echo "✅ Container tcf-backend-ssh est en cours d'exécution"
else
    echo "❌ Container tcf-backend-ssh n'est pas en cours d'exécution"
    echo "Lancez: docker-compose -f docker-compose.ssh.yml up -d"
    exit 1
fi

echo
echo "Informations de connexion:"
echo "  - Hôte: localhost"
echo "  - Port: 2222"
echo "  - Utilisateur: sshuser"
echo "  - Mot de passe: $(docker exec tcf-backend-ssh printenv SSH_PASSWORD 2>/dev/null || echo 'admin123')"
echo
echo "Commande de connexion:"
echo "  ssh sshuser@localhost -p 2222"
echo
echo "Test de connexion (5 secondes):"
timeout 5 ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no sshuser@localhost -p 2222 "echo '✅ Connexion SSH réussie!'" 2>/dev/null || echo "⚠️ Connexion SSH non testée (timeout ou clé non acceptée)"
echo
echo "=== Fin du test ==="