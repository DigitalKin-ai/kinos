# Project Map

Ce document est une carte dynamique du projet qui est automatiquement mise à jour pour fournir une vue d'ensemble de la structure et de l'état du projet. Il surveille notamment :
- L'arborescence complète des fichiers
- La taille de chaque document en tokens
- La phase actuelle du projet (EXPANSION/CONVERGENCE)
- Les alertes et recommandations d'optimisation

La map est automatiquement mise à jour par le MapService à chaque :
- Modification de fichier markdown
- Changement de phase du projet
- Création ou suppression de fichier

Les indicateurs visuels (✓, ⚠️, 🔴) permettent d'identifier rapidement les fichiers nécessitant une attention particulière.

Generated: 2024-11-13 11:04:21

## Project Phase
🔄 CONVERGENCE PHASE
In this phase, agents focus on optimization and consolidation:
- Limited new content creation
- Focus on reducing token usage
- Emphasis on content optimization
- Can return to EXPANSION below 64.0k tokens

## Token Usage
Total: 118.3k/128k (92.4%)
Convergence at: 76.8k (60%)

## Phase Status
🔴 Convergence needed
Headroom: 9.7k tokens

## Active Agents
Current agent weights:
- evaluation: 0.40
- duplication: 0.60
- redondance: 0.80
- validation: 0.50
- documentaliste: 0.30

## Document Tree
📁 Project
├── 📄 README.md (0.6k tokens) ✓
├── 📄 __init__.py (0.1k tokens) ✓
├── 📁 agents/
│   ├── 📄 __init__.py (0.1k tokens) ✓
│   ├── 📁 base/
│   │   ├── 📄 __init__.py (0.1k tokens) ✓
│   │   ├── 📄 agent_base.py (1.3k tokens) ✓
│   │   ├── 📄 file_handler.py (0.7k tokens) ✓
│   │   └── 📄 prompt_handler.py (1.5k tokens) ✓
│   ├── 📄 kinos_agent.py (7.2k tokens) ⚠️
│   ├── 📁 research/
│   │   ├── 📄 __init__.py (0.0k tokens) ✓
│   │   └── 📄 research_agent.py (1.3k tokens) ✓
│   └── 📁 utils/
│       ├── 📄 encoding.py (0.4k tokens) ✓
│       ├── 📄 path_utils.py (0.3k tokens) ✓
│       └── 📄 rate_limiter.py (0.7k tokens) ✓
├── 📁 config/
│   ├── 📄 __init__.py (0.0k tokens) ✓
│   ├── 📄 agent_intervals.json (0.1k tokens) ✓
│   ├── 📄 global_config.py (1.2k tokens) ✓
│   └── 📄 perplexity_config.json (0.1k tokens) ✓
├── 📄 config.py (0.0k tokens) ✓
├── 📁 docs/
│   ├── 📄 ARCHITECTURE.md (10.0k tokens) ⚠️
│   ├── 📄 CLI.md (1.0k tokens) ✓
│   ├── 📄 DOCUMENTATION.md (12.2k tokens) 🔴
│   ├── 📄 EVALUATION.md (1.1k tokens) ✓
│   ├── 📄 FILE_PATHS.md (1.4k tokens) ✓
│   └── 📄 SPECIFICATION.md (3.4k tokens) ✓
├── 📄 kin.bat (0.0k tokens) ✓
├── 📄 kinos_cli.py (2.9k tokens) ✓
├── 📄 main.py (0.2k tokens) ✓
├── 📄 map (readonly).md (2.8k tokens) ✓
├── 📄 package-lock.json (0.0k tokens) ✓
├── 📁 prompts/
│   ├── 📄 chercheur.md (1.3k tokens) ✓
│   ├── 📄 chroniqueur.md (1.6k tokens) ✓
│   ├── 📄 cleaner.md (0.7k tokens) ✓
│   ├── 📄 documentaliste.md (1.3k tokens) ✓
│   ├── 📄 duplication.md (1.4k tokens) ✓
│   ├── 📄 evaluation.md (1.5k tokens) ✓
│   ├── 📄 management.md (1.5k tokens) ✓
│   ├── 📄 production.md (1.1k tokens) ✓
│   ├── 📄 redacteur.md (1.0k tokens) ✓
│   ├── 📄 redondance.md (1.1k tokens) ✓
│   ├── 📄 research.md (0.2k tokens) ✓
│   ├── 📄 specifications.md (1.4k tokens) ✓
│   ├── 📄 testeur.md (1.8k tokens) ✓
│   └── 📄 validation.md (1.4k tokens) ✓
├── 📄 requirements.txt (0.2k tokens) ✓
├── 📁 services/
│   ├── 📄 __init__.py (0.5k tokens) ✓
│   ├── 📄 agent_service.py (11.9k tokens) ⚠️
│   ├── 📄 base_service.py (1.2k tokens) ✓
│   ├── 📄 dataset_service.py (3.9k tokens) ✓
│   ├── 📄 file_manager.py (1.0k tokens) ✓
│   ├── 📄 file_service.py (1.1k tokens) ✓
│   ├── 📄 map_service.py (3.4k tokens) ✓
│   ├── 📄 phase_service.py (1.4k tokens) ✓
│   └── 📄 team_service.py (4.3k tokens) ✓
├── 📄 setup.py (0.2k tokens) ✓
├── 📄 start.sh (0.0k tokens) ✓
├── 📁 teams/
│   ├── 📁 book_writing/
│   │   └── 📄 config.json (0.5k tokens) ✓
│   ├── 📁 coding/
│   │   └── 📄 config.json (0.5k tokens) ✓
│   ├── 📁 default/
│   │   └── 📄 config.json (0.5k tokens) ✓
│   └── 📁 literature_review/
│       └── 📄 config.json (0.5k tokens) ✓
├── 📁 templates/
│   ├── 📁 initial_content/
│   │   └── 📄 demande.md (0.7k tokens) ✓
│   └── 📁 test_data/
│       └── 📄 demande_test_1.md (2.2k tokens) ✓
├── 📁 tests/
│   ├── 📄 conftest.py (0.2k tokens) ✓
│   ├── 📁 integration/
│   │   ├── 📁 routes/
│   │   │   └── 📄 test_agent_routes.py (0.5k tokens) ✓
│   │   └── 📄 test_web.py (0.4k tokens) ✓
│   ├── 📁 performance/
│   │   └── 📄 test_performance.py (0.5k tokens) ✓
│   └── 📁 unit/
│       ├── 📁 services/
│       │   ├── 📄 test_agent_service.py (0.5k tokens) ✓
│       │   ├── 📄 test_cache_service.py (0.7k tokens) ✓
│       │   ├── 📄 test_mission_service.py (0.7k tokens) ✓
│       │   └── 📄 test_notification_service.py (0.5k tokens) ✓
│       ├── 📄 test_agents.py (0.5k tokens) ✓
│       ├── 📄 test_services.py (0.4k tokens) ✓
│       └── 📁 utils/
│           └── 📄 test_error_handler.py (0.4k tokens) ✓
└── 📁 utils/
    ├── 📄 advanced_logger.py (0.0k tokens) ✓
    ├── 📄 chat_logger.py (0.0k tokens) ✓
    ├── 📄 commit_logger.py (1.1k tokens) ✓
    ├── 📄 constants.py (0.9k tokens) ✓
    ├── 📄 decorators.py (0.6k tokens) ✓
    ├── 📄 error_handler.py (0.5k tokens) ✓
    ├── 📄 exceptions.py (0.4k tokens) ✓
    ├── 📄 log_manager.py (0.0k tokens) ✓
    ├── 📄 logger.py (2.5k tokens) ✓
    ├── 📁 managers/
    │   ├── 📄 cache_manager.py (0.4k tokens) ✓
    │   ├── 📄 health_manager.py (0.7k tokens) ✓
    ├── 📄 path_manager.py (2.9k tokens) ✓
    ├── 📄 perplexity_client.py (0.5k tokens) ✓
    └── 📄 validators.py (0.1k tokens) ✓

## Warnings
⚠️ kinos_agent.py approaching limit (>6.0k tokens)
⚠️ ARCHITECTURE.md approaching limit (>6.0k tokens)
🔴 DOCUMENTATION.md needs consolidation (>12.0k tokens)
⚠️ agent_service.py approaching limit (>6.0k tokens)