# TCF Oral Expression Backend Implementation

## Vue d'ensemble

Cette implémentation étend le backend pour supporter la structure spécifique des tâches orales TCF définies dans le frontend `OralExamModel.js`. Le système crée des tables dédiées et des endpoints API pour chaque type de tâche orale (entretien, questions, expression) afin de stocker leurs champs uniques.

## Structure des Modèles

### 1. TCFOralSubject
Table principale pour les sujets d'expression orale TCF.

```python
class TCFOralSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')
    duration_minutes = db.Column(db.Integer, default=15)
    total_points = db.Column(db.Integer, default=100)
    evaluation_criteria = db.Column(db.Text)
    tasks = db.relationship('TCFOralTask', backref='subject', lazy=True, cascade='all, delete-orphan')
```

### 2. TCFOralTask
Table pour les tâches individuelles (entretien, questions, expression).

```python
class TCFOralTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('tcforal_subject.id'), nullable=False)
    task_type_id = db.Column(db.Integer, db.ForeignKey('tcforal_task_type.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    structure_to_respect = db.Column(db.Text)
    specific_instructions = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    points = db.Column(db.Integer)
    
    # Champs spécifiques pour "questions"
    roleplay_scenario = db.Column(db.Text)
    preparation_time_minutes = db.Column(db.Integer)
```

### 3. TCFOralExampleQuestion
Table pour les questions d'exemple de la tâche "entretien".

```python
class TCFOralExampleQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tcforal_task.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('tcforal_question_category.id'))
```

### 4. TCFOralDebateTopic
Table pour les sujets de débat de la tâche "expression".

```python
class TCFOralDebateTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tcforal_task.id'), nullable=False)
    topic_question = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    difficulty_level_id = db.Column(db.Integer, db.ForeignKey('tcforal_difficulty_level.id'))
```

### 5. Tables de Référence

#### TCFOralTaskType
- entretien
- questions  
- expression

#### TCFOralQuestionCategory
- personnel
- professionnel
- culturel
- loisirs
- projets

#### TCFOralDifficultyLevel
- facile
- moyen
- difficile

## Endpoints API

### Sujets Oraux
- `GET /tcf-oral/subjects` - Liste tous les sujets
- `POST /tcf-oral/subjects` - Crée un nouveau sujet
- `GET /tcf-oral/subjects/{id}` - Récupère un sujet spécifique
- `PUT /tcf-oral/subjects/{id}` - Met à jour un sujet
- `DELETE /tcf-oral/subjects/{id}` - Supprime un sujet

### Tâches
- `GET /tcf-oral/subjects/{subject_id}/tasks` - Liste les tâches d'un sujet
- `POST /tcf-oral/subjects/{subject_id}/tasks` - Crée une nouvelle tâche
- `PUT /tcf-oral/tasks/{id}` - Met à jour une tâche
- `DELETE /tcf-oral/tasks/{id}` - Supprime une tâche

### Questions d'Exemple
- `GET /tcf-oral/tasks/{task_id}/example-questions` - Liste les questions d'exemple
- `POST /tcf-oral/tasks/{task_id}/example-questions` - Ajoute une question d'exemple
- `PUT /tcf-oral/example-questions/{id}` - Met à jour une question
- `DELETE /tcf-oral/example-questions/{id}` - Supprime une question

### Sujets de Débat
- `GET /tcf-oral/tasks/{task_id}/debate-topics` - Liste les sujets de débat
- `POST /tcf-oral/tasks/{task_id}/debate-topics` - Ajoute un sujet de débat
- `PUT /tcf-oral/debate-topics/{id}` - Met à jour un sujet de débat
- `DELETE /tcf-oral/debate-topics/{id}` - Supprime un sujet de débat

### Métadonnées
- `GET /tcf-oral/task-types` - Liste les types de tâches
- `GET /tcf-oral/question-categories` - Liste les catégories de questions
- `GET /tcf-oral/difficulty-levels` - Liste les niveaux de difficulté

## Installation et Configuration

### 1. Créer la Migration
```bash
cd /Users/user/Documents/reussir-tcfcanada/backend
python create_oral_migration.py
```

### 2. Appliquer la Migration
```bash
flask db upgrade
```

### 3. Initialiser les Données de Référence
```bash
python init_oral_metadata.py
```

## Correspondance Frontend-Backend

### Tâche 1: Entretien
- **Frontend**: Questions d'exemple avec texte et catégorie
- **Backend**: Table `TCFOralExampleQuestion` avec `question_text` et `category_id`

### Tâche 2: Questions
- **Frontend**: Scénario de jeu de rôle et temps de préparation
- **Backend**: Champs `roleplay_scenario` et `preparation_time_minutes` dans `TCFOralTask`

### Tâche 3: Expression
- **Frontend**: Sujets de débat avec question, contexte et niveau de difficulté
- **Backend**: Table `TCFOralDebateTopic` avec `topic_question`, `context` et `difficulty_level_id`

## Exemples d'Utilisation

### Créer un Sujet avec Tâches
```python
# Créer le sujet
subject_data = {
    "name": "TCF Oral - Session 1",
    "description": "Premier sujet d'expression orale",
    "duration_minutes": 15,
    "total_points": 100,
    "evaluation_criteria": "<p>Critères d'évaluation...</p>"
}

# Créer les tâches
tasks_data = [
    {
        "task_type_id": 1,  # entretien
        "title": "Entretien dirigé",
        "structure_to_respect": "<p>Structure...</p>",
        "duration_minutes": 5,
        "points": 30
    },
    {
        "task_type_id": 2,  # questions
        "title": "Échange d'informations",
        "roleplay_scenario": "<p>Scénario...</p>",
        "preparation_time_minutes": 2,
        "duration_minutes": 5,
        "points": 35
    },
    {
        "task_type_id": 3,  # expression
        "title": "Expression d'un point de vue",
        "duration_minutes": 5,
        "points": 35
    }
]
```

### Ajouter des Questions d'Exemple
```python
example_questions = [
    {
        "question_text": "Pouvez-vous vous présenter?",
        "category_id": 1  # personnel
    },
    {
        "question_text": "Parlez-moi de votre travail",
        "category_id": 2  # professionnel
    }
]
```

### Ajouter des Sujets de Débat
```python
debate_topics = [
    {
        "topic_question": "Pensez-vous que les réseaux sociaux ont un impact positif sur la société?",
        "context": "Dans le contexte actuel...",
        "difficulty_level_id": 2  # moyen
    }
]
```

## Fichiers Créés

1. **`models/tcf_model_oral.py`** - Définitions des modèles de base de données
2. **`services/crud/tcf_admin_oral.py`** - API endpoints et logique métier
3. **`init_oral_metadata.py`** - Script d'initialisation des données de référence
4. **`create_oral_migration.py`** - Script de génération de migration

## Notes Importantes

- Le namespace `tcf_oral_ns` est déjà enregistré dans `app.py`
- Les modèles utilisent des relations SQLAlchemy pour maintenir l'intégrité référentielle
- Les suppressions en cascade sont configurées pour éviter les données orphelines
- L'API suit les conventions RESTful pour une intégration facile avec le frontend
- Les champs de texte riche (ReactQuill) sont stockés comme TEXT dans la base de données