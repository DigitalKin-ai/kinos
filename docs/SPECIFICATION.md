# Gestion Dynamique des Chemins de Fichiers dans KinOS

## Nouveau Modèle de Gestion des Chemins de Mission

### Changement Fondamental
- Le répertoire de travail actuel devient le contexte de mission
- Aucuna configuration complexa requise
- Lancement immédiat dans n'importe quel dossier de projet

### Principes Clés

#### 1. Contexte Dynamique
- Chaque répertoire peut devenir instantanément un contexte de mission
- Pas besoin de configuration préalable
- L'agent s'adapte automatiquement à l'environnement courant

#### 2. Résolution de Chemin
- Utilisation du répertoire courant comme racine de mission
- Support optionnel de chemins personnalisés
- Validation dynamique des permissions
- Normalisation intelligente des chemins

### Exemples d'Utilisation

```bash
# Lancement avec l'équipe par défaut dans le répertoire courant
kin

# Lancement d'une équipe spécifique
kin book-writing

# Lancement avec un chemin personnalisé
kin book-writing -p /chemin/specifique
```

### Stratégies de Validation

```python
def validate_mission_path(path: str) -> bool:
    """
    Validation comprehensive du chemin de mission
    
    Critères:
    - Chemin absolu
    - Existe et est accessible
    - Permissions lecture/écriture
    - Exclusion des chemins système
    """
    return (
        os.path.isabs(path) and
        os.path.exists(path) and
        os.access(path, os.R_OK | os.W_OK) and
        not path.startswith('/sys') and
        not path.startswith('/proc')
    )
```

### Avantages

1. **Simplicité**
   - Aucune configuration complexe
   - Démarrage immédiat
   - Zéro configuration requise

2. **Flexibilité**
   - Adaptable à tous les types de projets
   - Support multi-langages
   - Indépendant de la structure de projet

3. **Sécurité**
   - Validation stricte des chemins
   - Vérification des permissions
   - Protection contre les accès non autorisés

### Bonnes Pratiques

1. Toujours vérifier les permissions avant opération
2. Utiliser des chemins absolus
3. Gérer les erreurs de chemin
4. Logger les opérations sensibles
5. Fournir des options de configuration personnalisée

## 2. Composants Principaux

### 2.1 Agents
Les agents sont le cœur du système KinOS, chacun opérant de manière totalement autonome avec une gestion flexible des ressources.

#### Types d'agents
1. **Agent de Spécifications (SpecificationsAgent)**
   - Analyse autonome des demandes et définition des spécifications
   - Gestion flexible des documents de spécifications
   - Création de sous-spécifications selon les besoins
   - Maintien proactif de la cohérence entre documents
   - Validation continue des exigences

2. **Agent de Production (ProductionAgent)**
   - Génération et optimisation autonome du code/contenu
   - Organisation libre des fichiers de production
   - Création dynamique de modules/composants
   - Gestion intelligente des dépendances
   - Optimisation continue du code

3. **Agent de Management (ManagementAgent)**
   - Coordination autonome des activités
   - Organisation flexible des tâches et priorités
   - Création dynamique de rapports et tableaux de bord
   - Gestion adaptative des ressources
   - Résolution proactive des conflits

4. **Agent d'Évaluation (EvaluationAgent)**
   - Tests et validation autonomes
   - Organisation dynamique des suites de tests
   - Génération de rapports de couverture
   - Analyse continue des performances
   - Identification proactive des améliorations

5. **Agent chroniqueur (ChroniqueurAgent)**
   - Documentation autonome des activités
   - Gestion flexible de l'historique
   - Génération dynamique de rapports
   - Suivi adaptatif des métriques
   - Alertes proactives

#### Cycle de vie des agents
1. **Initialisation**
   - Validation autonome du contexte d'exécution
   - Vérification dynamique des permissions
   - Configuration adaptative des ressources
   - Établissement flexible des connexions

2. **Exécution**
   - Surveillance autonome des ressources
   - Adaptation dynamique du rythme d'exécution
   - Prise de décision indépendante
   - Gestion proactive des erreurs
   - Optimisation continue des performances

3. **Communication**
   - Échange asynchrone d'informations
   - Synchronisation adaptative
   - Notifications temps réel
   - Résolution autonome des conflits
   - Coordination flexible des ressources

#### Intégration avec Aider
1. **Format d'appel standardisé**
   ```bash
   aider --model anthropic/claude-3-5-haiku-20241022 --no-git --yes-always --file [fichiers_de_la_mission] --message [prompt]
   ```

2. **Choix techniques**
   - **Model haiku**: Optimisé pour les modifications de code et documentation
   - **--no-git**: Évite les conflits avec le système de versioning externe
   - **--yes-always**: Permet l'automatisation complète sans interventions
   - **--file**: Spécifie les fichiers à surveiller et modifier

3. **Avantages de cette approche**
   - Isolation des modifications par agent
   - Contrôle granulaire des changements
   - Traçabilité des opérations
   - Cohérence des modifications

4. **Gestion des chemins**
   - Utilisation de chemins relatifs pour la portabilité
   - Changement de contexte vers le dossier de mission
   - Retour au dossier original après exécution
   - Gestion des erreurs de chemins

### 2.2 Système de Fichiers

#### Gestion des fichiers
- **Format Markdown standardisé**
  - Structure cohérente
  - Sections prédéfinies
  - Métadonnées intégrées
  - Balisage sémantique

- **Synchronisation**
  - Verrouillage des fichiers
  - Gestion des accès concurrents
  - Sauvegarde automatique
  - Historique des versions

- **Organisation**
  - Séparation des préoccupations
  - Hiérarchie claire
  - Nommage conventionnel
  - Liens entre fichiers

### 2.3 Dataset Service

Le DatasetService gère la collecte et l'organisation des données pour le fine-tuning.

#### Fonctionnalités
- Collection automatique des interactions
- Validation des données
- Gestion des duplicatas
- Nettoyage périodique
- Métriques d'utilisation

#### Configuration
```python
# Chemins
data_dir = "data/"
dataset_file = "data/fine-tuning.jsonl"

# Format d'entrée
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "metadata": {
        "timestamp": "2024-03-21T15:30:45",
        "num_files": 3,
        "files": ["file1.md", "file2.md", "file3.md"]
    }
}
```

#### Méthodes Principales
- `add_interaction_async()`: Ajout asynchrone d'interactions
- `is_available()`: Vérification disponibilité service
- `get_dataset_stats()`: Statistiques d'utilisation
- `cleanup()`: Nettoyage périodique

#### Intégration
- Collecte automatique via AiderAgent
- Validation avant sauvegarde
- Métriques de performance
- Gestion des erreurs

### 2.4 Interface Web

#### Architecture Frontend
- **Vue.js 3**
  - Components réactifs
  - État centralisé
  - Rendu optimisé
  - Gestion des événements

- **Interface utilisateur**
  - Design responsive
  - Navigation intuitive
  - Feedback visuel
  - Accessibilité

#### Fonctionnalités principales

1. **Navigation**
   - Side panel de sélection des missions
   - Navigation contextuelle par mission
   - Accès rapide aux différentes vues

2. **Page Agents**
   - Liste complète des agents de la mission
   - Configuration des prompts par agent
   - Contrôles Start/Stop pour chaque agent
   - Indicateurs d'état en temps réel
   - Personnalisation des paramètres

3. **Page Fichiers**
   - Vue en temps réel de tous les fichiers de la mission
   - Mise à jour automatique du contenu
   - Visualisation des modifications
   - Organisation hiérarchique des fichiers
   - Système de coloration syntaxique

4. **Gestion des missions**
   - Création/suppression
   - Configuration
   - Vue d'ensemble
   - Statuts en temps réel

#### Système de notifications
- **Types de notifications**
  - Informations
  - Avertissements
  - Erreurs
  - Succès

- **Mécanismes de livraison**
  - Temps réel
  - File d'attente
  - Priorités
  - Persistance

#### API REST
- **Points d'entrée**
  - Gestion des missions
  - Contrôle des agents
  - Manipulation des fichiers
  - Monitoring système

- **Sécurité**
  - Authentification
  - Autorisation
  - Validation des données
  - Rate limiting

## 3. Fonctionnalités
### 3.1 Gestion des Missions
- Création/suppression
- Organisation
- États et transitions
- Sauvegarde et restauration

### 3.2 Communication Inter-Agents
- Protocoles d'échange
- Synchronisation
- Gestion des conflits
- Notifications

### 3.3 Monitoring et Contrôle
- Interface de contrôle
- Logs et traces
- Métriques de performance
- Gestion des erreurs

## 4. Aspects Techniques
### 4.1 Technologies Utilisées
- Stack technique
- Dépendances
- APIs externes
- Outils de développement

### 4.2 Configuration
- Variables d'environnement
- Fichiers de configuration
- Paramètres ajustables
- Modes de déploiement

### 4.3 Sécurité
- Gestion des accès
- Protection des données
- Validation des entrées
- Bonnes pratiques

## 5. Développement
### 5.1 Installation
- Prérequis
- Étapes d'installation
- Configuration initiale
- Tests de validation

### 5.2 Contribution
- Guidelines
- Workflow Git
- Standards de code
- Process de revue

### 5.3 Tests
- Stratégie de test
- Types de tests
- Couverture
- Automatisation

## 6. Roadmap
- Fonctionnalités futures
- Améliorations prévues
- Corrections planifiées
- Évolutions majeures

## 7. Interface CLI

### 7.1 Lancement d'Équipes

#### Commande de Lancement d'Équipe
```bash
python kinos_cli.py team launch --mission <nom_mission> --team <nom_equipe>
```

#### Fonctionnalités
- Lancement d'une équipe spécifique pour une mission
- Streaming des logs en temps réel
- Gestion des erreurs et états
- Support de différents types d'équipes prédéfinies

#### Modes de Lancement
1. **Mode Standard**
   - Activation séquentielle des agents
   - Logs détaillés
   - Gestion des dépendances entre agents

2. **Mode Verbose**
   - Informations de débogage complètes
   - Métriques de performance
   - Trace des appels système

#### Exemple de Workflow
```bash
# Lancer l'équipe de développement pour la mission "projet-ia"
python kinos_cli.py team launch --mission projet-ia --team coding

# Mode verbose pour diagnostic
python kinos_cli.py team launch --mission projet-ia --team coding --verbose
```

#### Gestion des Erreurs
- Validation des noms de mission et d'équipe
- Gestion des équipes non existantes
- Détection des conflits de ressources
- Mécanisme de rollback en cas d'échec

#### Streaming de Logs
- Affichage en temps réel
- Formatage coloré
- Filtrage par niveau de log
- Sauvegarde optionnelle dans un fichier

#### Options Avancées
```bash
python kinos_cli.py team launch 
    --mission <nom>       # Mission cible
    --team <nom>          # Équipe à lancer
    --verbose             # Mode débogage
    --dry-run             # Simulation sans exécution
    --timeout <secondes>  # Limite de temps
    --log-file <chemin>   # Fichier de log
    --phase <phase>       # Phase initiale (expansion/convergence)
    --tokens-limit <n>    # Limite de tokens personnalisée
```

#### Commandes de Phase
```bash
# Phase Management Commands

## View Phase Status
```bash
# View current phase and token usage
kin phase status

# View detailed token metrics
kin phase tokens

# View all phase-related metrics
kin phase metrics
```

## Phase Control
```bash
# Force phase change (use with caution)
kin phase set expansion   # Switch to expansion phase
kin phase set convergence # Switch to convergence phase

# Monitor phase transitions
kin phase watch          # Real-time phase monitoring

# Get phase history
kin phase history        # View phase transition history
```

## Token Management
```bash
# View token usage by file
kin tokens list

# Get warnings for files approaching limits
kin tokens check

# View token headroom
kin tokens headroom
```
```
