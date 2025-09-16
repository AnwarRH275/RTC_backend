#!/bin/bash

# Script de construction de l'image Docker pour TCF Backend

set -e

echo "🚀 Construction de l'image Docker TCF Backend..."

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
    exit 1
fi

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile non trouvé. Assurez-vous d'être dans le répertoire backend."
    exit 1
fi

# Nom de l'image
IMAGE_NAME="tcf-backend"
TAG="latest"

# Construire l'image
echo "📦 Construction de l'image Docker..."
docker build -t ${IMAGE_NAME}:${TAG} .

# Vérifier que l'image a été construite
if ! docker image inspect ${IMAGE_NAME}:${TAG} > /dev/null 2>&1; then
    echo "❌ Erreur lors de la construction de l'image"
    exit 1
fi

# Afficher les informations de l'image
echo "✅ Image construite avec succès!"
echo "📊 Taille de l'image:"
docker images ${IMAGE_NAME}:${TAG} --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"

# Tester l'image localement
echo "🧪 Test de l'image..."
docker run --rm -d --name test-tcf-backend -p 5002:5001 ${IMAGE_NAME}:${TAG}
sleep 5

# Vérifier que le conteneur fonctionne
if docker ps | grep -q test-tcf-backend; then
    echo "✅ Conteneur de test démarré avec succès"
    echo "🌐 Testez l'API: http://localhost:5002"
    
    # Arrêter le conteneur de test
    docker stop test-tcf-backend > /dev/null 2>&1 || true
else
    echo "❌ Le conteneur de test n'a pas démarré correctement"
    echo "📋 Vérifiez les logs: docker logs test-tcf-backend"
fi

# Optionnel : créer une archive
echo "📦 Création de l'archive pour Plesk..."
docker save ${IMAGE_NAME}:${TAG} > ${IMAGE_NAME}.tar

echo "✅ Archive créée: ${IMAGE_NAME}.tar"
echo "📁 Taille de l'archive:"
ls -lh ${IMAGE_NAME}.tar

echo ""
echo "🎯 Instructions pour le déploiement :"
echo "1. Transférez le fichier ${IMAGE_NAME}.tar vers votre serveur Plesk"
echo "2. Sur le serveur: docker load < ${IMAGE_NAME}.tar"
echo "3. Lancez: docker run -d --name tcf-backend -p 5001:5001 -e SECRET_KEY=your-secret-key tcf-backend:latest"
echo "4. Suivez le guide dans DEPLOYMENT.md pour la configuration HTTPS"