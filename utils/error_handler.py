from flask import jsonify
from typing import Tuple, Dict, Any

"""Centralized error handling for KinOS"""
from typing import Dict, Any, Tuple
from datetime import datetime
import traceback
from flask import jsonify
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError

class ErrorHandler:
    """Centralised error handling for the application"""
    
    @staticmethod
    def handle_error(error: Exception, status_code: int = 500) -> Tuple[Dict[str, Any], int]:
        """Handle any exception with detailed error response"""
        error_details = {
            'error': str(error),
            'type': error.__class__.__name__,
            'details': {
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat(),
                'additional_info': getattr(error, 'additional_info', None)
            }
        }
        
        # Log the detailed error
        print(f"[ERROR] {error_details['type']}: {error_details['error']}")
        print(f"Traceback:\n{error_details['details']['traceback']}")
        
        return jsonify(error_details), status_code

    @staticmethod
    def validation_error(message: str) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors with details"""
        return ErrorHandler.handle_error(ValidationError(message), 400)

    @staticmethod
    def not_found_error(message: str) -> Tuple[Dict[str, Any], int]:
        """Handle not found errors with details"""
        return ErrorHandler.handle_error(ResourceNotFoundError(message), 404)

    @staticmethod
    def service_error(message: str) -> Tuple[Dict[str, Any], int]:
        """Handle service errors with details"""
        return ErrorHandler.handle_error(ServiceError(message), 500)
