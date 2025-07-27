# TCF Expression Orale - Documentation Backend

## Vue d'ensemble

Ce module gère la partie backend pour les sujets d'expression orale du TCF (Test de Connaissance du Français). Il comprend des modèles de données spécialisés et des services API pour créer, gérer et récupérer les sujets d'expression orale.

## Structure des fichiers

### Modèles (`models/tcf_model_oral.py`)

#### `TCFOralSubject`
Modèle principal pour les sujets d'expression orale.

**Champs:**
- `id`: Identifiant unique
- `name`: Nom du sujet
- `date`: Date de création (format YYYY-MM-DD)
- `status`: Statut (Actif/Inactif)
- `duration`: Durée totale en minutes
- `subject_type`: Toujours "Oral"
- `description`: Description optionnelle
- `combination`: Combinaison de tâches (optionnel)
- `tasks`: Relation vers les tâches orales

#### `TCFOralTask`
Modèle pour les tâches individuelles d'expression orale.

**Champs communs:**
- `id`: Identifiant unique
- `title`: Titre de la tâche
- `task_type`: Type de tâche (entretien, questions, expression)
- `duration`: Durée en minutes
- `instructions`: Instructions spécifiques
- `evaluation_criteria`: Critères d'évaluation
- `subject_id`: Référence vers le sujet parent

**Champs spécialisés selon le type:**

1. **Entretien (`task_type: "entretien"`):**
   - `example_questions`: Questions d'exemple avec catégories (JSON)

2. **Jeu de rôle (`task_type: "questions"`):**
   - `roleplay_scenario`: Scénario de jeu de rôle
   - `preparation_time`: Temps de préparation en minutes

3. **Expression spontanée (`task_type: "expression"`):**
   - `debate_topics`: Sujets de débat avec contexte et difficulté (JSON)

### Services (`services/tcf_admin_oral.py`)

#### Endpoints disponibles

##### Sujets
- `GET /tcf-oral/subjects` - Récupérer tous les sujets
- `POST /tcf-oral/subjects` - Créer un nouveau sujet
- `GET /tcf-oral/subjects/{id}` - Récupérer un sujet spécifique
- `PUT /tcf-oral/subjects/{id}` - Mettre à jour un sujet
- `DELETE /tcf-oral/subjects/{id}` - Supprimer un sujet

##### Tâches
- `GET /tcf-oral/subjects/{subject_id}/tasks` - Récupérer les tâches d'un sujet
- `POST /tcf-oral/subjects/{subject_id}/tasks` - Ajouter une tâche à un sujet
- `GET /tcf-oral/tasks/{task_id}` - Récupérer une tâche spécifique
- `PUT /tcf-oral/tasks/{task_id}` - Mettre à jour une tâche
- `DELETE /tcf-oral/tasks/{task_id}` - Supprimer une tâche

##### Métadonnées
- `GET /tcf-oral/task-types` - Types de tâches disponibles
- `GET /tcf-oral/categories` - Catégories pour les questions d'entretien
- `GET /tcf-oral/difficulties` - Niveaux de difficulté

## Structure des données JSON

### Questions d'exemple (entretien)
```json
[
  {
    "text": "Quel est votre film préféré ? Pourquoi ?",
    "category": "personnel"
  },
  {
    "text": "Décrivez votre travail actuel",
    "category": "professionnel"
  }
]
```

### Sujets de débat (expression)
```json
[
  {
    "topic": "Faut-il interdire la vente d'alcool aux mineurs ?",
    "context": "Contexte sur les problèmes de santé publique...",
    "difficulty": "moyen"
  }
]
```

## Types de tâches

1. **Entretien dirigé** (`entretien`)
   - Durée: 4 minutes
   - Questions personnelles et professionnelles
   - Catégories: personnel, professionnel, culturel, loisirs, projets

2. **Jeu de rôle** (`questions`)
   - Durée: 4 minutes
   - Poser des questions dans un contexte donné
   - Temps de préparation configurable

3. **Expression spontanée** (`expression`)
   - Durée: 4 minutes
   - Débat et argumentation sur un sujet
   - Niveaux de difficulté: facile, moyen, difficile

## Installation et configuration

1. Les modèles sont automatiquement importés via `models/tcf_model_oral.py`
2. Le service est enregistré dans `application.py`
3. Les endpoints sont disponibles sous le namespace `/tcf-oral`

## Migration de base de données

Après avoir ajouté les nouveaux modèles, exécutez:

```bash
flask db migrate -m "Add TCF Oral models"
flask db upgrade
```

## Utilisation avec le frontend

Le frontend peut utiliser ces endpoints pour:
- Créer et gérer des sujets d'expression orale
- Configurer différents types de tâches
- Récupérer les métadonnées (types, catégories, difficultés)
- Sauvegarder les configurations de modal oral

## Sécurité

Tous les endpoints sont protégés par JWT (si configuré dans l'application principale). Les champs sont optionnels pour permettre une flexibilité maximale dans la création des sujets.