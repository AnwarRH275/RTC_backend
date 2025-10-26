-- Script d'initialisation MySQL pour TCF Canada
-- Ce script est exécuté automatiquement lors du premier démarrage de MySQL

-- Créer la base de données si elle n'existe pas
CREATE DATABASE IF NOT EXISTS admin_tcf_canada_STZ CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Utiliser la base de données
USE admin_tcf_canada_STZ;

-- Créer l'utilisateur s'il n'existe pas
CREATE USER IF NOT EXISTS 'admin_tcf_canada_STZ'@'%' IDENTIFIED BY 'admin_tcf_canada_STZ';

-- Accorder tous les privilèges sur la base de données
GRANT ALL PRIVILEGES ON admin_tcf_canada_STZ.* TO 'admin_tcf_canada_STZ'@'%';

-- Appliquer les changements
FLUSH PRIVILEGES;

-- Afficher un message de confirmation
SELECT 'Base de données TCF Canada initialisée avec succès!' as message;