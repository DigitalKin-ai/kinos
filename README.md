# KinOS

KinOS est un framework d'agents autonomes parallèles conçu pour accélérer et améliorer le développement de projets complexes. Chaque agent gère son propre fichier et opère de manière continue et indépendante.

## 🌟 Caractéristiques

- **Simplicité maximale** dans la conception
- **Communication via fichiers markdown**
- **Modifications non-linéaires** via SEARCH/REPLACE
- **Autonomie complète** des agents
- **État persistant** dans les fichiers
- **Interface web intuitive** pour le suivi et le contrôle

## 🚀 Installation

1. Clonez le repository :
```bash
git clone git@github.com:DigitalKin-ai/kinos.git
cd kinos
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurez les clés API dans un fichier `.env` :
```env
ANTHROPIC_API_KEY=votre-clé-anthropic
OPENAI_API_KEY=votre-clé-openai
```

## 🚀 CLI Usage

### Mission Path Management

#### Launching a Mission with Custom Path

```bash
# Launch a mission using default path
python kinos_cli.py team launch --mission my-project

# Launch a mission with a custom base path
python kinos_cli.py team launch --mission my-project --base-path /custom/projects/missions

# Launch a mission with verbose logging
python kinos_cli.py team launch --mission my-project --verbose --base-path /custom/path
```

#### Mission Path Options

- `--mission`: Name of the mission (required)
- `--base-path`: Optional custom base path for mission files
- `--verbose`: Detailed logging about path resolution
- `--dry-run`: Simulate mission launch without creating files

#### Path Management Commands

```bash
# List available missions
python kinos_cli.py missions list

# Get details about a specific mission's path
python kinos_cli.py missions path --mission my-project
```

### Path Configuration Examples

#### Default Behavior
- Missions stored in `~/KinOS_Missions/`
- Automatic path normalization
- Secure path validation

#### Custom Path Configuration
```bash
# Set a custom missions directory in .env
KINOS_DEFAULT_MISSIONS_DIR=/path/to/custom/missions
```

### Path Security Features

- Validates mission directory paths
- Prevents path traversal attacks
- Enforces permission checks
- Normalizes mission names
- Supports multiple base paths

## 🎮 Utilisation

1. Lancez le serveur :
```bash
python run_server.py
```

2. Ouvrez votre navigateur à l'adresse : `http://127.0.0.1:8000`

3. Utilisez l'interface pour :
   - Démarrer/arrêter les agents
   - Visualiser les fichiers en temps réel
   - Suivre les logs d'exécution
   - Exporter les logs
   - Charger des données de test

## 🤖 Agents

#### Core Agents
1. **SpecificationsAgent**
   - Gestion du template et structure documentaire
   - Analyse des demandes initiales
   - Extraction des exigences
   - Configuration:
     ```python
     {
         "name": "Specification",
         "prompt_file": "prompts/specifications.md",
         "check_interval": 300
     }
     ```

2. **ProductionAgent**
   - Création et implémentation du contenu
   - Génération de code optimisé
   - Respect des standards
   - Configuration:
     ```python
     {
         "name": "Production",
         "prompt_file": "prompts/production.md",
         "check_interval": 300
     }
     ```

3. **ManagementAgent**
   - Coordination et planification
   - Gestion des priorités
   - Résolution des conflits
   - Configuration:
     ```python
     {
         "name": "Management",
         "prompt_file": "prompts/management.md",
         "check_interval": 300
     }
     ```

4. **EvaluationAgent**
   - Contrôle qualité et validation
   - Tests fonctionnels
   - Mesures performances
   - Configuration:
     ```python
     {
         "name": "Evaluation",
         "prompt_file": "prompts/evaluation.md",
         "check_interval": 300
     }
     ```

5. **DocumentalisteAgent**
   - Analyse de la documentation existante
   - Détection des incohérences avec le code
   - Mise à jour automatique de la documentation
   - Configuration:
     ```python
     {
         "name": "Documentaliste",
         "prompt_file": "prompts/documentaliste.md",
         "check_interval": 300
     }
     ```

#### Agent Interactions
- Surveillance continue des fichiers partagés
- Communication via système de fichiers
- Notifications temps réel des modifications
- Coordination via AgentService
- Résolution des conflits par ManagementAgent

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

- Python 3.9+
- Clés API (Anthropic et OpenAI)
- Navigateur web moderne

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- [Contact à définir]
