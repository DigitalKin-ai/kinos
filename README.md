# KinOS

KinOS est un framework d'agents autonomes qui opèrent directement dans votre dossier de projet. Les agents collaborent de manière autonome pour améliorer et accélérer le développement.

## ✨ Points Clés

- **Zéro configuration** - Fonctionne dans n'importe quel dossier
- **Agents autonomes** - Collaboration intelligente
- **CLI minimaliste** - Une seule commande : `kin`
- **Phases adaptatives** - Expansion/Convergence automatique
- **Dataset intégré** - Collection pour fine-tuning
- **Gestion dynamique** - S'adapte à votre projet

## 🚀 Installation

```bash
# Installation des prérequis
pip install aider-chat

# Installation de KinOS
pip install kinos

# Configuration des clés API (requises)
export ANTHROPIC_API_KEY="votre-clé"
export OPENAI_API_KEY="votre-clé"
```

## 🚀 Utilisation

```bash
# Lancer KinOS dans votre projet
cd votre-projet
kin

# Voir le statut des phases
kin phase status
kin phase tokens

# Gérer les phases manuellement
kin phase set expansion
kin phase set convergence

# Voir l'aide complète
kin --help
```

## 📊 Phases de Projet

KinOS alterne automatiquement entre deux phases selon l'utilisation des tokens :

- **EXPANSION** (< 60% tokens) 
  * Création libre de contenu
  * Développement de nouvelles fonctionnalités
  * Documentation extensive

- **CONVERGENCE** (> 60% tokens)
  * Optimisation du contenu existant
  * Réduction de la duplication
  * Consolidation des documents

## 🤖 Agents Disponibles

Les agents collaborent automatiquement selon les besoins :

- **SpecificationsAgent** - Analyse des besoins
- **ProductionAgent** - Génération de code
- **ValidationAgent** - Contrôle qualité
- **DocumentalisteAgent** - Documentation
- **DuplicationAgent** - Détection redondances
- **ChroniqueurAgent** - Suivi des changements
- **TesteurAgent** - Tests automatisés

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
