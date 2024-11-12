# KinOS Documentation

## Architecture

### Commit Icons

Les commits sont catégorisés visuellement avec des icônes spécifiques :

| Catégorie | Icône | Description |
|-----------|-------|-------------|
| feat | ✨ | Nouvelle fonctionnalité |
| fix | 🐛 | Correction de bug |
| docs | 📚 | Documentation |
| style | 💎 | Style/formatage |
| refactor | ♻️ | Refactoring |
| perf | ⚡️ | Performance |
| test | 🧪 | Tests |
| build | 📦 | Build/dépendances |
| ci | 🔄 | CI/CD |
| chore | 🔧 | Maintenance |
| revert | ⏪ | Retour arrière |
| autre | 🔨 | Type non catégorisé |

Format des messages de commit :
```bash
[AgentName] <icône> Commit [<type>] <hash>: <message>
```

Exemples :
```bash
[AgentName] ♻️ Commit [refactor] e7975b9: Remove web_instance references
[AgentName] 🐛 Commit [fix] a1b2c3d: Fix race condition in file locking
[AgentName] ✨ Commit [feat] x7y8z9w: Add new notification system
```

Cette catégorisation visuelle permet :
- Une identification rapide du type de modification
- Une meilleure lisibilité des logs
- Une cohérence avec les conventions de commit conventionnels
- Un suivi facilité des différents types de changements

### Agents

#### Architecture des Agents
- **Gestion autonome des fichiers**
  - Chaque agent détermine ses besoins en fichiers
  - Création dynamique des fichiers selon le contexte
  - Modification flexible de multiples fichiers
  - Surveillance intelligente des fichiers pertinents
  - Adaptation aux changements de structure

- **Gestion des chemins**
  - Utilisation des chemins relatifs pour les opérations
  - Normalisation des noms de mission via FileManager
  - Validation stricte des permissions d'accès
  - Respect de la structure de dossiers existante

- **Cycle de vie**
  1. Initialisation
     - Vérification du dossier mission
     - Chargement des prompts
     - Configuration des chemins relatifs
     - Validation des permissions

  2. Exécution
     - Surveillance autonome des fichiers pertinents
     - Création/modification de fichiers selon besoins
     - Adaptation dynamique aux changements
     - Gestion indépendante des ressources

  3. Communication
     - Notifications de changements
     - Coordination via système de fichiers
     - Logging détaillé des opérations
     - Gestion des erreurs autonome

#### Types d'Agents
Chaque agent peut maintenant :
- Gérer plusieurs fichiers simultanément
- Créer ses fichiers à la demande
- Définir sa propre stratégie de surveillance
- Adapter son comportement selon le contexte

1. **SpecificationsAgent**
   - Analyse des demandes et définition des spécifications
   - Gestion flexible des documents de spécifications
   - Création de sous-spécifications si nécessaire
   - Maintien de la cohérence entre documents

2. **ProductionAgent**
   - Génération et optimisation du code/contenu
   - Organisation libre des fichiers de production
   - Création de modules/composants selon besoins
   - Gestion des dépendances entre fichiers

3. **ManagementAgent**
   - Coordination et suivi du projet
   - Organisation flexible des tâches
   - Création de rapports et tableaux de bord
   - Gestion des priorités et ressources

4. **EvaluationAgent**
   - Tests et validation qualité
   - Organisation des suites de tests
   - Rapports de couverture
   - Analyse des performances

6. **DocumentalisteAgent**
   - Maintien de la documentation
   - Organisation des références
   - Validation de la cohérence
   - Génération de documentation

7. **DuplicationAgent**
   - Analyse du code et contenu
   - Détection des duplications
   - Suggestions d'optimisation
   - Refactoring automatique

8. **TesteurAgent**
   - Création et exécution des tests
   - Validation des fonctionnalités
   - Rapports de couverture
   - Tests de régression

9. **RedacteurAgent**
   - Rédaction et mise à jour du contenu
   - Organisation des documents
   - Validation du style
   - Gestion des versions

10. **ValidationAgent**
    - Validation des livrables et conformité
    - Responsabilités:
      * Validation des spécifications
      * Vérification de la conformité
      * Mesures quantitatives
      * Validation des critères objectifs
      * Contrôle qualité automatisé

10. **ValidationAgent**
    - Validation des livrables et conformité
    - Responsabilités:
      * Validation des spécifications
      * Vérification de la conformité
      * Mesures quantitatives
      * Validation des critères objectifs
      * Contrôle qualité automatisé

### Teams Management

#### Team Configurations
Teams are predefined agent groupings optimized for specific tasks:

1. **Book Writing Team**
   - Purpose: Content creation and documentation
   - Agents:
     * SpecificationsAgent - Content requirements
     * ManagementAgent - Project coordination
     * EvaluationAgent - Content evaluation
     * ChroniqueurAgent - Progress tracking
     * DocumentalisteAgent - Documentation structure
     * DuplicationAgent - Content redundancy check
     * RedacteurAgent - Content writing
     * ValidationAgent - Quality control

2. **Literature Review Team**
   - Purpose: Research and analysis
   - Agents:
     * SpecificationsAgent - Review scope
     * ManagementAgent - Review coordination
     * EvaluationAgent - Analysis evaluation
     * ChroniqueurAgent - Progress monitoring
     * DocumentalisteAgent - Source organization
     * DuplicationAgent - Duplicate detection
     * RedacteurAgent - Review writing
     * ValidationAgent - Review validation

3. **Coding Team**
   - Purpose: Software development
   - Agents:
     * SpecificationsAgent - Technical requirements
     * ManagementAgent - Project management
     * EvaluationAgent - Code evaluation
     * ChroniqueurAgent - Development tracking
     * DocumentalisteAgent - Technical documentation
     * DuplicationAgent - Code duplication check
     * ProductionAgent - Code generation
     * TesteurAgent - Testing
     * ValidationAgent - Code quality

#### Team Operations
- **Team-wide Controls**
  - Start/stop all team agents
  - Monitor team status
  - Track team efficiency
  - View team history

- **Agent-level Controls**
  - Individual agent start/stop
  - Status monitoring
  - Performance tracking
  - Error handling

- **Team Metrics**
  - Success rate
  - Response time
  - Completed tasks
  - Team efficiency score
  - Agent status summary

#### Team Interface
- Real-time status updates
- Visual status indicators
- Loading states for operations
- Tooltips with detailed information
- Team and agent-level controls
- Performance metrics display

#### Configuration des Agents
```python
base_config = {
    "check_interval": 100,
    "mission_name": "nom_mission",
    "logger": log_function,
    "web_instance": web_instance,
    "mission_dir": "chemin/relatif/mission"
}
```

#### Système de Fichiers
- Structure flexible par mission
- Pas de structure imposée aux agents
- Validation des permissions d'accès
- Utilisation de chemins relatifs
- Normalisation des noms de fichiers

### Gestion des Prompts et Configuration des Agents

#### Configuration des Agents
La configuration des agents est maintenant plus flexible et robuste :

1. **Structure de Configuration**
```json
{
    "check_interval": 100,
    "max_retries": 3,
    "timeout": 300,
    "cache_size": 1000,
    "file_patterns": ["*.md", "*.py", "*.js"],
    "ignore_patterns": [".git/*", "__pycache__/*"],
    "metrics": {
        "enabled": true,
        "collection_interval": 60
    },
    "recovery": {
        "enabled": true,
        "max_attempts": 3,
        "cooldown": 300
    }
}
```

2. **Hiérarchie de Configuration**
- Configuration par défaut dans le code
- Override via fichiers JSON dans `config/agents/<agent_name>.json`
- Validation automatique des valeurs
- Gestion des erreurs et fallbacks

3. **Validation de Configuration**
- Vérification des champs requis
- Validation des types de données
- Contraintes sur les valeurs numériques
- Logging des erreurs de validation

### Gestion des Prompts

#### Structure Simple
- Fichiers Markdown (*.md) stockés dans le dossier `prompts/`
- Format libre et flexible
- Pas de sections obligatoires
- Pas de validation structurelle

#### Organisation
- Un fichier prompt par agent : `prompts/<agent_name>.md`
- Exemple : `prompts/validation.md` pour ValidationAgent
- Contenu en texte brut, format Markdown
- Modifications possibles pendant l'exécution

#### Utilisation

1. **Création d'un Prompt**
- Créer un fichier .md dans le dossier `prompts/`
- Écrire les instructions en texte libre
- Sauvegarder avec le nom de l'agent

2. **Modification des Prompts**
- Édition directe via l'interface web
- Rechargement automatique par l'agent
- Pas de redémarrage nécessaire
- Conservation de l'historique des modifications

#### Bonnes Pratiques

1. **Rédaction**
- Être clair et concis
- Utiliser le Markdown pour la lisibilité
- Documenter le contexte si nécessaire
- Éviter les instructions contradictoires

2. **Maintenance**
- Garder les prompts à jour
- Documenter les changements majeurs
- Faire des sauvegardes régulières
- Tester les modifications importantes

#### Utilisation

1. **Configuration d'un Agent**
```bash
config/agents/validation_agent.json
```
```json
{
    "check_interval": 120,
    "max_retries": 5,
    "file_patterns": ["*.md", "*.py"],
    "metrics": {
        "enabled": true,
        "collection_interval": 30
    }
}
```

2. **Personnalisation d'un Prompt**
```bash
config/prompts/validation_agent_custom.json
```
```json
{
    "version": "1.0",
    "customizations": {
        "variables": {
            "check_depth": 3,
            "min_coverage": 80
        },
        "additional_sections": [
            {
                "title": "Validation Criteria",
                "content": "..."
            }
        ]
    }
}
```

#### Bonnes Pratiques

1. **Configuration**
- Utiliser des valeurs raisonnables par défaut
- Documenter les options de configuration
- Valider toutes les entrées utilisateur
- Prévoir des fallbacks en cas d'erreur

2. **Prompts**
- Maintenir une structure cohérente
- Utiliser des sections logiques
- Documenter les placeholders disponibles
- Tester les customisations

3. **Validation**
- Implémenter des contrôles stricts
- Logger les erreurs de validation
- Fournir des messages d'erreur clairs
- Maintenir la rétrocompatibilité

#### Points d'Extension

1. **Nouvelles Configurations**
- Ajouter des options dans le schéma JSON
- Implémenter la validation correspondante
- Mettre à jour la documentation
- Tester les nouvelles options

2. **Customisation des Prompts**
- Créer de nouveaux types de sections
- Ajouter des variables personnalisées
- Étendre le système de règles
- Supporter de nouveaux formats

3. **Validation Avancée**
- Ajouter des règles métier
- Implémenter des validations spécifiques
- Supporter des formats personnalisés
- Étendre les métriques de qualité

### Gestion des Chemins (PathManager)

#### Vue d'Ensemble
Le PathManager est un composant central qui gère tous les chemins de fichiers de manière cohérente et sécurisée :
- Normalisation des chemins entre systèmes d'exploitation
- Validation des accès et permissions
- Gestion des chemins temporaires et de cache
- Organisation des ressources du projet

#### Méthodes Principales

1. **Chemins de Base**
   ```python
   PathManager.get_project_root()  # Racine du projet
   PathManager.get_mission_path(mission_name)  # Dossier d'une mission
   PathManager.get_prompts_path()  # Dossier des prompts
   PathManager.get_config_path()  # Dossier de configuration
   ```

2. **Ressources Application**
   ```python
   PathManager.get_templates_path()  # Templates Flask
   PathManager.get_static_path()  # Fichiers statiques
   PathManager.get_logs_path()  # Fichiers de logs
   ```

3. **Fichiers Temporaires**
   ```python
   PathManager.get_temp_path()  # Dossier temp
   PathManager.get_temp_file(prefix="", suffix="")  # Fichier temporaire
   PathManager.get_backup_path()  # Dossier backups
   ```

4. **Fichiers Spécialisés**
   ```python
   PathManager.get_config_file_path(filename)  # Fichier config
   PathManager.get_static_file_path(filename)  # Fichier statique
   PathManager.get_log_file_path(log_type)  # Fichier log
   PathManager.get_cache_file_path(cache_key)  # Fichier cache
   ```

#### Utilisation par Service

1. **FileService**
   - Accès aux fichiers mission
   - Validation des chemins
   - Gestion des permissions
   ```python
   file_path = PathManager.get_mission_path(mission_name)
   if os.path.exists(file_path):
       # Opérations fichier...
   ```

2. **CacheService**
   - Organisation du cache
   - Fichiers temporaires
   - Nettoyage automatique
   ```python
   cache_file = PathManager.get_cache_file_path(key)
   temp_file = PathManager.get_temp_file()
   ```

3. **NotificationService**
   - Logs d'activité
   - Fichiers de suivi
   ```python
   log_path = PathManager.get_log_file_path('notifications')
   ```

4. **AgentService**
   - Prompts des agents
   - Fichiers de travail
   ```python
   prompt_path = PathManager.get_prompts_path()
   work_dir = PathManager.get_mission_path(mission)
   ```

#### Bonnes Pratiques

1. **Validation des Chemins**
   ```python
   # Toujours utiliser normalize_path pour les entrées externes
   safe_path = PathManager.normalize_path(user_input)
   if not safe_path.startswith(PathManager.get_project_root()):
       raise SecurityError("Invalid path")
   ```

2. **Gestion des Erreurs**
   ```python
   try:
       path = PathManager.get_mission_path(mission_name)
   except ValueError as e:
       logger.error(f"Invalid mission path: {e}")
   ```

3. **Organisation des Fichiers**
   ```python
   # Structure recommandée
   project_root/
   ├── missions/
   ├── prompts/
   ├── config/
   ├── templates/
   ├── static/
   ├── logs/
   └── temp/
   ```

#### Sécurité

1. **Validation des Accès**
   - Vérification des permissions
   - Prévention des traversées de répertoire
   - Normalisation des chemins

2. **Isolation des Ressources**
   - Séparation des dossiers temporaires
   - Gestion des backups
   - Nettoyage automatique

3. **Audit et Logging**
   - Traçage des accès fichiers
   - Détection des anomalies
   - Historique des opérations

#### Configuration

1. **Variables d'Environnement**
   ```env
   PROJECT_ROOT=/path/to/project
   TEMP_DIR=/path/to/temp
   LOG_DIR=/path/to/logs
   ```

2. **Paramètres Ajustables**
   ```python
   TEMP_FILE_PREFIX = "kinos_"
   BACKUP_RETENTION = 30  # jours
   CACHE_CLEANUP_INTERVAL = 3600  # secondes
   ```

#### Extensibilité

1. **Ajout de Nouveaux Types**
   ```python
   @staticmethod
   def get_custom_path(name: str) -> str:
       """Get path for custom resource type"""
       return os.path.join(PathManager.get_project_root(), "custom", name)
   ```

2. **Validation Personnalisée**
   ```python
   @staticmethod
   def validate_custom_path(path: str) -> bool:
       """Add custom path validation rules"""
       return PathManager.normalize_path(path).startswith(
           PathManager.get_custom_path("")
       )
   ```

### Service Layer

#### BaseService
Base class providing common functionality for all services:

Core Features:
- Dependency injection via constructor
- Standardized error handling with retry policies
- Input validation with custom rules
- Unified logging system with levels
- Thread-safe file operations via portalocker
- Multi-level cache management (Memory, Redis, Session)
- Performance metrics collection
- Resource cleanup
- Service lifecycle management
- Circuit breaker pattern implementation
- Configurable retry policies
- Distributed locking with Redis

Error Handling:
- Exception capture and logging
- Standardized error formatting
- Configurable automatic retries
- Default value fallbacks
- Controlled error propagation
- Resource cleanup on errors
- Circuit breaker pattern
- Error metrics collection
- Configurable alerting
- Automatic recovery

Inherited Methods:
- _validate_input() - Input validation
- _handle_error() - Error management
- _log_operation() - Unified logging
- _safe_file_operation() - File operations
- _ensure_directory() - Directory management
- cleanup() - Resource cleanup

Input Validation:
- Type checking
- Format validation
- Custom constraints
- Detailed error messages
- Data sanitization

Standardized Logging:
- Configurable log levels
- File rotation
- Unified format
- Execution context
- Performance metrics

Thread-safe File Operations:
- portalocker integration
- Configurable timeouts
- Automatic retries
- Cleanup handlers
- Path validation

Cache and Optimization:
- LRU memory cache
- Smart invalidation
- Configurable preloading
- Usage metrics
- Periodic cleanup

Automatic Retries:
- Configurable policies
- Exponential backoff
- Custom conditions
- Attempt limits
- Retry logging
- Configurable retry policies
- Distributed locking with Redis

Error Handling:
- Exception capture and logging
- Standardized error formatting
- Configurable automatic retries
- Default value fallbacks
- Controlled error propagation
- Resource cleanup on errors
- Circuit breaker pattern
- Error metrics collection
- Configurable alerting
- Automatic recovery

Inherited Methods:
- _validate_input() - Input validation
- _handle_error() - Error management
- _log_operation() - Unified logging
- _safe_file_operation() - File operations
- _ensure_directory() - Directory management
- cleanup() - Resource cleanup

Input Validation:
- Type checking
- Format validation
- Custom constraints
- Detailed error messages
- Data sanitization

Standardized Logging:
- Configurable log levels
- File rotation
- Unified format
- Execution context
- Performance metrics

Thread-safe File Operations:
- portalocker integration
- Configurable timeouts
- Automatic retries
- Cleanup handlers
- Path validation

Cache and Optimization:
- LRU memory cache
- Smart invalidation
- Configurable preloading
- Usage metrics
- Periodic cleanup

Automatic Retries:
- Configurable policies
- Exponential backoff
- Custom conditions
- Attempt limits
- Retry logging

Key features:
- Dependency injection via constructor
- Standardized error handling patterns
- Centralized logging
- Resource cleanup
- Service lifecycle management

#### Service Interactions
Services communicate through:
- Direct method calls with dependency injection
- Event system for async operations
- Shared caching layer
- Coordinated file access

### Notification System

#### Real-time Notifications
Architecture:
- Dedicated NotificationService with thread-safe queue
- WebSocket real-time updates with fallback polling
- Publish/subscribe system with Redis backend
- Configurable WebSocket heartbeat and reconnection
- Real-time metrics and monitoring
- Message prioritization and batching
- Automatic message expiration (TTL)
- Backpressure handling
- Guaranteed message delivery
- Message deduplication

Message Queue:
- Thread-safe queue implementation
- Configurable priorities
- Smart batching
- Message timeouts
- Automatic retries
- Performance metrics
- Periodic cleanup
- Optional persistence
- FIFO guarantee
- Backpressure handling

Notification Types:
- Info: General information
- Success: Operation completed
- Warning: Potential issues
- Error: Operation failed
- Flash: Ephemeral notifications
- Status: Agent state changes
- Content: File modifications
- System: Infrastructure events
- Validation: Validation results and metrics

Smart Content Cache:
- LRU memory cache
- Timestamp-based invalidation
- Adaptive preloading
- Data compression
- Configurable limits
- Usage metrics

Change Distribution:
- WebSocket notifications
- Optimized polling
- Type filtering
- Smart aggregation
- Order preservation
- Error handling

State Management:
- Atomic states
- Validated transitions
- Change history
- Error recovery
- Stability metrics
- Configurable alerts

#### Message Types
- Info: General information
- Success: Operation completed
- Warning: Potential issues
- Error: Operation failed
- Status: Agent state changes
- Content: File modifications
- System: Infrastructure events
- Validation: Validation results and metrics

#### Distribution
- WebSocket real-time updates
- Optimized polling fallback
- Message aggregation
- Ordered delivery
- Error recovery

### Cache System

#### Multi-level Cache
Cache Layers:
- LRU memory cache with configurable size
- Redis distributed cache with TTL
- Session cache for user data
- Prompt cache with invalidation
- Content cache with timestamps
- File system cache with locking
- Metadata cache for quick lookups
- Agent state cache
- Configuration cache
- Route cache for API responses
- Validation cache for metrics
- Validation cache for metrics

Invalidation Strategies:
- Timestamp-based
- Dependency-based
- Event-driven
- Cascade invalidation
- Smart preloading

Configuration:
- Per-level size limits
- Configurable TTL
- Eviction policies
- Data compression
- Usage metrics

Distributed Locking:
- portalocker for files
- Redis locks for cache
- Configurable timeouts
- Automatic retries
- Deadlock detection

#### Invalidation Strategies
- Time-based (TTL)
- Event-based
- Dependency tracking
- Cascade invalidation
- Manual purge

#### File Locking
- portalocker integration
- Configurable timeouts
- Automatic retry
- Deadlock prevention
- Lock inheritance

### Error Management

#### Centralized Error Handling
- Global error interceptors with retry policies
- Custom exception hierarchy with error codes
- Contextual error details and stack traces
- Automatic recovery strategies
- Error aggregation and reporting
- Circuit breaker pattern
- Error rate monitoring
- Configurable alerting
- Error response formatting
- Validation error handling

#### Retry Policies
- Exponential backoff
- Maximum attempts
- Retry conditions
- Timeout handling
- Circuit breaker

#### Exception Hierarchy
- KinOSError (base)
- ValidationError
- ResourceNotFoundError
- ServiceError
- AgentError
- FileOperationError

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend development)
- API keys for Anthropic and OpenAI
- portalocker (for thread-safe file locking)
- Aider CLI tool installed and configured

### Core Components

#### BaseService
Base class providing common functionality for all services:
- Error handling with configurable retry policies
- Input validation with custom rules
- Standardized logging with levels
- Thread-safe file operations via portalocker
- Cache management with invalidation
- Performance metrics collection

#### File Locking System
Uses portalocker for thread-safe file operations:
- Configurable timeouts via FILE_LOCK_TIMEOUT
- Automatic retry on lock failure
- Lock cleanup on process exit
- Deadlock prevention
- File access coordination between agents

#### Cache System
Multi-level caching strategy:
- Memory cache with LRU eviction
- File content caching with timestamps
- Prompt caching per agent
- Cache invalidation on file changes
- Configurable cleanup via CACHE_CLEANUP_INTERVAL

#### Error Handling
Centralized error management via ErrorHandler:
- Custom exception hierarchy (KinOSError base)
- Automatic retries with @safe_operation decorator
- Detailed error logging with stack traces
- Error aggregation and reporting
- Circuit breaker pattern implementation

### System Requirements
- 4GB RAM minimum
- 2 CPU cores minimum
- 1GB free disk space
- Network access for API calls

### Environment Variables
Required in `.env`:
```env
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Server Configuration
DEBUG=True/False
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=["http://localhost:8000"]
RATE_LIMIT="1000 per minute"
COMPRESS_RESPONSES=True
SESSION_SECRET=your_secret_here

# File Operations
FILE_LOCK_TIMEOUT=10
MAX_FILE_SIZE=10485760
LOCK_CHECK_INTERVAL=100
LOCK_RETRY_COUNT=3
LOCK_RETRY_DELAY=1.0
FILE_ENCODING="utf-8"

# Cache Settings
CACHE_DURATION=3600
CACHE_CLEANUP_INTERVAL=300
CONTENT_CACHE_SIZE=1000
CACHE_STRATEGY="lru"
REDIS_URL=optional_redis_url
CACHE_COMPRESSION=True

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
ERROR_RETRY_CODES=[408,429,500,502,503,504]
CIRCUIT_BREAKER_THRESHOLD=5
ERROR_COOLDOWN=300
ALERT_ON_ERROR=True

# Notifications
NOTIFICATION_QUEUE_SIZE=500
NOTIFICATION_BATCH_SIZE=50
NOTIFICATION_TIMEOUT=5
WEBSOCKET_HEARTBEAT=30
MESSAGE_TTL=3600
PRIORITY_LEVELS=["high","medium","low"]

# Logging
LOG_info
LOG_FORMAT="[%(asctime)s] [%(levelname)s] %(message)s"
LOG_FILE="kinos.log"
LOG_ROTATION="1 day"
LOG_BACKUP_COUNT=7

# Monitoring
ENABLE_METRICS=True
PROMETHEUS_PORT=9090
TRACE_REQUESTS=True
PROFILE_ENDPOINTS=False

# Security
JWT_SECRET=your_jwt_secret
JWT_EXPIRE=3600
SECURE_COOKIES=True
CSRF_PROTECTION=True
CORS_ORIGINS=["http://localhost:8000"]
RATE_LIMIT="1000 per minute"
COMPRESS_RESPONSES=True
SESSION_SECRET=your_secret_here

# File Operations
FILE_LOCK_TIMEOUT=10
MAX_FILE_SIZE=10485760
LOCK_CHECK_INTERVAL=100
LOCK_RETRY_COUNT=3
LOCK_RETRY_DELAY=1.0
FILE_ENCODING="utf-8"

# Cache Settings
CACHE_DURATION=3600
CACHE_CLEANUP_INTERVAL=300
CONTENT_CACHE_SIZE=1000
CACHE_STRATEGY="lru"
REDIS_URL=optional_redis_url
CACHE_COMPRESSION=True

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
ERROR_RETRY_CODES=[408,429,500,502,503,504]
CIRCUIT_BREAKER_THRESHOLD=5
ERROR_COOLDOWN=300
ALERT_ON_ERROR=True

# Notifications
NOTIFICATION_QUEUE_SIZE=500
NOTIFICATION_BATCH_SIZE=50
NOTIFICATION_TIMEOUT=5
WEBSOCKET_HEARTBEAT=30
MESSAGE_TTL=3600
PRIORITY_LEVELS=["high","medium","low"]

# Logging
LOG_info
LOG_FORMAT="[%(asctime)s] [%(levelname)s] %(message)s"
LOG_FILE="kinos.log"
LOG_ROTATION="1 day"
LOG_BACKUP_COUNT=7

# Monitoring
ENABLE_METRICS=True
PROMETHEUS_PORT=9090
TRACE_REQUESTS=True
PROFILE_ENDPOINTS=False

# Security
JWT_SECRET=your_jwt_secret
JWT_EXPIRE=3600
SECURE_COOKIES=True
CSRF_PROTECTION=True
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
  - Response: `{ "agent_name": { "running": bool, "last_run": timestamp } }`
  - Errors: 500 Internal Server Error

- POST `/api/agents/start` - Start all agents
  - Response: `{ "status": "started" }`
  - Errors: 500 Internal Server Error

- POST `/api/agents/stop` - Stop all agents
  - Response: `{ "status": "stopped" }`
  - Errors: 500 Internal Server Error

- GET `/api/agent/<id>/prompt` - Get agent prompt
  - Response: `{ "prompt": "prompt content" }`
  - Errors: 404 Not Found, 500 Internal Server Error

- POST `/api/agent/<id>/prompt` - Update agent prompt
  - Request: `{ "prompt": "new prompt content" }`
  - Response: `{ "status": "success" }`
  - Errors: 400 Bad Request, 404 Not Found, 500 Internal Server Error

- POST `/api/agent/<id>/<action>` - Control individual agent
  - Actions: "start", "stop"
  - Response: `{ "status": "success" }`
  - Errors: 400 Bad Request, 404 Not Found, 500 Internal Server Error

- GET `/api/agent/<id>/logs` - Get agent operation logs
  - Response: Array of log entries with timestamps
  - Errors: 404 Not Found, 500 Internal Server Error

- PUT `/api/agent/<id>/config` - Update agent configuration
  - Request: Configuration object
  - Response: `{ "status": "success" }`
  - Errors: 400 Bad Request, 404 Not Found, 500 Internal Server Error

#### Notification Routes
- GET `/api/notifications` - Get pending notifications
- POST `/api/notifications` - Send new notification
- GET `/api/changes` - Get content changes stream

#### Mission Routes
- GET `/api/missions` - List all missions
- POST `/api/missions` - Create new mission
- GET `/api/missions/<id>` - Get mission details
- GET `/api/missions/<id>/content` - Get mission content
- POST `/api/missions/<id>/reset` - Reset mission files
- POST `/api/missions/<id>/test-data` - Load test data
- PUT `/api/missions/<id>` - Update mission

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

#### DocumentalisteAgent
Agent responsable de la cohérence entre code et documentation.

Responsabilités:
- Analyse de la documentation existante
- Détection des incohérences avec le code
- Mise à jour automatique de la documentation
- Maintien de la qualité documentaire
- Validation des références croisées
- Vérification des exemples de code
- Génération de documentation manquante

Configuration:
```python
{
    "name": "Documentaliste",
    "prompt_file": "prompts/documentaliste.md",
    "check_interval": 300,
    "file_patterns": ["*.md", "*.py", "*.js"]
}
```

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
- Redis server (optional, for distributed cache)

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
CORS_ORIGINS=["http://localhost:8000"]
RATE_LIMIT="1000 per minute"
COMPRESS_RESPONSES=True
SESSION_SECRET=your_secret_here

# File Operations
FILE_LOCK_TIMEOUT=10
MAX_FILE_SIZE=10485760
LOCK_CHECK_INTERVAL=100
LOCK_RETRY_COUNT=3
LOCK_RETRY_DELAY=1.0
FILE_ENCODING="utf-8"

# Cache Settings
CACHE_DURATION=3600
CACHE_CLEANUP_INTERVAL=300
CONTENT_CACHE_SIZE=1000
CACHE_STRATEGY="lru"
REDIS_URL=optional_redis_url
CACHE_COMPRESSION=True

# Error Handling
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
ERROR_RETRY_CODES=[408,429,500,502,503,504]
CIRCUIT_BREAKER_THRESHOLD=5
ERROR_COOLDOWN=300
ALERT_ON_ERROR=True

# Notifications
NOTIFICATION_QUEUE_SIZE=500
NOTIFICATION_BATCH_SIZE=50
NOTIFICATION_TIMEOUT=5
WEBSOCKET_HEARTBEAT=30
MESSAGE_TTL=3600
PRIORITY_LEVELS=["high","medium","low"]

# Logging
LOG_info
LOG_FORMAT="[%(asctime)s] [%(levelname)s] %(message)s"
LOG_FILE="kinos.log"
LOG_ROTATION="1 day"
LOG_BACKUP_COUNT=7

# Monitoring
ENABLE_METRICS=True
PROMETHEUS_PORT=9090
TRACE_REQUESTS=True
PROFILE_ENDPOINTS=False

# Security
JWT_SECRET=your_jwt_secret
JWT_EXPIRE=3600
SECURE_COOKIES=True
CSRF_PROTECTION=True
```

### Installation
1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and configure API keys
5. Run `python kinos_web.py`

## User Guide

### 1. Core Application
- `kinos_web.py`
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

    * ChroniqueurAgent
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
  - `/agents` : Gestion des agents

### 5. Interface Utilisateur
- `templates/`
  - `base.html` : Template parent
  - `agents.html` : Vue des agents

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
    - `KinOSError`: Exception de base
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
4. Register in `KinOSWeb`
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
