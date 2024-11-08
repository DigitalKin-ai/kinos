# Architecture Parallagon

## Overview

The Parallagon system uses a modular architecture built around autonomous agents that collaborate through a shared file system. The core components are:

- Web Application (Flask)
- Autonomous Agents
- Service Layer
- File System
- Real-time Notifications

## Component Architecture

### Core
- `parallagon_web.py` - Classe principale de l'application
  - Initialisation de Flask
  - Configuration des routes
  - Gestion des services
  - Gestion des erreurs

### Agents
- `aider_agent.py` - Agent de base utilisant Aider
  - Classe de base pour tous les agents
  - Gestion des prompts
  - Exécution des commandes Aider
  - Surveillance des fichiers

- `agents.py` - Implémentations spécifiques des agents
  - SpecificationsAgent
  - ProductionAgent
  - ManagementAgent
  - EvaluationAgent
  - SuiviAgent

### Services
- `services/base_service.py` - Classe de base pour tous les services
  - Gestion des erreurs
  - Validation des entrées
  - Logging
  - Opérations fichiers

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
  - ParallagonError
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

### Frontend
- `static/js/`
  - `agent-manager.js` - Gestion UI des agents
  - `mission-selector.js` - Sélection des missions
  - `mission-service.js` - Service frontend missions

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
  - Variables d'environnement
  - Clés API
  - Paramètres de debug

## Flux de Données

1. Interface utilisateur
   - Interactions via les routes view
   - Appels API via les routes API
   - Notifications temps réel

2. Services
   - Traitement des requêtes
   - Gestion de l'état
   - Communication avec les agents

3. Agents
   - Surveillance des fichiers
   - Exécution des tâches
   - Mise à jour du contenu

4. Système de fichiers
   - Organisation par mission
   - Fichiers spécifiques par agent
   - Logs et données temporaires

## Points d'Extension

1. Nouveaux Agents
   - Hériter de AiderAgent
   - Implémenter la logique spécifique
   - Ajouter les routes nécessaires

2. Nouveaux Services
   - Hériter de BaseService
   - Implémenter les opérations CRUD
   - Ajouter la gestion d'erreurs

3. Nouvelles Fonctionnalités UI
   - Ajouter les composants Vue.js
   - Créer les routes API
   - Mettre à jour les templates

## Sécurité et Performance

1. Validation des Entrées
   - Décorateurs de validation
   - Middleware de sécurité
   - Sanitization des données

2. Gestion des Erreurs
   - Logging centralisé
   - Réponses formatées
   - Recovery automatique

3. Optimisation
   - Cache de contenu
   - Rate limiting
   - Pooling de connexions
