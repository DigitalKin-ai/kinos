# KinOS

KinOS est un framework d'agents autonomes qui opèrent directement dans votre dossier de projet. Les agents collaborent pour améliorer et accélérer le développement.

## ✨ Points Clés

- **Zéro configuration** - Fonctionne dans n'importe quel dossier
- **Agents autonomes** - Collaboration intelligente
- **CLI minimaliste** - Une seule commande : `kin`
- **Dataset intégré** - Collection pour fine-tuning
- **Gestion dynamique** - S'adapte à votre projet

## 🚀 Installation

```bash
# Installation
pip install kinos

# Configuration (requise)
export ANTHROPIC_API_KEY="votre-clé"
```

## 🚀 Utilisation

```bash
# Lancer KinOS
cd votre-projet
kin

# Lancer une équipe spécifique
kin coding

# Voir l'aide
kin --help
```

## 🤖 Agents Disponibles

Les agents collaborent automatiquement selon les besoins :

- **SpecificationsAgent** - Analyse des besoins
- **ProductionAgent** - Génération de code
- **ValidationAgent** - Contrôle qualité
- **DocumentalisteAgent** - Documentation
- **DuplicationAgent** - Détection redondances
- **ChroniqueurAgent** - Suivi des changements
- **TesteurAgent** - Tests automatisés

## 🏗️ Structure du Projet

KinOS utilise désormais une structure de projet team-local :

```
mon_projet/
├── team_default/
│   ├── config.json      # Configuration de l'équipe
│   ├── history/         # Historique des interactions
│   ├── prompts/         # Prompts spécifiques à l'équipe
│   └── team_types/      # Types d'équipes personnalisés
├── team_coding/         # Autres équipes possibles
└── main.py
```

- Chaque équipe a sa propre configuration
- Les fichiers sont locaux à l'équipe
- Détection dynamique des équipes

## 📋 Prérequis

- Python 3.8+
- Git (pour Aider)
- Aider CLI
- Clés API :
  * Anthropic Claude
  * OpenAI (optionnel)

## 📚 Documentation

Documentation complète : https://kinos.readthedocs.io

## 🤝 Contribution

Les contributions sont bienvenues ! Voir CONTRIBUTING.md

## 📝 Licence

MIT License - voir LICENSE
