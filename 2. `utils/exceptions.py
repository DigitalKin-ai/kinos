class KinosCLIError(Exception):
    """Exception de base pour les erreurs CLI"""
    pass

class MissionNotFoundError(KinosCLIError):
    """Erreur lorsqu'une mission n'est pas trouvée"""
    pass

class TeamNotFoundError(KinosCLIError):
    """Erreur lorsqu'une équipe n'est pas trouvée"""
    pass

class TeamActivationError(KinosCLIError):
    """Erreur lors de l'activation d'une équipe"""
    pass
