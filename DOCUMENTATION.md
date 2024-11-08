# Parallagon Documentation

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend development)
- API keys for Anthropic and OpenAI
- portalocker (for thread-safe file locking)
- Redis (optional, for distributed caching)
- Aider CLI tool installed and configured

### System Requirements
- 4GB RAM minimum
- 2 CPU cores minimum
- 1GB free disk space
- Network access for API calls

### Environment Variables
Required in `.env`:
```
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Server Configuration
DEBUG=True/False
PORT=8000
HOST=0.0.0.0

# File Operations
FILE_LOCK_TIMEOUT=10
MAX_FILE_SIZE=10485760
LOCK_CHECK_INTERVAL=100

# Cache Settings
CACHE_DURATION=3600
CACHE_CLEANUP_INTERVAL=300
CONTENT_CACHE_SIZE=1000

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
ERROR_RETRY_CODES=[408,429,500,502,503,504]

# Notifications
NOTIFICATION_QUEUE_SIZE=500
NOTIFICATION_BATCH_SIZE=50

# Logging
LOG_LEVEL=info
```

### Core Components

#### BaseService
Base class providing common functionality for all services:
- Error handling with retry policies
- Input validation
- Standardized logging
- Thread-safe file operations
- Caching with invalidation
- Performance metrics

#### File Locking System
Uses portalocker for thread-safe file operations:
- Configurable timeouts
- Automatic retry on failure
- Lock cleanup
- Deadlock prevention
- File access coordination

#### Cache System
Multi-level caching strategy:
- Memory cache with LRU eviction
- File content caching
- Prompt caching per agent
- Cache invalidation on file changes
- Configurable cleanup intervals

#### Error Handling
Centralized error management:
- Custom exception hierarchy
- Automatic retries with @safe_operation
- Detailed error logging
- Error aggregation and reporting
- Circuit breaker pattern

### API Routes

#### Agent Routes
- GET `/api/agents/status` - Get status of all agents
- POST `/api/agents/start` - Start all agents
- POST `/api/agents/stop` - Stop all agents
- GET `/api/agent/<id>/prompt` - Get agent prompt
- POST `/api/agent/<id>/prompt` - Update agent prompt
- POST `/api/agent/<id>/<action>` - Control individual agent

#### Mission Routes
- GET `/api/missions` - List all missions
- POST `/api/missions` - Create new mission
- GET `/api/missions/<id>` - Get mission details
- GET `/api/missions/<id>/content` - Get mission content
- POST `/api/missions/<id>/reset` - Reset mission files
- POST `/api/missions/<id>/test-data` - Load test data

#### Notification Routes
- GET `/api/notifications` - Get pending notifications
- POST `/api/notifications` - Send notification
- GET `/api/changes` - Get content changes

### Agents

#### DuplicationAgent
Agent spécialisé dans la détection et réduction de la duplication de code.

#### Fonctionnalités
- Analyse statique du code source via AST
- Détection des fonctions similaires
- Identification des configurations redondantes
- Analyse des duplications de documentation
- Calcul des métriques de complexité

#### Configuration
```python
{
    "name": "Duplication",
    "prompt_file": "prompts/duplication.md",
    "check_interval": 300,  # 5 minutes
    "file_patterns": ["*.py", "*.js", "*.md"]
}
```

#### Prompt
Le prompt de l'agent est configuré dans `prompts/duplication.md` et définit :
- Objectifs d'analyse
- Instructions spécifiques
- Format des rapports
- Critères d'évaluation

### Routes API

#### Notifications
- GET `/api/notifications`
  - Récupère les notifications en attente
  - Retourne un tableau de notifications avec timestamps
  - Support du filtrage par type et priorité

- POST `/api/notifications`
  - Envoie une nouvelle notification
  - Corps de requête :
    ```json
    {
        "type": "info|warning|error",
        "message": "Message content",
        "panel": "Panel name",
        "flash": true|false
    }
    ```

#### Missions
- POST `/api/missions/<id>/reset`
  - Réinitialise les fichiers d'une mission
  - Préserve le fichier demande.md
  - Recrée les autres fichiers avec contenu initial

### Décorateurs

#### @safe_operation
Décorateur pour sécuriser les opérations avec retry automatique.

```python
@safe_operation(max_retries=3, delay=1.0)
def some_operation():
    # Code protégé ici
    pass
```

Paramètres :
- max_retries : Nombre maximum de tentatives (défaut: 3)
- delay : Délai entre les tentatives en secondes (défaut: 1.0)

Fonctionnalités :
- Retry automatique sur exception
- Délai exponentiel entre les tentatives
- Logging des retries et erreurs
- Nettoyage des ressources
- Propagation de la dernière erreur

### Système de Cache

#### Cache de Contenu
- Cache LRU en mémoire pour les fichiers
- Invalidation basée sur les timestamps
- Configuration via variables d'environnement :
  ```
  CACHE_DURATION=3600
  CACHE_CLEANUP_INTERVAL=300
  CONTENT_CACHE_SIZE=1000
  ```

#### Cache des Prompts
- Cache par agent avec _prompt_cache
- Invalidation automatique sur modification
- Préchargement intelligent

### Development Guide

#### Adding New Agent
1. Create agent class inheriting from AiderAgent
2. Implement required methods:
   - _build_prompt()
   - _run_aider()
   - list_files()
3. Configure:
   - Prompt file
   - Watch files
   - Execution intervals
4. Register in AgentService

#### Creating New Service
1. Create service class inheriting from BaseService
2. Implement standard methods:
   - _validate_input()
   - _handle_error()
   - _log_operation()
3. Add:
   - Custom error handling
   - Input validation
   - Specialized logging
   - Cache if needed

#### Best Practices
1. Error Handling:
   - Use custom exceptions
   - Implement retries
   - Log errors properly
   - Clean up resources

2. File Operations:
   - Use portalocker
   - Handle timeouts
   - Implement retries
   - Validate paths

3. Cache Management:
   - Use LRU cache
   - Set TTL values
   - Handle invalidation
   - Monitor usage

4. Testing:
   - Unit tests
   - Integration tests
   - Performance tests
   - Error scenarios

### System Requirements
- 4GB RAM minimum
- 2 CPU cores minimum
- 1GB free disk space
- Network access for API calls

### Environment Variables
Required in `.env`:
```
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Server Configuration
DEBUG=True/False
PORT=8000
HOST=0.0.0.0

# File Operations
FILE_LOCK_TIMEOUT=10
MAX_FILE_SIZE=10485760
LOCK_CHECK_INTERVAL=100

# Cache Settings
CACHE_DURATION=3600
CACHE_CLEANUP_INTERVAL=300
CONTENT_CACHE_SIZE=1000

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
ERROR_RETRY_CODES=[408,429,500,502,503,504]

# Notifications
NOTIFICATION_QUEUE_SIZE=500
NOTIFICATION_BATCH_SIZE=50

# Logging
LOG_LEVEL=info
```

### Installation
1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure API keys
5. Run `python parallagon_web.py`

## User Guide

### 1. Core Application
- `parallagon_web.py`
  - Point d'entrée principal de l'application
  - Configuration Flask et middleware
  - Initialisation des services
  - Gestion des routes et erreurs

### 2. Agents
- `aider_agent.py`
  - Framework de base pour les agents autonomes
  - Intégration avec l'outil Aider
  - Gestion des prompts avec cache et invalidation
    * Cache LRU configurable via CACHE_DURATION
    * Invalidation basée sur les timestamps
    * Préchargement intelligent avec _load_prompt()
    * Cache par agent avec _prompt_cache
  - Surveillance des fichiers avec portalocker
    * Verrouillage thread-safe via Lock class
    * Timeouts configurables via FILE_LOCK_TIMEOUT
    * Retry automatique avec @safe_operation
    * Nettoyage des verrous via context manager
  - Gestion des chemins de fichiers
    * Résolution des chemins absolus
    * Validation des chemins via _validate_file_path
    * Création automatique des dossiers manquants
    * Support des liens symboliques
  - Exécution sécurisée des commandes
    * Validation des entrées
    * Capture des erreurs stdout/stderr
    * Timeouts configurables
    * Retry sur échec avec délai exponentiel
  - Notifications temps réel
    * Envoi via API /api/notifications
    * Support du flash des onglets
    * Messages formatés avec timestamps
    * Queue thread-safe

- `agents.py`
  - Agents spécialisés :
    * SpecificationsAgent
      - Analyse des demandes initiales
      - Extraction des exigences
      - Validation de cohérence
      - Génération de spécifications
      - Mise à jour continue

    * ProductionAgent
      - Génération de code optimisé
      - Respect des standards
      - Refactoring intelligent
      - Tests unitaires
      - Documentation inline

    * ManagementAgent
      - Coordination des agents
      - Gestion des priorités
      - Résolution des conflits
      - Rapports d'avancement
      - Métriques de projet

    * EvaluationAgent
      - Tests fonctionnels
      - Validation qualité
      - Mesures performances
      - Rapports de bugs
      - Suggestions d'amélioration

    * SuiviAgent
      - Documentation temps réel
      - Historique des changements
      - Rapports de progression
      - Métriques d'activité
      - Alertes configurables

    * DuplicationAgent
      - Analyse statique et dynamique
        * Parsing AST complet
        * Graphes de dépendances
        * Analyse sémantique
        * Métriques de complexité
        * Patterns récurrents

      - Détection de duplication
        * Code source
        * Configurations
        * Documentation
        * Tests
        * Resources

      - Analyse d'impact
        * Coût maintenance
        * Dette technique
        * Risques potentiels
        * Bénéfices refactoring
        * ROI estimé

      - Suggestions d'optimisation
        * Extraction méthodes
        * Création classes base
        * Utilisation interfaces
        * Patterns conception
        * Tests de régression

      - Rapports détaillés
        * Visualisations graphiques
        * Métriques quantitatives
        * Recommandations priorisées
        * Plan d'action
        * Suivi des changements

### 3. Services
- `services/base_service.py`
  - Classe abstraite pour tous les services
  - Gestion des erreurs commune
  - Validation des entrées
  - Logging standardisé
  - Opérations fichiers sécurisées

- `services/notification_service.py`
  - Système de notifications temps réel
  - Queue de messages
  - Cache de contenu
  - Diffusion des changements

- `services/agent_service.py`
  - Gestion du cycle de vie des agents
  - Contrôle des états (start/stop)
  - Monitoring des performances
  - Mise à jour des configurations

- `services/mission_service.py`
  - Gestion des missions
  - CRUD et validation
  - Organisation des fichiers
  - Données de test

- `services/notification_service.py`
  - Système de notifications temps réel
  - Queue de messages
  - Cache de contenu
  - Diffusion des changements

### 4. Routes API
- `routes/agent_routes.py`
  - `/api/agents/status` : État des agents
  - `/api/agents/start` : Démarrer tous les agents
  - `/api/agents/stop` : Arrêter tous les agents
  - `/api/agent/<id>/prompt` : GET/POST pour gérer les prompts
  - `/api/agent/<id>/<action>` : Contrôle individuel des agents
  - `/api/agent/<id>/logs` : Historique des opérations
  - `/api/agent/<id>/config` : Configuration des agents

- `routes/notification_routes.py`
  - `/api/notifications` : GET pour récupérer les notifications
  - `/api/notifications` : POST pour envoyer des notifications
  - `/api/changes` : Suivi des modifications en temps réel

- `routes/mission_routes.py`
  - `/api/missions` : CRUD missions
  - `/api/missions/<id>/content` : Contenu des missions
  - `/api/missions/<id>/test-data` : Données de test

- `routes/notification_routes.py`
  - `/api/notifications` : Flux de notifications
  - `/api/changes` : Suivi des modifications

- `routes/view_routes.py`
  - `/` : Redirection vers l'éditeur
  - `/editor` : Interface principale
  - `/agents` : Gestion des agents
  - `/clean` : Vue épurée

### 5. Interface Utilisateur
- `templates/`
  - `base.html` : Template parent
  - `agents.html` : Vue des agents
  - `clean.html` : Interface épurée
  - `editor.html` : Éditeur principal

- `static/js/`
  - `agent-manager.js` : Gestion UI des agents
  - `mission-selector.js` : Navigation des missions
  - `mission-service.js` : Service frontend

- `static/css/`
  - `main.css` : Styles globaux
  - `modal.css` : Fenêtres modales
  - `notifications.css` : Système de notifications
  - `sidebar.css` : Navigation latérale

### 6. Utilitaires
- `utils/`
  - `error_handler.py` : Gestion centralisée des erreurs
    - Formatage uniforme des erreurs via `handle_error()`
    - Conversion en réponses HTTP avec codes appropriés
    - Logging automatique des erreurs
    - Stack traces en mode debug
    - Méthodes spécialisées:
      * `validation_error()`: Erreurs 400
      * `not_found_error()`: Erreurs 404  
      * `service_error()`: Erreurs 500

  - `exceptions.py` : Exceptions personnalisées
    - `ParallagonError`: Exception de base
    - `ValidationError`: Erreurs de validation
    - `ResourceNotFoundError`: Ressource non trouvée
    - `ServiceError`: Erreurs de service
    - `AgentError`: Erreurs d'agent
    - `FileOperationError`: Erreurs fichiers

  - `logger.py` : Système de logging
    - Niveaux: info, success, warning, error, debug
    - Formatage: `[HH:MM:SS] [LEVEL] message`
    - Couleurs par niveau via COLORS dict
    - Double sortie fichier/console
    - Gestion des erreurs de logging

  - `decorators.py` : Décorateurs utilitaires
    - `@safe_operation(max_retries=3, delay=1.0)`
      * Retry automatique avec délai exponentiel
      * Nombre de tentatives configurable
      * Délai entre tentatives paramétrable
      * Logging des retries et erreurs
      * Propagation de la dernière erreur

### 7. Configuration
- `config.py`
  - Variables d'environnement requises:
    * ANTHROPIC_API_KEY : Clé API Anthropic
    * OPENAI_API_KEY : Clé API OpenAI
    * DEBUG : Mode debug (true/false)
    * PORT : Port du serveur (default: 8000)
    * HOST : Host du serveur (default: 0.0.0.0)
    * LOG_LEVEL : Niveau de logging (debug/info/warning/error)
    * FILE_LOCK_TIMEOUT : Timeout verrous fichiers (secondes)
    * CACHE_DURATION : Durée cache prompts (secondes)
    * RETRY_ATTEMPTS : Tentatives opérations (1-5)
    * RETRY_DELAY : Délai entre tentatives (secondes)
    * NOTIFICATION_QUEUE_SIZE : Taille queue notifications (100-1000)
    * MAX_FILE_SIZE : Taille max fichiers (bytes)
    * CONTENT_CACHE_SIZE : Taille cache contenus (items)
    * LOCK_CHECK_INTERVAL : Intervalle vérification verrous (ms)
    * ERROR_RETRY_CODES : Codes erreur pour retry (liste)
    * NOTIFICATION_BATCH_SIZE : Taille lots notifications
    * CACHE_CLEANUP_INTERVAL : Nettoyage cache (secondes)

## Development Guide

### Adding a New Agent
1. Create new agent class in `agents.py`
2. Inherit from `AiderAgent`
3. Implement required methods
4. Register in `AgentService`
5. Add API routes if needed

### Creating a New Service
1. Create service class in `services/`
2. Inherit from `BaseService`
3. Implement core functionality
4. Register in `ParallagonWeb`
5. Add tests

### Frontend Development
1. Add new components in `static/js/`
2. Update templates in `templates/`
3. Add styles in `static/css/`
4. Test with development server

## Fonctionnalités Principales

### Gestion des Missions
1. Création/suppression de missions
2. Organisation des fichiers
3. Chargement de données test
4. Reset des documents

### Agents Autonomes
1. Surveillance continue des fichiers
2. Analyse et modifications automatiques
3. Communication inter-agents
4. Prompts personnalisables

### Interface Utilisateur
1. Éditeur temps réel
2. Notifications instantanées
3. Contrôle des agents
4. Navigation des missions

### Système de Fichiers
1. Structure par mission
2. Fichiers spécialisés par agent
3. Historique des modifications
4. Logs d'opérations

### Détection de Duplication
1. Analyse automatique du code source
   - Scan continu des fichiers
   - Détection des motifs similaires
   - Analyse syntaxique approfondie
   - Métriques de complexité

2. Identification des duplications
   - Fonctions similaires
   - Blocs de code répétés
   - Configurations redondantes
   - Structures de données dupliquées

3. Analyse et suggestions
   - Calcul des métriques de duplication
   - Évaluation de l'impact
   - Propositions de refactoring
   - Estimation des bénéfices

4. Intégration continue
   - Rapports automatiques
   - Seuils d'alerte configurables
   - Historique des modifications
   - Tendances et évolution

## Guides Pratiques

### Démarrage Rapide
1. Configuration environnement
2. Lancement serveur
3. Création première mission
4. Activation des agents

### Développement
1. Ajout nouvel agent
2. Création nouveau service
3. Extension interface utilisateur
4. Tests et débogage

### Maintenance
1. Logs et monitoring
2. Backup des données
3. Mise à jour des dépendances
4. Résolution problèmes courants

### Prompts
- `prompts/duplication.md` : Prompt pour la détection de duplication
