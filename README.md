# KinOS

KinOS est un framework d'agents autonomes parallèles conçu pour accélérer et améliorer le développement de projets complexes via une interface en ligne de commande (CLI). Chaque agent gère son propre fichier et opère de manière continue et indépendante.

## 🌟 Caractéristiques

- **Simplicité maximale** dans la conception
- **Communication via fichiers markdown**
- **Modifications non-linéaires** via SEARCH/REPLACE
- **Autonomie complète** des agents
- **État persistant** dans les fichiers
- **Interface CLI intuitive** pour le contrôle

## 🚀 Installation

1. Clonez le repository :
```bash
git clone git@github.com:DigitalKin-ai/kinos.git
cd kinos
```

2. Installez les dépendances :
```bash
pip install -e .
```

3. Configurez les clés API dans un fichier `.env` :
```env
ANTHROPIC_API_KEY=votre-clé-anthropic
OPENAI_API_KEY=votre-clé-openai
```

## 🚀 Utilisation

### Commandes de Base
```bash
# Lancer l'équipe par défaut dans le dossier courant
kin

# Lancer avec logs détaillés
kin -v

# Afficher l'aide
kin --help

# Lancer une équipe spécifique
kin coding
kin book-writing
kin literature-review
```

### Équipes Prédéfinies

1. **default** (équipe par défaut)
   - Création de contenu et documentation
   - Agents: Specifications, Management, Evaluation, etc.
   - Usage: `kin`

2. **coding**
   - Développement logiciel
   - Agents: Specifications, Production, Testing, etc.
   - Usage: `kin coding`

3. **literature-review**
   - Recherche et analyse
   - Agents: Specifications, Management, Evaluation, etc.
   - Usage: `kin literature-review`

## 🤖 Agents

### Équipe par Défaut

Par défaut, une équipe standard est utilisée avec les agents suivants :
- Specifications
- Management
- Evaluation
- Chroniqueur
- Documentaliste

### Agents Principaux

1. **SpecificationsAgent**
   - Gestion du template et structure documentaire
   - Analyse des demandes initiales
   - Extraction des exigences

2. **ProductionAgent**
   - Création et implémentation du contenu
   - Génération de code optimisé
   - Respect des standards

3. **ManagementAgent**
   - Coordination et planification
   - Gestion des priorités
   - Résolution des conflits

4. **EvaluationAgent**
   - Contrôle qualité et validation
   - Tests fonctionnels
   - Mesures performances

5. **DocumentalisteAgent**
   - Analyse de la documentation existante
   - Détection des incohérences avec le code
   - Mise à jour automatique de la documentation

## 🛠️ Développement

Pour contribuer au projet :

1. Créez une branche pour votre fonctionnalité
2. Committez vos changements
3. Ouvrez une Pull Request

## 📄 Licence

[À définir]

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir des issues
- Proposer des pull requests
- Suggérer des améliorations

## ⚠️ Prérequis

- Python 3.8+
- Clés API (Anthropic et OpenAI)
- Aider CLI installé et configuré

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- [Contact à définir]
