FROM python:3.9-slim-bullseye@sha256:75a1b8c0d5fb3f1f95e5d49b01c27c89d3669ae91e8b1f7a0b8d59f1a5f3e4f

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le fichier de configuration par défaut
COPY .env.docker .env

# Copier le code source
COPY . .

# Créer le dossier pour les bases de données SQLite
RUN mkdir -p /app/data

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 5001

# Commande pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "app:application"]