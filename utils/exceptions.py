class ParallagonError(Exception):
    """Base exception for Parallagon application"""
    pass

class ValidationError(ParallagonError):
    """Raised when input validation fails"""
    pass

class ResourceNotFoundError(ParallagonError):
    """Raised when a requested resource is not found"""
    pass

class ServiceError(ParallagonError):
    """Raised when a service operation fails"""
    pass

class AgentError(ParallagonError):
    """Raised when an agent operation fails"""
    pass

class FileOperationError(ParallagonError):
    """Raised when a file operation fails"""
    pass
