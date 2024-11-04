# Parallagon

Parallagon est un framework d'agents autonomes parallèles conçu pour accélérer et améliorer le développement de projets complexes. Chaque agent gère son propre fichier et opère de manière continue et indépendante.

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
git clone git@github.com:DigitalKin-ai/parallagon.git
cd parallagon
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

- **Agent Spécification** : Gestion du template et structure documentaire
- **Agent Management** : Coordination et planification
- **Agent Production** : Création et implémentation du contenu
- **Agent Évaluation** : Contrôle qualité et validation

## 📁 Structure des Fichiers

```plaintext
/parallagon
  ├── demande.md         # Fichier de demande utilisateur
  ├── specifications.md  # Agent Spécification
  ├── management.md      # Agent Management
  ├── production.md      # Agent Production
  └── evaluation.md      # Agent Evaluation
```

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
