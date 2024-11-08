# Parallagon Documentation

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend development)
- API keys for Anthropic and OpenAI
- portalocker (for file locking)

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
  - Surveillance des fichiers avec portalocker
  - Gestion des chemins avec validation
  - Retry automatique via @safe_operation
  - Logging détaillé avec niveaux
  - Métriques de performance

- `agents.py`
  - Agents spécialisés :
    * SpecificationsAgent : Analyse des demandes et spécifications
    * ProductionAgent : Génération et optimisation du code
    * ManagementAgent : Coordination et gestion du projet
    * EvaluationAgent : Tests et validation
    * SuiviAgent : Documentation et suivi
    * DuplicationAgent : 
      - Détection de code dupliqué avec analyse AST
      - Analyse des fonctions similaires avec métriques de complexité
      - Identification des configurations redondantes avec diff intelligent
      - Suggestions de refactoring basées sur les patterns
      - Analyse de dépendances avec graphe de relations
      - Métriques de duplication avec seuils configurables
      - Rapports détaillés au format Markdown
      - Intégration avec les outils d'analyse statique
      - Historique des modifications avec git blame
      - Suggestions de tests pour le code refactoré

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
    - Formatage uniforme des erreurs
    - Conversion en réponses HTTP
    - Logging automatique
    - Stack traces en mode debug
    - Retry configurable

  - `exceptions.py` : Exceptions personnalisées
    - ParallagonError (base)
    - ValidationError
    - ResourceNotFoundError 
    - ServiceError
    - AgentError
    - FileOperationError

  - `logger.py` : Système de logging
    - Niveaux configurables
    - Formatage timestamp
    - Couleurs par niveau
    - Sortie fichier/console
    - Rotation des logs

  - `decorators.py` : Décorateurs utilitaires
    - @safe_operation
      * Retry automatique
      * Délai configurable
      * Nombre max de tentatives
      * Logging des retries
      * Gestion des timeouts

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
