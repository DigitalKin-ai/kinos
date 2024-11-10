import os

class PathManager:
    """Gestionnaire centralisé des chemins pour KinOS"""
    
    @staticmethod
    def get_project_root() -> str:
        """Retourne le chemin racine du projet"""
        # Remonte jusqu'à trouver le dossier racine du projet (contenant missions/)
        current = os.path.abspath(__file__)
        while current:
            if os.path.exists(os.path.join(current, "missions")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        raise ValueError("Project root not found")

    @staticmethod
    def get_mission_path(mission_name: str) -> str:
        """Retourne le chemin absolu vers une mission"""
        root = PathManager.get_project_root()
        return os.path.join(root, "missions", mission_name)

    @staticmethod
    def get_prompts_path() -> str:
        """Retourne le chemin vers le dossier des prompts"""
        return os.path.join(PathManager.get_project_root(), "prompts")

    @staticmethod
    def get_config_path() -> str:
        """Retourne le chemin vers le dossier de configuration"""
        return os.path.join(PathManager.get_project_root(), "config")
