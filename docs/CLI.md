# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

La CLI KinOS offre un ensemble de commandes pour interagir avec le système d'agents autonomes, gérer les missions et contrôler les opérations.

## Installation et Prérequis

- Python 3.8+
- Dépendances installées via `requirements.txt`
- Clés API configurées dans `.env`

## Utilisation Générale

```bash
python kinos_cli.py <commande> <sous-commande> [options]
```

## Commandes Disponibles

### 1. Gestion des Équipes

#### Lancer une Équipe
```bash
python kinos_cli.py team launch --mission <nom_mission> --team <nom_equipe>
```

**Options**:
- `--mission` (requis): Nom de la mission
- `--team` (requis): Nom de l'équipe
- `--verbose`: Mode débogage détaillé
- `--dry-run`: Simulation sans exécution
- `--timeout <secondes>`: Limite de temps
- `--log-file <chemin>`: Fichier de log

**Exemples**:
```bash
# Lancer l'équipe de développement
python kinos_cli.py team launch --mission projet-ia --team coding

# Mode verbose pour diagnostic
python kinos_cli.py team launch --mission projet-ia --team coding --verbose
```

### 2. Gestion des Agents

#### Lister les Agents
```bash
python kinos_cli.py agent list
```

**Fonctionnalités**:
- Affiche tous les agents disponibles
- Montre le statut de chaque agent
- Utile pour vérifier les agents configurés

**Exemple**:
```bash
python kinos_cli.py agent list
```

### 3. Gestion des Missions

#### Lister les Missions
```bash
python kinos_cli.py missions list
```

**Fonctionnalités**:
- Affiche toutes les missions disponibles
- Montre l'ID, le nom, le statut et la date de création
- Utile pour avoir un aperçu des projets en cours

**Exemple**:
```bash
python kinos_cli.py missions list
```

### 4. Gestion des Équipes Disponibles

#### Lister les Équipes
```bash
python kinos_cli.py teams list
```

**Fonctionnalités**:
- Affiche toutes les équipes prédéfinies
- Montre l'ID, le nom et les agents de chaque équipe
- Aide à choisir l'équipe adaptée à un projet

**Exemple**:
```bash
python kinos_cli.py teams list
```

## Types d'Équipes Prédéfinies

1. **Équipe Développement (coding)**
   - Agents: SpecificationsAgent, ProductionAgent, TesteurAgent, etc.
   - Idéal pour les projets de développement logiciel

2. **Équipe Rédaction (book-writing)**
   - Agents: SpecificationsAgent, RedacteurAgent, ValidationAgent, etc.
   - Adapté à la création de documentation ou de contenu

3. **Équipe Revue Littéraire (literature-review)**
   - Agents: DocumentalisteAgent, EvaluationAgent, SuiviAgent, etc.
   - Pour l'analyse et la revue de documents

## Gestion des Erreurs

- Validation stricte des noms de mission et d'équipe
- Messages d'erreur détaillés
- Codes de sortie pour intégration avec scripts

## Bonnes Pratiques

1. Toujours spécifier une mission existante
2. Vérifier les agents disponibles avant lancement
3. Utiliser `--verbose` pour le débogage
4. Surveiller les logs pour les détails d'exécution

## Dépannage

- Vérifiez que les clés API sont configurées
- Assurez-vous que la mission existe
- Consultez les logs pour les détails des erreurs
- Utilisez `--dry-run` pour tester sans exécuter

## Configuration Avancée

Vous pouvez personnaliser le comportement via des variables d'environnement :

```bash
# Exemple de configuration
KINOS_LOG_LEVEL=DEBUG python kinos_cli.py team launch ...
```

## Contribution et Support

- Rapportez les bugs sur le dépôt GitHub
- Consultez la documentation complète
- Rejoignez notre communauté Discord

## Versions

- Version actuelle : 0.1.0
- Dernière mise à jour : 2024-02-15
- Compatibilité : Python 3.8+
