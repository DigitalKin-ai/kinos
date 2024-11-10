from datetime import datetime
from typing import Optional, Dict, Any

class KinOSBaseException(Exception):
    """Base exception for KinOS with enriched information"""
    
    def __init__(
        self, 
        message: str, 
        additional_info: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        """
        Initialize an exception with additional context
        
        Args:
            message (str): Error message
            additional_info (dict, optional): Supplementary error information
            error_code (str, optional): Unique error identifier
        """
        super().__init__(message)
        self.additional_info = additional_info or {}
        self.timestamp = datetime.now().isoformat()
        self.error_code = error_code or self._generate_error_code()
        
    def _generate_error_code(self) -> str:
        """Generate a unique error code"""
        import uuid
        return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to a dictionary for serialization
        
        Returns:
            dict: Exception representation
        """
        return {
            'message': str(self),
            'type': self.__class__.__name__,
            'timestamp': self.timestamp,
            'error_code': self.error_code,
            'additional_info': self.additional_info
        }

class ServiceError(KinOSBaseException):
    """Generic service-level error"""
    pass

class ValidationError(KinOSBaseException):
    """Data validation error"""
    pass

class ResourceNotFoundError(KinOSBaseException):
    """Resource not found error"""
    pass

class AuthenticationError(KinOSBaseException):
    """Authentication-related error"""
    pass

class PermissionError(KinOSBaseException):
    """Permission-related error"""
    pass

class AgentError(KinOSBaseException):
    """Agent-related error"""
    pass

class FileOperationError(KinOSBaseException):
    """File operation error"""
    pass
