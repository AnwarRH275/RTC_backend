# Système de Permissions des Modérateurs

Ce document décrit l'implémentation du système de permissions pour les modérateurs dans l'application Réussir TCF Canada.

## Vue d'ensemble

Le système de permissions des modérateurs limite l'accès et les actions que peuvent effectuer les utilisateurs avec le rôle "moderator". Les modérateurs ont des permissions restreintes par rapport aux administrateurs.

## Restrictions des Modérateurs

### 1. Accès aux Sections

Les modérateurs n'ont accès qu'aux sections suivantes :
- **Gestion de compte** (`/user-management`)
- **Profil** (`/profile`)

Toutes les autres sections (Coach TCF, Examens, Résultats, Packs, Facturation, etc.) sont réservées aux administrateurs et clients.

### 2. Gestion des Utilisateurs

#### Création d'utilisateurs
- ✅ Les modérateurs peuvent créer de nouveaux utilisateurs
- ❌ Ils ne peuvent créer que des comptes avec le rôle "client"
- ❌ Ils ne peuvent pas créer d'administrateurs ou d'autres modérateurs
- ℹ️ Les utilisateurs créés par un modérateur sont marqués avec `created_by = username_moderateur`

#### Modification d'utilisateurs
- ✅ Les modérateurs peuvent modifier les utilisateurs qu'ils ont créés
- ✅ Les modérateurs peuvent modifier les clients existants (non créés par eux)
- ❌ Ils ne peuvent pas modifier les comptes administrateurs
- ❌ Ils ne peuvent pas modifier les comptes d'autres modérateurs
- ❌ Ils ne peuvent pas modifier les mots de passe des administrateurs
- ❌ Ils ne peuvent pas changer les rôles des utilisateurs

#### Suppression d'utilisateurs
- ✅ Les modérateurs peuvent supprimer les utilisateurs qu'ils ont créés
- ❌ Ils ne peuvent pas supprimer les comptes administrateurs
- ❌ Ils ne peuvent pas supprimer les comptes d'autres modérateurs
- ❌ Ils ne peuvent pas supprimer les clients créés par d'autres modérateurs

#### Gestion des soldes
- ✅ Les modérateurs peuvent modifier les soldes des utilisateurs qu'ils gèrent
- ❌ Ils ne peuvent pas modifier les soldes des administrateurs ou autres modérateurs

### 3. Visualisation des Données

- Les modérateurs ne voient que :
  - Les utilisateurs qu'ils ont créés
  - Les clients existants (pour modification limitée)
- Ils ne voient pas :
  - Les comptes administrateurs
  - Les comptes d'autres modérateurs

## Architecture Technique

### Frontend

#### Fichiers modifiés :
- `frontend/src/routes.js` : Restriction d'accès aux routes
- `frontend/src/layouts/user-management/index.js` : Validation des permissions côté client

#### Fonctionnalités :
- Filtrage des utilisateurs affichés selon les permissions
- Désactivation des boutons d'action non autorisés
- Validation des formulaires selon le rôle

### Backend

#### Nouveaux fichiers :
- `backend/services/moderator_permissions.py` : Service de validation des permissions
- `backend/services/crud/manage.py` : Service CRUD avec validation des permissions
- `backend/migrate_add_created_by.py` : Script de migration de base de données

#### Fichiers modifiés :
- `backend/services/auth/auth.py` : Intégration des validations de permissions
- `backend/models/model.py` : Ajout du champ `created_by`

### Base de Données

#### Nouveau champ :
- `User.created_by` : Stocke le nom d'utilisateur du modérateur qui a créé l'utilisateur

## Installation et Migration

### 1. Migration de la Base de Données

```bash
cd backend
python migrate_add_created_by.py
```

Ce script :
- Ajoute la colonne `created_by` à la table `user`
- Vérifie que la migration s'est bien déroulée
- Ne modifie pas les utilisateurs existants (created_by reste NULL)

### 2. Redémarrage des Services

Après la migration, redémarrez :
- Le serveur backend Flask
- L'application frontend React (si nécessaire)

## Utilisation

### Création d'un Modérateur

1. Connectez-vous en tant qu'administrateur
2. Allez dans "Gestion de compte"
3. Créez un nouvel utilisateur avec le rôle "Moderator"

### Connexion en tant que Modérateur

1. Le modérateur se connecte avec ses identifiants
2. Il n'a accès qu'aux sections "Gestion de compte" et "Profil"
3. Dans "Gestion de compte", il ne voit que les utilisateurs qu'il peut gérer

## Sécurité

### Validation Double

Chaque action est validée :
1. **Frontend** : Interface utilisateur adaptée selon les permissions
2. **Backend** : Validation serveur obligatoire pour toutes les API

### Principe de Moindre Privilège

Les modérateurs ont le minimum de permissions nécessaires :
- Accès limité aux sections
- Actions restreintes sur les utilisateurs
- Pas d'accès aux fonctionnalités administratives sensibles

## Tests

### Scénarios de Test

1. **Accès aux routes** :
   - Vérifier que les modérateurs ne peuvent pas accéder aux routes interdites
   - Tester la redirection automatique

2. **Gestion des utilisateurs** :
   - Créer un utilisateur en tant que modérateur
   - Tenter de modifier un administrateur (doit échouer)
   - Tenter de supprimer un utilisateur non autorisé (doit échouer)

3. **Interface utilisateur** :
   - Vérifier que les boutons non autorisés sont désactivés
   - Tester les messages d'erreur appropriés

### Commandes de Test

```bash
# Test de l'API backend
curl -X GET "http://localhost:5000/auth/users" \
  -H "Authorization: Bearer <moderator_token>"

# Test de création d'utilisateur
curl -X POST "http://localhost:5000/auth/signup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <moderator_token>" \
  -d '{"username":"test","email":"test@test.com","password":"password","role":"client"}'
```

## Dépannage

### Problèmes Courants

1. **Erreur de migration** :
   - Vérifier que la base de données est accessible
   - S'assurer que l'application n'est pas en cours d'exécution

2. **Permissions non appliquées** :
   - Vérifier que le token JWT contient le bon rôle
   - Redémarrer le serveur backend

3. **Interface non mise à jour** :
   - Vider le cache du navigateur
   - Redémarrer l'application frontend

### Logs

Les actions des modérateurs sont loggées dans :
- Console du serveur Flask
- Fichiers de logs de l'application (si configurés)

## Maintenance

### Ajout de Nouvelles Restrictions

1. Modifier `moderator_permissions.py`
2. Mettre à jour les validations frontend
3. Ajouter les tests correspondants
4. Mettre à jour cette documentation

### Surveillance

Surveiller régulièrement :
- Les tentatives d'accès non autorisées
- Les erreurs de permissions dans les logs
- L'utilisation des fonctionnalités par les modérateurs