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
# Lancement dans le répertoire courant
kin

# Lancement d'une équipe spécifique
kin book-writing

# Lancement avec un chemin personnalisé
kin book-writing -p /chemin/specifique/projet
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

### Configuration Minimale

```python
# Configuration par défaut dans global_config.py
DEFAULT_CONFIG = {
    'core': {
        'default_mission_dir': os.getcwd(),
        'verbose': False
    },
    'paths': {
        'current_mission': os.path.basename(os.getcwd())
    }
}
```

### Diagnostic et Débogage

Utilisez le script de diagnostic pour comprendre la configuration des chemins :

```bash
python diagnose_paths.py
```

Ce script fournira :
- Répertoire de travail actuel
- Racine du projet
- Chemin de mission
- Vérification des permissions
```

### Stratégies d'Accès

#### 1. Initialisation de Mission
```python
mission_dir = "/chemin/absolu/vers/missions/ma-mission"
agent_config = {
    'mission_dir': mission_dir,
    'git_enabled': True
}
```

#### 2. Lancement Aider
```bash
# Changement de répertoire avant l'appel d'Aider
cd /chemin/absolu/vers/missions/ma-mission
aider --no-git --yes-always --file *.py --message "Modifier le code"
```

### Considérations de Sécurité
- Validation stricte des chemins absolus
- Vérification des permissions d'accès
- Protection contre les traversées de répertoire
- Validation des chemins en dehors du projet

### Méthodes de Validation
```python
def validate_mission_path(path: str) -> bool:
    """
    Valide un chemin de mission
    
    Critères:
    - Chemin absolu
    - Existe et est accessible
    - N'est pas dans le répertoire du projet
    - Permissions en lecture/écriture
    """
    if not os.path.isabs(path):
        return False
    
    if not os.path.exists(path):
        return False
    
    if not os.access(path, os.R_OK | os.W_OK):
        return False
    
    # Optionnel : Vérifier que le chemin n'est pas dans le projet
    project_root = PathManager.get_project_root()
    if path.startswith(project_root):
        return False
    
    return True
```

### Intégration avec PathManager
```python
class PathManager:
    @staticmethod
    def get_mission_path(mission_name: str, base_path: str = None) -> str:
        """
        Récupère le chemin complet d'une mission
        
        Args:
            mission_name: Nom de la mission
            base_path: Chemin de base personnalisé (optionnel)
        """
        if base_path:
            # Utiliser le chemin de base fourni
            mission_path = os.path.join(base_path, mission_name)
        else:
            # Utiliser un chemin par défaut si non spécifié
            mission_path = os.path.join("/chemin/par/defaut/missions", mission_name)
        
        # Validation du chemin
        if not validate_mission_path(mission_path):
            raise ValueError(f"Chemin de mission invalide : {mission_path}")
        
        return mission_path
```

### Bonnes Pratiques
1. Toujours utiliser des chemins absolus
2. Valider les chemins avant utilisation
3. Gérer les permissions explicitement
4. Supporter les chemins personnalisés
5. Documenter la configuration des chemins
