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

    @staticmethod
    def get_templates_path() -> str:
        """Retourne le chemin vers le dossier des templates"""
        return os.path.join(PathManager.get_project_root(), "templates")

    @staticmethod
    def get_static_path() -> str:
        """Retourne le chemin vers le dossier static"""
        return os.path.join(PathManager.get_project_root(), "static")

    @staticmethod
    def get_logs_path() -> str:
        """Retourne le chemin vers le dossier des logs"""
        logs_dir = os.path.join(PathManager.get_project_root(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir

    @staticmethod
    def get_temp_path() -> str:
        """Retourne le chemin vers le dossier temp"""
        temp_dir = os.path.join(PathManager.get_project_root(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @staticmethod
    def get_temp_file(prefix: str = "", suffix: str = "") -> str:
        """Crée un chemin de fichier temporaire"""
        import uuid
        temp_dir = PathManager.get_temp_path()
        return os.path.join(temp_dir, f"{prefix}{uuid.uuid4()}{suffix}")

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalise un chemin de fichier"""
        return os.path.normpath(os.path.abspath(path))
