#!/bin/bash

echo "🔄 Reconstruction de l'image Docker avec --no-cache"
echo "Cela va forcer l'installation d'EdgeTTS 7.2.3"

# Arrêter les conteneurs existants
echo "📦 Arrêt des conteneurs existants..."
docker-compose -f docker-compose.dev.yml down

# Supprimer les images existantes pour forcer la reconstruction
echo "🗑️ Suppression des images existantes..."
docker-compose -f docker-compose.dev.yml down --rmi all

# Nettoyer le cache Docker
echo "🧹 Nettoyage du cache Docker..."
docker system prune -f

# Reconstruire avec --no-cache
echo "🏗️ Reconstruction de l'image avec --no-cache..."
docker-compose -f docker-compose.dev.yml build --no-cache

# Démarrer les services
echo "🚀 Démarrage des services..."
docker-compose -f docker-compose.dev.yml up -d

echo "✅ Reconstruction terminée!"
echo "📋 Vérifiez les logs avec: docker-compose -f docker-compose.dev.yml logs -f"