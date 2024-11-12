# Gestion Dynamique des Chemins de Fichiers dans KinOS

## Nouveau Modèle de Gestion des Chemins de Mission

### Changement Fondamental
- Les chemins de mission sont désormais des chemins absolus, complètement indépendants du répertoire du projet
- Le chemin de mission est spécifié explicitement et peut se trouver n'importe où sur le système de fichiers
- Permet une séparation claire entre le code du projet et les fichiers de mission
- Facilite l'activation de Git pour chaque mission

### Avantages
1. **Isolation Complète**
   - Chaque mission a son propre espace de fichiers
   - Indépendance totale du répertoire du projet KinOS
   - Possibilité de gérer des missions dans n'importe quel emplacement du système

2. **Activation Git Simplifiée**
   - Aider peut être lancé directement dans le dossier de mission
   - Gestion de version locale pour chaque mission
   - Contrôle de version indépendant

### Exemple de Configuration

```python
# Exemple de spécification de chemin de mission
mission_config = {
    'name': 'mon-projet-ia',
    'path': '/chemin/absolu/vers/missions/mon-projet-ia',
    'git_enabled': True
}
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
