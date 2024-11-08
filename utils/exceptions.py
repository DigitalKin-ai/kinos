class KinOSError(Exception):
    """Base exception for KinOS application"""
    pass

class ValidationError(KinOSError):
    """Raised when input validation fails"""
    pass

class ResourceNotFoundError(KinOSError):
    """Raised when a requested resource is not found"""
    pass

class ServiceError(KinOSError):
    """Raised when a service operation fails"""
    pass

class AgentError(KinOSError):
    """Raised when an agent operation fails"""
    pass

class FileOperationError(KinOSError):
    """Raised when a file operation fails"""
    pass
