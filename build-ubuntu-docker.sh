#!/bin/bash

# Script de build pour l'image Docker Ubuntu avec migration automatique
set -e

echo "=== Build de l'image Docker Ubuntu avec migration automatique ==="

# Variables
IMAGE_NAME="reussir-tcf-backend-ubuntu"
TAG="latest"
DOCKERFILE="Dockerfile.ubuntu"

# Vérifier que les fichiers nécessaires existent
echo "Vérification des fichiers requis..."

if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ ERREUR: $DOCKERFILE non trouvé!"
    exit 1
fi

if [ ! -f "dev.db" ]; then
    echo "❌ ERREUR: dev.db non trouvé! Ce fichier est requis pour la migration."
    exit 1
fi

if [ ! -f "migrate_sqlite_to_mariadb.py" ]; then
    echo "❌ ERREUR: migrate_sqlite_to_mariadb.py non trouvé!"
    exit 1
fi

if [ ! -f "start-ubuntu.sh" ]; then
    echo "❌ ERREUR: start-ubuntu.sh non trouvé!"
    exit 1
fi

echo "✅ Tous les fichiers requis sont présents"

# Afficher les informations sur dev.db
echo "📊 Informations sur dev.db:"
echo "  - Taille: $(du -h dev.db | cut -f1)"
echo "  - Dernière modification: $(stat -f "%Sm" dev.db)"

# Build de l'image Docker
echo "🔨 Construction de l'image Docker..."
echo "  - Image: $IMAGE_NAME:$TAG"
echo "  - Dockerfile: $DOCKERFILE"
echo "  - Plateforme: linux/amd64"

docker build \
    --platform linux/amd64 \
    -f "$DOCKERFILE" \
    -t "$IMAGE_NAME:$TAG" \
    .

if [ $? -eq 0 ]; then
    echo "✅ Image construite avec succès!"
    
    # Afficher les informations sur l'image
    echo "📋 Informations sur l'image:"
    docker images "$IMAGE_NAME:$TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Optionnel: Sauvegarder l'image en tar
    read -p "Voulez-vous sauvegarder l'image en fichier tar? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        TAR_FILE="${IMAGE_NAME}-$(date +%Y%m%d-%H%M%S).tar"
        echo "💾 Sauvegarde de l'image en $TAR_FILE..."
        docker save "$IMAGE_NAME:$TAG" -o "$TAR_FILE"
        echo "✅ Image sauvegardée: $TAR_FILE ($(du -h "$TAR_FILE" | cut -f1))"
    fi
    
    echo ""
    echo "🚀 Pour tester l'image localement:"
    echo "docker run -p 5001:5001 -e DATABASE_URL='mysql://user:password@host:3306/database' $IMAGE_NAME:$TAG"
    echo ""
    echo "📝 N'oubliez pas de configurer DATABASE_URL avec vos paramètres MariaDB!"
    
else
    echo "❌ Erreur lors de la construction de l'image"
    exit 1
fi