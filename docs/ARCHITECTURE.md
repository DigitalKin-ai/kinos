# Architecture KinOS

## Overview

KinOS est un système d'agents autonomes conçu pour simplifier et accélérer le développement de projets complexes via une interface en ligne de commande (CLI). L'architecture est centrée sur:

- Agents autonomes avec gestion dynamique des ressources
- Communication via système de fichiers
- Interface CLI simple et efficace
- Gestion intelligente des chemins

## Component Architecture

### Core
- `kinos_cli.py` - Point d'entrée principal CLI
  - Gestion des commandes et options
  - Initialisation des services
  - Gestion des erreurs avec retry
  - Monitoring des agents
  - Configuration dynamique
  - Validation des chemins
  - Logging détaillé
  - Gestion des ressources

### Single Server Architecture

KinOS uses a single server architecture where both frontend and backend are served from the same Flask application:

#### Overview
- No separate backend server
- No traditional database
- File system as primary storage
- Single port (default: 8000)

#### Key Design Choices

1. **Unified Server**
   - Flask serves both static files and API endpoints
   - All requests handled by same process
   - Relative API paths (/api/*) instead of absolute URLs
   - Simplified deployment and configuration

2. **File-Based Storage**
   - File system as primary data store
   - No traditional database required
   - Directory structure:
     ```
     project_root/
     ├── missions/           # Mission data and files
     │   └── <mission_name>/
     │       ├── demande.md
     │       ├── specifications.md
     │       └── ...
     ├── prompts/           # Agent prompts
     ├── config/           # Configuration files
     ├── static/           # Frontend assets
     ├── templates/        # HTML templates
     └── logs/            # Application logs
     ```

3. **API Design**
   - RESTful endpoints under /api prefix
   - File operations handled synchronously
   - Portalocker for thread-safe file access
   - Caching for performance optimization

4. **Frontend Integration**
   - Vue.js components served from /static
   - API calls use relative paths:
     ```javascript
     // Correct
     fetch('/api/missions')
     
     // Incorrect - don't use absolute URLs
     fetch('http://localhost:8000/api/missions')
     ```

#### Benefits
- Simplified deployment (single process)
- No database configuration needed
- Easy backup (just copy files)
- Reduced complexity
- Direct file system access
- Portable between systems

#### Considerations
- Scale limited by file system performance
- Concurrent access managed via file locks
- Regular backups recommended
- Monitor disk space usage
- Consider file system limitations

### Agents
- `agents/kinos_agent.py` - Base agent class
  - Dynamic file management
  - Flexible file monitoring
  - Self-regulated execution cycles
  - Automatic error recovery
  - Adaptive timing control
  - Smart resource management

- `agents/aider_agent.py` - Aider integration
  - Prompt management with caching
  - File operation coordination
  - Change notifications
  - Error handling and retry

- Specific agent implementations:
  - SpecificationsAgent - Requirements analysis
  - ProductionAgent - Code generation and optimization
  - ManagementAgent - Activity coordination
  - EvaluationAgent - Testing and validation
  - ChroniqueurAgent - Progress tracking
  - ValidationAgent - Validation et conformité
    * Validation des spécifications
    * Vérification de la conformité
    * Mesures quantitatives
    * Validation des critères objectifs
    * Contrôle qualité automatisé
    * Contrôle qualité automatisé

### Services
- `services/base_service.py` - Base class for all services
  - Error handling with retry policies
  - Input validation with custom rules
  - Standardized logging system
  - Thread-safe file operations
  - Resource cleanup
  - Service lifecycle management

- `services/cache_service.py` - Multi-level caching service
  - Memory cache (LRU)
  - File content cache
  - Prompt cache
  - Metadata cache
  - Cache metrics collection
  - Automatic cleanup

- `services/file_service.py` - File operations service
  - Thread-safe file operations
  - Content caching
  - Path validation
  - Mission file management
  - Error recovery

- `services/notification_service.py` - Real-time notification service
  - Message queue management
  - Content change detection
  - Cache performance metrics
  - Real-time updates

### File System
- Structure dynamique par mission
  * Organisation flexible des fichiers
  * Création à la demande par les agents
  * Pas de structure prédéfinie imposée
  * Support multi-fichiers par agent

- Gestion intelligente des chemins
  * Normalisation automatique via FileManager
  * Validation stricte des permissions
  * Résolution dynamique des chemins
  * Support des chemins relatifs/absolus
  * Prévention des conflits de noms

- Sécurité et validation
  * Vérification des permissions UNIX
  * Validation des chemins de fichiers
  * Prévention des traversées de répertoire
  * Nettoyage automatique des ressources
  * Logging des opérations sensibles

- Optimisation des accès
  * Cache intelligent du contenu
  * Verrouillage thread-safe
  * Retry automatique sur erreur
  * Gestion efficace des ressources
  * Métriques de performance

### Error Management
- Centralized error handling via ErrorHandler
- Custom exception hierarchy
  - KinOSError (base)
  - ValidationError
  - ResourceNotFoundError
  - ServiceError
  - AgentError
  - FileOperationError
- Automatic retries with @safe_operation decorator
- Detailed error logging with stack traces

### Utils
- `utils/decorators.py` - Utility decorators
  - @safe_operation decorator for error handling
  - Retry logic with exponential backoff
  
- `utils/exceptions.py` - Custom exceptions hierarchy
  - Standardized error handling
  - Error classification
  - Custom error messages
  - Stack trace preservation

- `utils/logger.py` - Advanced logging system
  - Colored output by level
  - File and console logging
  - Timestamp formatting
  - Error context capture

  - Gestion des erreurs commune
    * Capture et logging des exceptions
    * Formatage des messages d'erreur
    * Retry automatique configurable
    * Fallback sur valeurs par défaut
    * Propagation contrôlée
    * Nettoyage des ressources
    * Circuit breaker pattern
    * Métriques d'erreurs
    * Alerting configurable
    * Recovery automatique

  - Méthodes communes héritées
    * _validate_input() - Validation des entrées
    * _handle_error() - Gestion des erreurs
    * _log_operation() - Logging unifié
    * _safe_file_operation() - Opérations fichiers
    * _ensure_directory() - Gestion dossiers
    * cleanup() - Nettoyage ressources

  - Validation des entrées
    * Vérification des types
    * Validation des formats
    * Contraintes personnalisées
    * Messages d'erreur détaillés
    * Sanitization des données

  - Logging standardisé
    * Niveaux de log configurables
    * Rotation des fichiers
    * Format unifié
    * Contexte d'exécution
    * Métriques de performance

  - Opérations fichiers sécurisées
    * Verrouillage avec portalocker
    * Timeouts configurables
    * Retry sur échec
    * Nettoyage automatique
    * Validation des chemins

  - Cache et optimisation
    * Cache mémoire LRU
    * Invalidation intelligente
    * Préchargement configurable
    * Métriques d'utilisation
    * Nettoyage périodique

  - Retry automatique
    * Politiques configurables
    * Délais exponentiels
    * Conditions personnalisées
    * Limites de tentatives
    * Logging des retries

- `services/agent_service.py` - Gestion des agents
  - Initialisation des agents
  - Contrôle (start/stop)
  - Surveillance des états
  - Mise à jour des chemins

- `services/mission_service.py` - Gestion des missions
  - CRUD missions
  - Gestion des fichiers de mission
  - Chargement des données test

- `services/notification_service.py` - Gestion des notifications
  - File d'attente de notifications
  - Mise à jour du contenu
  - Cache de contenu

### Routes
- `routes/agent_routes.py` - Routes API agents
  - Status des agents
  - Contrôle des agents
  - Gestion des prompts

- `routes/mission_routes.py` - Routes API missions
  - CRUD missions
  - Contenu des missions
  - Reset/Test data

- `routes/notification_routes.py` - Routes API notifications
  - Récupération notifications
  - Changements de contenu

- `routes/view_routes.py` - Routes des vues
  - Interface éditeur
  - Interface agents
  - Interface clean

### Utils
- `utils/error_handler.py` - Gestion centralisée des erreurs
  - Formatage des erreurs
  - Réponses HTTP
  - Stack traces

- `utils/exceptions.py` - Exceptions personnalisées
  - KinOSError
  - ValidationError
  - ServiceError
  - etc.

- `utils/logger.py` - Système de logging
  - Formatage des logs
  - Niveaux de log
  - Sortie fichier/console

- `utils/decorators.py` - Décorateurs utilitaires
  - safe_operation
  - Retry logic

### Teams Management

#### Architecture
- **Team Configuration**
  - Predefined team templates in teams-manager.js
  - Dynamic agent groupings
  - Flexible team composition
  - Status tracking per team

- **Team Operations**
  - Centralized control via TeamsManager component
  - Real-time status monitoring
  - Individual and team-wide agent controls
  - Performance metrics collection

- **State Management**
  - Team status tracking
  - Agent status per team
  - Loading states
  - Operation history
  - Performance metrics

- **Interface Components**
  - TeamsManager Vue component
  - Team cards with controls
  - Agent status indicators
  - Performance displays
  - Real-time updates

#### Data Flow
1. Team Configuration
   - Stored in teams-manager.js
   - Loaded on component mount
   - Updated via UI interactions
   - Persisted across sessions

2. Status Updates
   - Regular polling of agent states
   - Real-time metric updates
   - Team efficiency calculations
   - History tracking

3. Control Operations
   - Team-wide start/stop
   - Individual agent toggling
   - Loading state management
   - Error handling and recovery

#### Integration
- Interfaces with AgentService
- Coordinates with NotificationService
- Uses shared caching layer
- Maintains operation history

### Frontend Components

#### JavaScript
- `static/js/api-client.js` - API client for frontend
  - Features:
    * Base URL configuration
    * Token management
    * Response handling
    * Error handling

- `static/js/agent-manager.js`
  - Props:
    * currentMission: Object
  - Events:
    * agent-started
    * agent-stopped
    * prompt-updated
  - Features:
    * Real-time agent status
    * Prompt editing
    * Start/Stop controls
    * Status indicators

- `static/js/mission-selector.js`
  - Props:
    * currentMission: Object
    * missions: Array
    * loading: Boolean
  - Events:
    * select-mission
    * create-mission
    * sidebar-toggle
  - Features:
    * Mission list navigation
    * Create new missions
    * Collapsible sidebar
    * Loading states

#### Notification System
- Real-time updates via polling
- Flash messages for important events
- Tab highlighting for changes
- Status indicators
- Error handling
- Loading states
- Success confirmations

- `static/css/`
  - `sidebar.css` - Styles de la sidebar
  - `main.css` - Styles globaux
  - `modal.css` - Styles des modals
  - `notifications.css` - Styles des notifications

### Templates
- `templates/`
  - `base.html` - Template de base
  - `agents.html` - Vue des agents
  - `editor.html` - Interface d'édition
  - `clean.html` - Interface clean

### Configuration
- `config.py` - Configuration de l'application
  - Variables d'environnement requises
    * ANTHROPIC_API_KEY - Clé API Anthropic
    * OPENAI_API_KEY - Clé API OpenAI
    * DEBUG - Mode debug (true/false)
    * PORT - Port serveur (default: 8000)
    * HOST - Host serveur (default: 0.0.0.0)
    * LOG_LEVEL - Niveau logging
    * FILE_LOCK_TIMEOUT - Timeout verrous
    * CACHE_DURATION - Durée cache
    * RETRY_ATTEMPTS - Tentatives max
    * RETRY_DELAY - Délai entre tentatives
    * NOTIFICATION_QUEUE_SIZE - Taille queue
    * MAX_FILE_SIZE - Taille max fichiers
    * CONTENT_CACHE_SIZE - Taille cache
    * LOCK_CHECK_INTERVAL - Intervalle verrous
    * ERROR_RETRY_CODES - Codes pour retry
    * NOTIFICATION_BATCH_SIZE - Taille lots
    * CACHE_CLEANUP_INTERVAL - Nettoyage

  - Validation configuration
    * Types de données
    * Valeurs par défaut
    * Contraintes
    * Dépendances
    * Logging erreurs

## Flux de Données

1. Interface utilisateur
   - Routes view pour le rendu des templates
   - Routes API REST pour les opérations CRUD
   - Notifications temps réel via polling optimisé
   - Gestion des états avec Vue.js
   - Validation côté client

2. Services (via BaseService)
   - Validation des entrées avec _validate_input()
   - Gestion des erreurs via _handle_error()
   - Logging unifié avec _log_operation()
   - Opérations fichiers sécurisées
   - Communication inter-services

3. Agents (via AiderAgent)
   - Surveillance fichiers avec portalocker
   - Exécution des commandes Aider
   - Cache des prompts avec invalidation
   - Notification des changements
   - Gestion des erreurs et retry

4. Système de fichiers
   - Structure par mission avec FileManager
   - Verrouillage thread-safe via portalocker
     * Timeouts configurables
     * Retry automatique
     * Nettoyage des verrous
   - Cache de contenu avec invalidation
     * Timestamps pour détection changements
     * Cache LRU en mémoire
     * Préchargement intelligent
   - Notifications temps réel
     * Queue de messages thread-safe
     * Agrégation des changements
     * Diffusion optimisée

## Nouvelles Fonctionnalités

1. Système de Notifications
   - Architecture temps réel
     * Service dédié NotificationService
     * Queue de messages thread-safe
     * Système publish/subscribe
     * Gestion des connexions WebSocket
     * Heartbeat et reconnexion
     * Métriques temps réel

   - Queue de messages
     * File d'attente thread-safe
     * Priorités configurables 
     * Batching intelligent
     * Timeout par message
     * Retry sur échec
     * Métriques de performance
     * Nettoyage périodique
     * Persistance optionnelle
     * Ordre garanti FIFO
     * Gestion backpressure

   - Types de notifications
     * Info - Informations générales
     * Success - Opérations réussies
     * Warning - Avertissements
     * Error - Erreurs système
     * Flash - Notifications éphémères
     * Status - États des agents
     * Content - Changements contenu
     * System - Messages système

   - Cache de contenu intelligent
     * Cache LRU en mémoire
     * Invalidation par timestamp
     * Préchargement adaptatif
     * Compression des données
     * Limites configurables
     * Métriques d'utilisation

   - Diffusion des changements
     * Notifications WebSocket
     * Polling optimisé
     * Filtrage par type
     * Agrégation intelligente
     * Ordre préservé
     * Gestion des erreurs

   - Gestion des états
     * États atomiques
     * Transitions validées
     * Historique des changements
     * Restauration sur erreur
     * Métriques de stabilité
     * Alertes configurables

2. Gestion des Erreurs
   - Centralisation avec ErrorHandler
   - Retry automatique avec @safe_operation
   - Logging détaillé
   - Recovery intelligent

3. Système de Cache
   - Cache multi-niveaux
     * Cache mémoire LRU
     * Cache Redis distribué
     * Cache de session
     * Cache de prompts
     * Cache de contenu

   - Stratégies d'invalidation
     * Par timestamp
     * Par dépendances
     * Par événements
     * Invalidation cascade
     * Préchargement intelligent

   - Configuration
     * Taille maximale par niveau
     * TTL configurable
     * Politique d'éviction
     * Compression données
     * Métriques utilisation

   - Verrouillage distribué
     * Portalocker pour fichiers
     * Verrous Redis pour cache
     * Timeouts configurables
     * Retry automatique
     * Détection deadlocks

4. Verrouillage Fichiers
   - Utilisation de portalocker
   - Gestion des timeouts
   - Recovery automatique
   - Prévention des conflits

## Points d'Extension

1. Nouveaux Agents
   - Hériter de AiderAgent
   - Implémenter méthodes requises:
     * _build_prompt()
     * _run_aider()
     * list_files()
   - Configurer:
     * Prompt file
     * Fichiers à surveiller
     * Intervalles d'exécution

2. Nouveaux Services
   - Hériter de BaseService
   - Implémenter méthodes standard:
     * _validate_input()
     * _handle_error() 
     * _log_operation()
   - Ajouter:
     * Gestion des erreurs spécifiques
     * Validation des entrées
     * Logging personnalisé
     * Cache si nécessaire

3. Nouvelles Fonctionnalités UI
   - Ajouter les composants Vue.js
   - Créer les routes API
   - Mettre à jour les templates

## Sécurité et Performance

1. Validation et Sécurité
   - Validation des entrées
     * Types et formats
     * Tailles maximales
     * Caractères autorisés
     * Chemins de fichiers
     * JSON/XML valide

   - Sécurité des fichiers
     * Verrouillage avec portalocker
     * Timeouts configurables
     * Retry sur échec
     * Nettoyage automatique
     * Chemins sécurisés

   - Protection des données
     * CORS configurable
     * Rate limiting
     * Validation des sessions
     * Sanitization HTML
     * Logs sécurisés

2. Gestion des Erreurs
   - Logging centralisé avec rotation des fichiers
   - Réponses formatées avec codes HTTP appropriés
   - Recovery automatique avec circuit breaker
   - Alerting configurable (email, Slack)
   - Métriques d'erreurs avec Prometheus
   - Traçabilité avec OpenTelemetry

3. Optimisation
   - Cache de contenu multi-niveaux
     * Cache mémoire avec LRU
     * Cache Redis distribué
     * Cache de session utilisateur
   - Rate limiting adaptatif
   - Pooling de connexions avec timeouts
   - Compression des réponses
   - Lazy loading des ressources
   - Minification des assets
