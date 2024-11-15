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
   - Current directory as mission context
   - Minimal dependencies

3. **File System**
   - Current directory as mission context
   - Dynamic path validation
   - Thread-safe file operations
   - Automatic backup handling
   - Permission validation
   - Resource cleanup
   - No complex configuration needed

4. **Services Layer**
   - Minimal dependencies
   - Team management
   - Agent coordination
   - File operations
   - Path validation
   - Error handling
   - Resource management
   - Simple initialization

### Key Features

1. **Simplicity**
   - Zero configuration required
   - Current directory = mission context
   - Single command operation
   - Automatic team selection
   - Graceful error handling
   - Minimal dependencies
   - No web instance required
   - Direct file system access

2. **Autonomy**
   - Self-managing agents
   - Dynamic resource allocation
   - Automatic recovery
   - Smart scheduling
   - Independent operation
   - Local file system based
   - No external dependencies

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

### Claude Integration System

#### Overview
Le système d'intégration avec Claude-3 permet une interaction sophistiquée et contextuelle entre les agents et le modèle. Chaque agent utilise Claude pour :
- Analyser le contexte du projet
- Générer des instructions précises
- Guider les modifications de code

#### Architecture

1. **Collecte de Contexte**
   ```python
   {
       "system": "Prompt spécifique à l'agent",
       "chat_history": "Historique des interactions",
       "files_context": {
           "file1.py": "contenu...",
           "file2.md": "contenu..."
       }
   }
   ```

2. **Structure des Messages**
   - Message système : Définit le rôle et les responsabilités
   - Message assistant : Contient l'historique des interactions
   - Message utilisateur : Demande d'analyse et instructions

3. **Format de Prompt**
   ```
   Based on:
   1. The system prompt defining my role
   2. The chat history showing previous actions
   3. The current state of project files

   Choose ONE specific task and explain it in detail.
   ```

#### Workflow

1. **Préparation du Contexte**
   - Lecture de l'historique des chats
   - Collection des fichiers pertinents
   - Formatage du contexte

2. **Appel à Claude**
   ```python
   response = client.messages.create(
       model="claude-3-haiku-20240307",
       max_tokens=4000,
       messages=[...]
   )
   ```

3. **Traitement de la Réponse**
   - Validation des instructions
   - Formatage pour Aider
   - Exécution des modifications

#### Avantages

1. **Contextuel**
   - Compréhension complète du projet
   - Prise en compte de l'historique
   - Décisions informées

2. **Précis**
   - Instructions détaillées
   - Tâches concrètes
   - Modifications ciblées

3. **Adaptatif**
   - Ajustement aux changements
   - Apprentissage continu
   - Optimisation progressive

#### Configuration

1. **Modèle**
   ```python
   MODEL_CONFIG = {
       "name": "claude-3-haiku-20240307",
       "max_tokens": 4000,
       "temperature": 0.7
   }
   ```

2. **Format des Messages**
   ```python
   messages = [
       {
           "role": "system",
           "content": prompt
       },
       {
           "role": "assistant",
           "content": chat_history
       },
       {
           "role": "user",
           "content": f"Based on: ..."
       }
   ]
   ```

#### Bonnes Pratiques

1. **Gestion du Contexte**
   - Limiter la taille du contexte
   - Prioriser les fichiers pertinents
   - Nettoyer l'historique régulièrement

2. **Prompts**
   - Être spécifique et concis
   - Définir clairement les objectifs
   - Inclure les contraintes importantes

3. **Traitement des Réponses**
   - Valider avant exécution
   - Logger les modifications
   - Gérer les erreurs gracieusement

#### Intégration avec les Agents

1. **Dans AiderAgent**
   ```python
   def run(self):
       # Collecte du contexte
       chat_history = self._get_chat_history()
       files_context = self._get_files_context()
       
       # Appel à Claude
       instructions = self._get_claude_instructions(
           chat_history, 
           files_context
       )
       
       # Exécution avec Aider
       self._run_aider(instructions)
   ```

2. **Dans ResearchAgent**
   ```python
   def _run_aider(self, prompt: str):
       # Génération de requête
       query = self.generate_query(prompt)
       results = self.execute_query(query)
       
       # Formatage pour Aider
       return self._format_research_results(results)
   ```

#### Monitoring et Logging

1. **Métriques**
   - Temps de réponse
   - Taux de succès
   - Utilisation de tokens
   - Qualité des modifications

2. **Logs**
   - Instructions générées
   - Modifications effectuées
   - Erreurs et retries
   - Performance globale

Cette architecture permet une interaction sophistiquée et efficace entre les agents et Claude, assurant des modifications de code précises et contextuelles.

### Weight System

#### Vue d'Ensemble
Le système de poids permet d'ajuster dynamiquement l'importance et le comportement des agents selon la phase du projet et le contexte d'exécution.

### Research Agent

#### Vue d'Ensemble
Le ResearchAgent est un agent spécialisé qui utilise l'API Perplexity pour effectuer des recherches ciblées et enrichir le projet avec des références académiques.

#### Architecture

1. **Workflow Principal**
   ```mermaid
   graph TD
      A[Analyse du Contenu] --> B[Extraction des Topics]
      B --> C[Génération des Requêtes]
      C --> D[Exécution via Perplexity]
      D --> E[Sauvegarde des Résultats]
      E --> F[Intégration dans le Projet]
   ```

2. **Composants Clés**
   - Extracteur de topics avec Claude
   - Générateur de requêtes optimisées
   - Client Perplexity avec rate limiting
   - Système de cache des résultats
   - Gestionnaire de données de recherche

#### Fonctionnalités

1. **Extraction de Topics**
   ```python
   def extract_research_topics(self, content: str) -> List[str]:
       """
       Analyse le contenu pour identifier les besoins de recherche
       
       Utilise Claude pour:
       - Analyser le contexte du projet
       - Identifier les questions clés
       - Prioriser les besoins de recherche
       """
   ```

2. **Génération de Requêtes**
   ```python
   def generate_query(self, topic: str) -> str:
       """
       Optimise les topics pour l'API Perplexity
       
       - Reformulation en questions précises
       - Ajout de qualificateurs académiques
       - Focus sur les sources vérifiées
       - Demande d'exemples spécifiques
       """
   ```

3. **Exécution des Recherches**
   ```python
   def execute_query(self, query: str) -> Optional[Dict[str, Any]]:
       """
       Exécute les requêtes avec gestion avancée
       
       - Rate limiting intelligent
       - Cache des résultats
       - Retry sur erreur
       - Validation des réponses
       """
   ```

#### Gestion des Données

1. **Structure de Stockage**
   ```python
   research_data = {
       "timestamp": "2024-03-21T15:30:45",
       "topic": "Topic de recherche",
       "query": "Requête optimisée",
       "results": {
           "sources": [...],
           "findings": [...],
           "citations": [...]
       }
   }
   ```

2. **Format des Résultats**
   ```python
   def _format_research_results(self, results: List[Dict]) -> str:
       """
       Formate les résultats pour Aider
       
       Structure:
       - Topic et contexte
       - Résultats principaux
       - Citations et références
       - Suggestions d'intégration
       """
   ```

#### Intégration avec Aider

1. **Préparation du Prompt**
   ```python
   def _build_prompt(self, research_results: Dict) -> str:
       """
       Crée un prompt pour Aider avec:
       - Contexte de la recherche
       - Résultats pertinents
       - Suggestions d'intégration
       - Format des citations
       """
   ```

2. **Exécution des Modifications**
   ```python
   def _run_aider(self, prompt: str) -> Optional[str]:
       """
       Intègre les résultats de recherche via Aider
       
       - Identifie les points d'insertion
       - Formate les citations
       - Maintient la cohérence
       - Valide les modifications
       """
   ```

#### Configuration

1. **API Perplexity**
   ```json
   {
       "api_key": "",
       "default_params": {
           "max_tokens": 1000,
           "temperature": 0.7,
           "model": "pplx-7b-online"
       },
       "rate_limits": {
           "queries_per_minute": 10,
           "queries_per_hour": 100
       },
       "retry_config": {
           "max_retries": 3,
           "delay_seconds": 1,
           "backoff_factor": 2
       }
   }
   ```

2. **Prompt de Recherche**
   ```markdown
   # Research Agent

   ## MISSION
   Analyze content to identify research needs and collect academic references.

   ## CONTEXT
   - Project state and requirements
   - Current documentation gaps
   - Research priorities

   ## INSTRUCTIONS
   1. Analyze content for research needs
   2. Generate optimized queries
   3. Execute targeted research
   4. Format and integrate findings

   ## RULES
   - Prioritize verified sources
   - Maintain academic standards
   - Ensure proper citations
   - Respect API limits
   ```

#### Bonnes Pratiques

1. **Recherche**
   - Formuler des requêtes précises
   - Prioriser les sources académiques
   - Valider la pertinence
   - Éviter la duplication

2. **Intégration**
   - Citations standardisées
   - Contexte approprié
   - Liens avec le contenu existant
   - Documentation des sources

3. **Performance**
   - Cache intelligent
   - Rate limiting adaptatif
   - Optimisation des requêtes
   - Monitoring des ressources

#### Métriques

1. **Performance**
   - Taux de succès des requêtes
   - Temps de réponse moyen
   - Utilisation du cache
   - Qualité des résultats

2. **Impact**
   - Citations ajoutées
   - Améliorations documentaires
   - Couverture des topics
   - Feedback utilisateur

#### Gestion des Erreurs

1. **Stratégies de Retry**
   ```python
   @retry(max_attempts=3, delay=1.0, backoff=2.0)
   def execute_query(self, query: str):
       """
       Exécution avec retry intelligent:
       - Délai exponentiel
       - Validation des réponses
       - Logging détaillé
       - Circuit breaker
       """
   ```

2. **Validation des Résultats**
   ```python
   def validate_research_results(self, results: Dict) -> bool:
       """
       Vérifie la qualité des résultats:
       - Présence de sources
       - Pertinence du contenu
       - Format des citations
       - Cohérence globale
       """
   ```

Cette documentation fournit une vue complète du ResearchAgent, de son architecture à son utilisation pratique, en passant par sa configuration et ses bonnes pratiques.

#### Architecture

1. **Configuration des Poids**
   ```json
   {
     "phase_config": {
       "expansion": {
         "active_agents": [
           {"name": "specifications", "weight": 0.9},
           {"name": "production", "weight": 0.8},
           {"name": "chroniqueur", "weight": 0.5}
         ]
       },
       "convergence": {
         "active_agents": [
           {"name": "validation", "weight": 0.9},
           {"name": "duplication", "weight": 0.8},
           {"name": "documentaliste", "weight": 0.7}
         ]
       }
     }
   }
   ```

2. **Impact des Poids**
   - Intervalle d'exécution : Plus le poids est élevé, plus l'agent s'exécute fréquemment
   - Priorité des tâches : Influence l'ordre d'exécution des agents
   - Allocation des ressources : Affecte le temps CPU et les tokens alloués
   - Seuils de décision : Module les critères de prise de décision

#### Calcul des Intervalles

```python
def calculate_dynamic_interval(self) -> float:
    """Calculate dynamic interval based on weight and activity"""
    base_interval = self.check_interval
    min_interval = 60  # Minimum 1 minute
    max_interval = 3600  # Maximum 1 hour
    
    # Get effective weight for current phase
    weight = self.get_effective_weight()
    
    # Calculate multiplier based on activity and weight
    if self.consecutive_no_changes > 0:
        multiplier = min(10, 1.5 ** min(5, self.consecutive_no_changes))
        
        # Apply weight - higher weight means shorter interval
        weight_factor = 2 - weight  # Convert 0-1 weight to 1-2 range
        multiplier *= weight_factor
        
        interval = base_interval * multiplier
        return max(min_interval, min(max_interval, interval))
    
    # Apply weight to base interval
    weight_factor = 2 - weight
    interval = base_interval * weight_factor
    return max(min_interval, min(max_interval, interval))
```

#### Phases et Poids

1. **Phase EXPANSION** (< 60% tokens)
   - Agents de création prioritaires
     * SpecificationsAgent: 0.9
     * ProductionAgent: 0.8
     * ChroniqueurAgent: 0.5
   - Focus sur la génération de contenu
   - Intervalles courts pour développement rapide

2. **Phase CONVERGENCE** (> 60% tokens)
   - Agents d'optimisation prioritaires
     * ValidationAgent: 0.9
     * DuplicationAgent: 0.8
     * DocumentalisteAgent: 0.7
   - Focus sur la qualité et l'optimisation
   - Intervalles plus longs pour analyse approfondie

#### Ajustement Dynamique

1. **Facteurs d'Ajustement**
   - Poids de base de l'agent
   - Phase actuelle du projet
   - Historique des modifications
   - Taux de succès
   - Utilisation des ressources

2. **Formule de Calcul**
   ```python
   effective_weight = base_weight * phase_multiplier * success_rate
   ```

#### Métriques et Monitoring

1. **Métriques par Agent**
   - Temps entre exécutions
   - Taux de modifications réussies
   - Utilisation des ressources
   - Impact des modifications

2. **Métriques Globales**
   - Distribution des poids
   - Équilibre des activités
   - Efficacité du système
   - Progression du projet

#### Configuration

1. **Par Équipe**
   ```json
   {
     "team": "coding",
     "phase_weights": {
       "expansion": {
         "production": 0.9,
         "testeur": 0.7
       },
       "convergence": {
         "validation": 0.9,
         "duplication": 0.8
       }
     }
   }
   ```

2. **Par Agent**
   ```python
   agent_config = {
     "name": "production",
     "type": "aider",
     "weight": 0.8,
     "min_interval": 60,
     "max_interval": 3600
   }
   ```

#### Bonnes Pratiques

1. **Configuration des Poids**
   - Adapter les poids aux objectifs de phase
   - Maintenir une somme cohérente
   - Éviter les changements brusques
   - Documenter les ajustements

2. **Monitoring**
   - Surveiller l'impact des poids
   - Ajuster selon les métriques
   - Valider l'efficacité
   - Optimiser la distribution

3. **Optimisation**
   - Analyser les patterns d'exécution
   - Identifier les goulots d'étranglement
   - Ajuster les seuils dynamiquement
   - Maintenir l'équilibre global

#### Intégration

1. **Dans TeamService**
   ```python
   def get_phase_weights(self, phase: str) -> Dict[str, float]:
       """Get agent weights for current phase"""
       phase_config = self.team_config['phase_config'][phase]
       return {
           agent['name']: agent['weight']
           for agent in phase_config['active_agents']
       }
   ```

2. **Dans AgentService**
   ```python
   def calculate_effective_weight(self, agent_name: str) -> float:
       """Calculate effective weight based on phase and performance"""
       base_weight = self.get_agent_weight(agent_name)
       phase_multiplier = self.get_phase_multiplier()
       return base_weight * phase_multiplier
   ```

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
   cat "map.md"
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

#### Phase-Based Agent Execution
Each team's agents are activated or deactivated based on the current project phase:

1. **EXPANSION Phase** (< 60% tokens)
   - Focus on content creation and development
   - Active agents prioritize:
     * Specifications and planning
     * Content production
     * Initial documentation
     * Progress tracking
   - Example: In coding team, ProductionAgent and TesteurAgent are most active

2. **CONVERGENCE Phase** (> 60% tokens)
   - Focus on optimization and refinement
   - Active agents prioritize:
     * Code/content optimization
     * Duplication detection
     * Quality validation
     * Documentation consolidation
   - Example: In coding team, DuplicationAgent and ValidationAgent take priority

The phase system automatically manages which agents run based on token usage:
- Each team defines phase-specific agent lists in its config
- Agents check their activation status before each run
- Smooth transitions as phases change
- Automatic workload optimization

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
     * Retry automatique
     * Détection deadlocks

4. Verrouillage Fichiers
   - Utilisation de portalocker
   - Recovery automatique
   - Prévention des conflits

### Map System

Le MapService est un composant central qui :
- Génère une vue d'ensemble structurée du projet
- Surveille la taille des documents en tokens
- Fournit des alertes visuelles (✓, ⚠️, 🔴)
- Met à jour automatiquement la map après chaque modification

#### Seuils de Taille
- ✓ OK : < 6k tokens
- ⚠️ Long : > 6k tokens 
- 🔴 Trop long : > 12k tokens

### Phase System
Le système de phases optimise l'utilisation des ressources :

- **EXPANSION** (< 60% tokens)
  * Création libre de contenu
  * Développement de nouvelles fonctionnalités
  * Documentation extensive

- **CONVERGENCE** (> 60% tokens)
  * Optimisation du contenu existant
  * Réduction de la duplication
  * Consolidation des documents

Seuils :
- Limite totale : 128k tokens
- CONVERGENCE : > 76.8k tokens (60%)
- Retour EXPANSION : < 64k tokens (50%)

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
   - Pooling de connexions
   - Compression des réponses
   - Lazy loading des ressources
   - Minification des assets
