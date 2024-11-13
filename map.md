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

Generated: 2024-11-13 06:33:04

## Project Phase
🌱 EXPANSION PHASE
In this phase, agents focus on content creation and development:
- Free to create new content and sections
- Normal operation of all agents
- Regular token monitoring
- Will transition to CONVERGENCE at 76.8k tokens

## Token Usage
Total: 48.7k/128k (38.0%)
Convergence at: 76.8k (60%)

## Phase Status
✓ Below convergence threshold
Headroom: 28.1k tokens

## Document Tree
📁 Project
├── 📄 README.md (0.6k tokens) ✓
├── 📁 docs/
│   ├── 📄 ARCHITECTURE.md (6.0k tokens) ✓
│   ├── 📄 CLI.md (1.0k tokens) ✓
│   ├── 📄 DOCUMENTATION.md (12.2k tokens) 🔴
│   ├── 📄 EVALUATION.md (1.1k tokens) ✓
│   ├── 📄 FILE_PATHS.md (1.4k tokens) ✓
│   └── 📄 SPECIFICATION.md (3.4k tokens) ✓
├── 📄 map (readonly).md (1.0k tokens) ✓
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
│   ├── 📄 redacteur2.md (1.0k tokens) ✓
│   ├── 📄 redacteur3.md (1.0k tokens) ✓
│   ├── 📄 redondance.md (1.1k tokens) ✓
│   ├── 📄 specifications.md (1.4k tokens) ✓
│   ├── 📄 testeur.md (1.8k tokens) ✓
│   └── 📄 validation.md (1.4k tokens) ✓
├── 📁 templates/
│   ├── 📁 initial_content/
│   │   └── 📄 demande.md (0.7k tokens) ✓
│   └── 📁 test_data/
│       └── 📄 demande_test_1.md (2.2k tokens) ✓

## Warnings
🔴 DOCUMENTATION.md needs consolidation (>12.0k tokens)