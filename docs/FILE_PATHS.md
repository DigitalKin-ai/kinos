# Gestion des Chemins de Fichiers dans KinOS

## Vue d'Ensemble

KinOS utilise une stratégie de gestion des chemins de fichiers qui combine:
- Chemins absolus pour la création et l'initialisation
- Chemins relatifs pour les opérations Aider
- Structure de dossiers standardisée

## Stratégies par Contexte

### 1. Création de Fichiers

- Utilise des chemins absolus
- Structure: `missions/<nom_mission>/<fichier>.md`
- Crée les dossiers parents si nécessaires
- Vérifie les droits d'accès

Exemple:
```python
mission_dir = os.path.join("missions", mission_name)
file_path = os.path.join(mission_dir, "specifications.md")
os.makedirs(mission_dir, exist_ok=True)
```

### 2. Opérations Aider

- Change vers le dossier mission
- Utilise des chemins relatifs
- Revient au dossier original après

Exemple:
```python
current_dir = os.getcwd()
try:
    os.chdir(mission_dir)
    # Utilise chemins relatifs pour Aider
finally:
    os.chdir(current_dir)
```

### 3. Lecture/Écriture

- Utilise chemins absolus pour accès direct
- Vérifie existence avant opérations
- Gère les erreurs de permissions

## Bonnes Pratiques

1. Validation des Chemins
   - Normaliser avec `os.path.normpath()`
   - Vérifier les traversées de dossier
   - Valider les extensions de fichiers

2. Gestion des Erreurs
   - Vérifier existence des dossiers
   - Gérer les erreurs de permissions
   - Nettoyer les ressources

3. Portabilité
   - Utiliser `os.path.join()`
   - Éviter les séparateurs codés en dur
   - Gérer les différences Windows/Unix

## Exemples de Code

### Création Sécurisée
```python
def create_mission_file(mission_name: str, file_name: str) -> bool:
    try:
        # Construire chemin absolu
        mission_dir = os.path.abspath(os.path.join("missions", mission_name))
        file_path = os.path.join(mission_dir, file_name)
        
        # Valider le chemin
        if not file_path.startswith(mission_dir):
            raise ValueError("Invalid file path")
            
        # Créer dossier et fichier
        os.makedirs(mission_dir, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write("")
            
        return True
        
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        return False
```

### Exécution Aider
```python
def run_aider_in_mission(mission_name: str, files: List[str]) -> bool:
    current_dir = os.getcwd()
    try:
        # Changer vers dossier mission
        mission_dir = os.path.join("missions", mission_name)
        os.chdir(mission_dir)
        
        # Utiliser chemins relatifs
        cmd = ["aider", "--no-git"]
        for file in files:
            cmd.extend(["--file", os.path.basename(file)])
            
        subprocess.run(cmd)
        return True
        
    finally:
        # Toujours revenir au dossier original
        os.chdir(current_dir)
```

## Points d'Attention

1. Sécurité
   - Valider tous les chemins
   - Éviter les traversées de dossier
   - Gérer les permissions

2. Performance
   - Minimiser les changements de dossier
   - Réutiliser les chemins calculés
   - Mettre en cache si possible

3. Maintenance
   - Documenter la stratégie
   - Centraliser la logique
   - Tests automatisés
