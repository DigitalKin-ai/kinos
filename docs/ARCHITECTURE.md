# Architecture KinOS

## Overview

KinOS est un système d'agents autonomes conçu pour simplifier et accélérer le développement de projets complexes via une interface en ligne de commande (CLI). L'architecture est centrée sur:

- Agents autonomes avec gestion dynamique des ressources
- Communication via système de fichiers
- Interface CLI simple et efficace
- Gestion intelligente des chemins

## Component Architecture

### Core Components

1. **CLI Interface** (`kinos_cli.py`)
   - Single command entry point: `kin`
   - Current directory detection
   - Dynamic team loading
   - Real-time agent monitoring
   - Error handling with retry
   - Graceful shutdown handling

2. **Agent System**
   - Autonomous file-focused agents
   - Self-regulated execution cycles
   - Dynamic file management
   - Automatic error recovery
   - Adaptive timing control
   - Smart resource management

3. **File System**
   - Current directory as mission context
   - Dynamic path validation
   - Thread-safe file operations
   - Automatic backup handling
   - Permission validation
   - Resource cleanup

4. **Services Layer**
   - Team management
   - Agent coordination
   - File operations
   - Path validation
   - Error handling
   - Resource management

### Key Features

1. **Simplicity**
   - Zero configuration required
   - Current directory = mission context
   - Single command operation
   - Automatic team selection
   - Graceful error handling

2. **Autonomy**
   - Self-managing agents
   - Dynamic resource allocation
   - Automatic recovery
   - Smart scheduling
   - Independent operation

3. **Flexibility**
   - Works in any directory
   - Multiple team configurations
   - Adaptable to any project
   - Language agnostic
   - Extensible design

### System Architecture

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
  - ValidationAgent - Quality control and conformity

### Services

- `services/base_service.py` - Base class for all services
  - Error handling with retry policies
  - Input validation with custom rules
  - Standardized logging system
  - Thread-safe file operations
  - Resource cleanup
  - Service lifecycle management

- `services/team_service.py` - Team management service
  - Team configuration and initialization
  - Agent coordination
  - Status monitoring
  - Performance metrics

- `services/file_service.py` - File operations service
  - Thread-safe file operations
  - Content caching
  - Path validation
  - Mission file management
  - Error recovery

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

### Map System

Le système de map fournit une vue d'ensemble structurée du projet et surveille la taille des documents.

#### Vue d'Ensemble

La map est un document Markdown généré automatiquement qui :
- Affiche l'arborescence complète du projet
- Surveille la taille des fichiers en tokens
- Fournit des alertes visuelles sur les fichiers trop longs
- Aide à maintenir des documents de taille raisonnable

#### Seuils de Taille (en tokens)

- ✓ OK : < 6k tokens
- ⚠️ Long : > 6k tokens 
- 🔴 Trop long : > 12k tokens

Ces seuils sont choisis pour :
- Maintenir les documents dans une taille gérable
- Faciliter la revue et la maintenance
- Optimiser l'utilisation des modèles de langage
- Encourager la modularisation du contenu

#### Format de la Map

```
# Project Map
Generated: 2024-03-21 15:30:45

## Document Tree
📁 Project
├── 📁 docs/
│   ├── 📄 architecture.md (4.2k tokens) ✓
│   └── 📄 api.md (7.1k tokens) ⚠️
├── 📁 src/
│   └── 📄 main.md (13.5k tokens) 🔴
└── 📄 README.md (2.1k tokens) ✓

## Warnings
⚠️ api.md approaching limit (>6k tokens)
🔴 main.md needs consolidation (>12k tokens)
```

#### Fonctionnalités

1. **Surveillance Automatique**
   - Analyse continue des fichiers Markdown
   - Mise à jour automatique après modifications
   - Calcul précis des tokens via Anthropic
   - Détection des dépassements de seuils

2. **Visualisation Claire**
   - Arborescence intuitive du projet
   - Indicateurs visuels de taille (✓, ⚠️, 🔴)
   - Tailles affichées en kilotokens
   - Section dédiée aux avertissements

3. **Aide à la Maintenance**
   - Identification rapide des fichiers problématiques
   - Suggestions de consolidation
   - Historique des changements de taille
   - Guide pour la restructuration

4. **Intégration**
   - Mise à jour via MapService
   - Accessible via l'API (/api/map)
   - Notifications de changements
   - Hooks de pré-commit disponibles

#### Utilisation

1. **Consultation**
   ```bash
   # Voir la map actuelle
   cat map.md
   ```

2. **Mise à jour Manuelle**
   ```python
   # Via l'API
   map_service.update_map()
   ```

3. **Surveillance Continue**
   - La map est mise à jour automatiquement après chaque modification de fichier
   - Les agents utilisent la map pour guider leurs décisions
   - Les avertissements sont propagés via le système de notifications

#### Bonnes Pratiques

1. **Structure des Documents**
   - Viser des documents < 6k tokens
   - Diviser les longs documents
   - Utiliser des références croisées
   - Maintenir une hiérarchie claire

2. **Maintenance**
   - Surveiller les avertissements de taille
   - Restructurer avant d'atteindre les limites
   - Réviser régulièrement l'organisation
   - Documenter les décisions de structure

3. **Optimisation**
   - Extraire les sections communes
   - Utiliser des liens plutôt que la duplication
   - Maintenir une granularité cohérente
   - Regrouper logiquement le contenu

### Phase System

Le système de phases permet une gestion intelligente de la taille totale du projet basée sur l'utilisation des tokens.

#### Vue d'Ensemble

Le système alterne automatiquement entre deux phases :
- EXPANSION : Création libre de contenu
- CONVERGENCE : Focus sur l'optimisation et la consolidation

Cette alternance est pilotée par des seuils d'utilisation des tokens du projet.

#### Constantes Système

```python
MODEL_TOKEN_LIMIT = 128_000  # Limite du modèle
CONVERGENCE_THRESHOLD = 0.60  # Seuil de passage en convergence (60%)
EXPANSION_THRESHOLD = 0.50    # Seuil de retour en expansion (50%)

# Valeurs dérivées en tokens
CONVERGENCE_TOKENS = 76_800   # 128k * 0.60
EXPANSION_TOKENS = 64_000     # 128k * 0.50
```

#### Format de la Map avec Phases

```markdown
# Project Map
Generated: 2024-03-21 15:30:45
Current Phase: EXPANSION

## Token Usage
Total: 72.5k/128k (56.6%)
Convergence at: 76.8k (60%)

## Phase Status
⚠️ Approaching convergence threshold
Headroom: 4.3k tokens

## Document Tree
📁 Project/
├── 📄 specifications.md (12.3k tokens)
├── 📁 docs/
│   └── 📄 guide.md (8.2k tokens)
[...]
```

#### États du Système

1. **EXPANSION**
   - État par défaut
   - Création libre de contenu
   - Monitoring continu des tokens
   - Avertissements à l'approche du seuil
   - Affichage du headroom disponible

2. **CONVERGENCE**
   - État de consolidation
   - Focus sur la réduction des tokens
   - Restriction sur nouveau contenu
   - Suggestions d'optimisation
   - Tracking de la réduction

#### Règles de Transition

1. **EXPANSION → CONVERGENCE**
   - Déclencheur: total_tokens > 76.8k
   - Action immédiate
   - Message: "Convergence needed - Token limit approaching"

2. **CONVERGENCE → EXPANSION**
   - Déclencheur: total_tokens < 64k
   - Action immédiate
   - Message: "Returning to expansion - Token usage optimized"

#### Indicateurs Visuels

1. **Symboles de Status**
   - ✓ : < 55% (<70.4k tokens)
   - ⚠️ : 55-60% (70.4k-76.8k tokens)
   - 🔴 : > 60% (>76.8k tokens)

2. **Messages de Status**
   - "Below convergence threshold"
   - "Approaching convergence threshold"
   - "Convergence needed"

#### Mise à Jour Automatique

1. **Déclencheurs**
   - Modification de fichier .md
   - Création/suppression de fichier
   - Changement de phase

2. **Processus**
   ```python
   def update_map():
       total_tokens = count_total_tokens()
       current_phase = determine_phase(total_tokens)
       update_map_file(total_tokens, current_phase)
       handle_phase_transition(current_phase)
   ```

#### Interface CLI

```bash
# Voir état actuel
kin status

# Voir détails tokens
kin tokens

# Forcer changement phase (debug)
kin phase [expansion|convergence]
```

#### Bonnes Pratiques

1. **En Phase d'EXPANSION**
   - Créer librement du contenu
   - Surveiller les avertissements
   - Anticiper la convergence
   - Maintenir une structure claire

2. **En Phase de CONVERGENCE**
   - Prioriser la consolidation
   - Optimiser les gros fichiers
   - Restructurer le contenu
   - Éliminer la redondance

#### Limitations Actuelles

- Pas de tracking individuel des fichiers
- Pas de seuils par fichier
- Pas d'historique des phases
- Pas de période de grâce lors des transitions

La map est un document Markdown généré automatiquement qui :
- Affiche l'arborescence complète du projet
- Surveille la taille des fichiers en tokens
- Fournit des alertes visuelles sur les fichiers trop longs
- Aide à maintenir des documents de taille raisonnable

#### Seuils de Taille (en tokens)

- ✓ OK : < 6k tokens
- ⚠️ Long : > 6k tokens 
- 🔴 Trop long : > 12k tokens

Ces seuils sont choisis pour :
- Maintenir les documents dans une taille gérable
- Faciliter la revue et la maintenance
- Optimiser l'utilisation des modèles de langage
- Encourager la modularisation du contenu

#### Format de la Map

```
# Project Map
Generated: 2024-03-21 15:30:45

## Document Tree
📁 Project
├── 📁 docs/
│   ├── 📄 architecture.md (4.2k tokens) ✓
│   └── 📄 api.md (7.1k tokens) ⚠️
├── 📁 src/
│   └── 📄 main.md (13.5k tokens) 🔴
└── 📄 README.md (2.1k tokens) ✓

## Warnings
⚠️ api.md approaching limit (>6k tokens)
🔴 main.md needs consolidation (>12k tokens)
```

#### Fonctionnalités

1. **Surveillance Automatique**
   - Analyse continue des fichiers Markdown
   - Mise à jour automatique après modifications
   - Calcul précis des tokens via Anthropic
   - Détection des dépassements de seuils

2. **Visualisation Claire**
   - Arborescence intuitive du projet
   - Indicateurs visuels de taille (✓, ⚠️, 🔴)
   - Tailles affichées en kilotokens
   - Section dédiée aux avertissements

3. **Aide à la Maintenance**
   - Identification rapide des fichiers problématiques
   - Suggestions de consolidation
   - Historique des changements de taille
   - Guide pour la restructuration

4. **Intégration**
   - Mise à jour via MapService
   - Accessible via l'API (/api/map)
   - Notifications de changements
   - Hooks de pré-commit disponibles

#### Utilisation

1. **Consultation**
   ```bash
   # Voir la map actuelle
   cat map.md
   ```

2. **Mise à jour Manuelle**
   ```python
   # Via l'API
   map_service.update_map()
   ```

3. **Surveillance Continue**
   - La map est mise à jour automatiquement après chaque modification de fichier
   - Les agents utilisent la map pour guider leurs décisions
   - Les avertissements sont propagés via le système de notifications

#### Bonnes Pratiques

1. **Structure des Documents**
   - Viser des documents < 6k tokens
   - Diviser les longs documents
   - Utiliser des références croisées
   - Maintenir une hiérarchie claire

2. **Maintenance**
   - Surveiller les avertissements de taille
   - Restructurer avant d'atteindre les limites
   - Réviser régulièrement l'organisation
   - Documenter les décisions de structure

3. **Optimisation**
   - Extraire les sections communes
   - Utiliser des liens plutôt que la duplication
   - Maintenir une granularité cohérente
   - Regrouper logiquement le contenu

### Phase System

Le système de phases permet une gestion intelligente de la taille totale du projet basée sur l'utilisation des tokens.

#### Vue d'Ensemble

Le système alterne automatiquement entre deux phases :
- EXPANSION : Création libre de contenu
- CONVERGENCE : Focus sur l'optimisation et la consolidation

Cette alternance est pilotée par des seuils d'utilisation des tokens du projet.

#### Constantes Système

```python
MODEL_TOKEN_LIMIT = 128_000  # Limite du modèle
CONVERGENCE_THRESHOLD = 0.60  # Seuil de passage en convergence (60%)
EXPANSION_THRESHOLD = 0.50    # Seuil de retour en expansion (50%)

# Valeurs dérivées en tokens
CONVERGENCE_TOKENS = 76_800   # 128k * 0.60
EXPANSION_TOKENS = 64_000     # 128k * 0.50
```

#### Format de la Map avec Phases

```markdown
# Project Map
Generated: 2024-03-21 15:30:45
Current Phase: EXPANSION

## Token Usage
Total: 72.5k/128k (56.6%)
Convergence at: 76.8k (60%)

## Phase Status
⚠️ Approaching convergence threshold
Headroom: 4.3k tokens

## Document Tree
📁 Project/
├── 📄 specifications.md (12.3k tokens)
├── 📁 docs/
│   └── 📄 guide.md (8.2k tokens)
[...]
```

#### États du Système

1. **EXPANSION**
   - État par défaut
   - Création libre de contenu
   - Monitoring continu des tokens
   - Avertissements à l'approche du seuil
   - Affichage du headroom disponible

2. **CONVERGENCE**
   - État de consolidation
   - Focus sur la réduction des tokens
   - Restriction sur nouveau contenu
   - Suggestions d'optimisation
   - Tracking de la réduction

#### Règles de Transition

1. **EXPANSION → CONVERGENCE**
   - Déclencheur: total_tokens > 76.8k
   - Action immédiate
   - Message: "Convergence needed - Token limit approaching"

2. **CONVERGENCE → EXPANSION**
   - Déclencheur: total_tokens < 64k
   - Action immédiate
   - Message: "Returning to expansion - Token usage optimized"

#### Indicateurs Visuels

1. **Symboles de Status**
   - ✓ : < 55% (<70.4k tokens)
   - ⚠️ : 55-60% (70.4k-76.8k tokens)
   - 🔴 : > 60% (>76.8k tokens)

2. **Messages de Status**
   - "Below convergence threshold"
   - "Approaching convergence threshold"
   - "Convergence needed"

#### Mise à Jour Automatique

1. **Déclencheurs**
   - Modification de fichier .md
   - Création/suppression de fichier
   - Changement de phase

2. **Processus**
   ```python
   def update_map():
       total_tokens = count_total_tokens()
       current_phase = determine_phase(total_tokens)
       update_map_file(total_tokens, current_phase)
       handle_phase_transition(current_phase)
   ```

#### Interface CLI

```bash
# Voir état actuel
kin status

# Voir détails tokens
kin tokens

# Forcer changement phase (debug)
kin phase [expansion|convergence]
```

#### Bonnes Pratiques

1. **En Phase d'EXPANSION**
   - Créer librement du contenu
   - Surveiller les avertissements
   - Anticiper la convergence
   - Maintenir une structure claire

2. **En Phase de CONVERGENCE**
   - Prioriser la consolidation
   - Optimiser les gros fichiers
   - Restructurer le contenu
   - Éliminer la redondance

#### Limitations Actuelles

- Pas de tracking individuel des fichiers
- Pas de seuils par fichier
- Pas d'historique des phases
- Pas de période de grâce lors des transitions

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

#### Predefined Teams
Teams are simple agent groupings optimized for specific tasks:

1. **default**
   - Purpose: General purpose team
   - Agents:
     * SpecificationsAgent - Requirements analysis
     * ManagementAgent - Project coordination
     * EvaluationAgent - Quality control
     * ChroniqueurAgent - Progress tracking
     * DocumentalisteAgent - Documentation

2. **coding**
   - Purpose: Software development
   - Agents:
     * SpecificationsAgent - Technical requirements
     * ProductionAgent - Code generation
     * TesteurAgent - Testing
     * DocumentalisteAgent - Documentation
     * ValidationAgent - Code quality

3. **literature-review**
   - Purpose: Research and analysis
   - Agents:
     * SpecificationsAgent - Review scope
     * EvaluationAgent - Analysis
     * ChroniqueurAgent - Progress tracking
     * DocumentalisteAgent - Source organization
     * ValidationAgent - Review validation

#### Team Operations
- **Launch**: `kin [team-name]`
- **Monitor**: Real-time status in terminal
- **Control**: Graceful shutdown with Ctrl+C
- **Recovery**: Automatic error handling and retry

#### Integration
- Automatic directory detection
- Dynamic path resolution
- Thread-safe file operations
- Graceful error handling

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
