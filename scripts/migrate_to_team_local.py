import os
import shutil
import json

def detect_existing_project_structure():
    """Détecte la structure existante du projet"""
    current_dir = os.getcwd()
    
    # Rechercher des indices de structure de projet
    potential_project_markers = [
        'main.py', 
        'setup.py', 
        'requirements.txt', 
        '.git',
        'config'
    ]
    
    return all(os.path.exists(os.path.join(current_dir, marker)) 
               for marker in potential_project_markers)

def create_default_team_structure(team_name='default'):
    """Crée une structure d'équipe par défaut"""
    current_dir = os.getcwd()
    team_dir = os.path.join(current_dir, f'team_{team_name}')
    
    # Créer les répertoires de l'équipe
    os.makedirs(team_dir, exist_ok=True)
    subdirs = ['history', 'prompts', 'team_types', 'logs']
    for subdir in subdirs:
        os.makedirs(os.path.join(team_dir, subdir), exist_ok=True)
    
    # Créer un fichier de configuration d'équipe
    config_path = os.path.join(team_dir, 'config.json')
    default_config = {
        "id": team_name,
        "name": "Default Team",
        "agents": [
            {"name": "default_agent", "type": "aider", "weight": 0.5}
        ]
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)

def migrate_project():
    """Migrer un projet existant vers la structure team-local"""
    if not detect_existing_project_structure():
        print("Ce script doit être exécuté à la racine d'un projet Python.")
        return
    
    # Créer la structure d'équipe par défaut
    create_default_team_structure()
    
    print("Migration vers la structure team-local terminée.")

if __name__ == '__main__':
    migrate_project()
