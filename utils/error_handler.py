import traceback
from flask import jsonify
from datetime import datetime
from utils.logger import Logger
from utils.exceptions import KinOSBaseException

class ErrorHandler:
    @staticmethod
    def handle_error(
        error, 
        log_level: str = 'error', 
        include_traceback: bool = True
    ):
        """
        Centralized error handling with detailed information
        
        Args:
            error (Exception): The raised exception
            log_level (str): Logging level
            include_traceback (bool): Whether to include full traceback
        
        Returns:
            flask.Response: JSON response with error details
        """
        logger = Logger()
        
        # Determine error details
        error_details = {
            'error': str(error),
            'type': error.__class__.__name__,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }
        
        # Add traceback if requested
        if include_traceback:
            error_details['details']['traceback'] = traceback.format_exc()
        
        # Add additional context for KinOS exceptions
        if isinstance(error, KinOSBaseException):
            error_details['details'].update(error.additional_info or {})
        
        # HTTP status code mapping
        status_map = {
            'ValidationError': 400,
            'ResourceNotFoundError': 404,
            'AuthenticationError': 401,
            'PermissionError': 403,
            'ServiceError': 500
        }
        
        # Determine status code
        status_code = status_map.get(error.__class__.__name__, 500)
        
        # Log the error
        logger.log(f"Error: {error_details}", log_level)
        
        return jsonify(error_details), status_code

    @staticmethod
    def validation_error(message: str, additional_info: dict = None):
        """Create a validation error response"""
        from utils.exceptions import ValidationError
        error = ValidationError(message, additional_info)
        return ErrorHandler.handle_error(error, log_level='warning')

    @staticmethod
    def not_found_error(message: str, additional_info: dict = None):
        """Create a not found error response"""
        from utils.exceptions import ResourceNotFoundError
        error = ResourceNotFoundError(message, additional_info)
        return ErrorHandler.handle_error(error, log_level='warning')

    @staticmethod
    def service_error(message: str, additional_info: dict = None):
        """Create a service error response"""
        from utils.exceptions import ServiceError
        error = ServiceError(message, additional_info)
        return ErrorHandler.handle_error(error, log_level='error')
