# KinOS

KinOS est un framework d'agents autonomes qui opèrent directement dans votre dossier de projet. Chaque agent gère ses propres fichiers et travaille de manière indépendante pour améliorer et accélérer le développement.

## ✨ Points Clés

- **Zéro configuration** - Fonctionne dans n'importe quel dossier
- **Agents autonomes** - Chaque agent gère ses fichiers
- **CLI simple** - Une seule commande : `kin`
- **Phases intelligentes** - Expansion/Convergence automatique
- **Dataset intégré** - Collection pour fine-tuning

## 🚀 Installation

```bash
# Installation depuis PyPI
pip install kinos

# Configuration des clés API
export ANTHROPIC_API_KEY="votre-clé"
export OPENAI_API_KEY="votre-clé"
```

## 🚀 Utilisation

```bash
# Lancer dans le dossier courant
cd votre-projet
kin

# Choisir une équipe spécifique
kin coding      # Équipe développement
kin book        # Équipe rédaction
kin research    # Équipe recherche

# Voir le statut des phases
kin phase status

# Voir l'aide complète
kin --help
```

## 📊 Phases de Projet

KinOS alterne automatiquement entre deux phases :

- **EXPANSION** (< 60% tokens) : Création libre de contenu
- **CONVERGENCE** (> 60% tokens) : Optimisation et consolidation

## 🤖 Agents Disponibles

Chaque équipe combine différents agents spécialisés :

- **SpecificationsAgent** - Analyse des besoins
- **ProductionAgent** - Génération de code
- **ValidationAgent** - Contrôle qualité
- **DocumentalisteAgent** - Documentation
- **DuplicationAgent** - Détection redondances

## 📋 Prérequis

- Python 3.8+
- Clés API Anthropic et OpenAI
- Aider CLI (`pip install aider-chat`)

## 📚 Documentation

Documentation complète : https://kinos.readthedocs.io

## 🤝 Contribution

Les contributions sont bienvenues ! Voir CONTRIBUTING.md

## 📝 Licence

MIT License - voir LICENSE
