from flask import jsonify
from typing import Tuple, Dict, Any

class ErrorHandler:
    """Centralised error handling for the application"""
    
    @staticmethod
    def handle_error(error: Exception, status_code: int = 500) -> Tuple[Dict[str, Any], int]:
        """
        Handle any exception and return appropriate response
        
        Args:
            error: The exception that occurred
            status_code: HTTP status code to return
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            'error': str(error),
            'type': error.__class__.__name__
        }
        
        # Add stack trace in debug mode
        if hasattr(error, 'stack_trace'):
            response['stack_trace'] = error.stack_trace
            
        return jsonify(response), status_code
        
    @staticmethod
    def validation_error(message: str) -> Tuple[Dict[str, str], int]:
        """Handle validation errors"""
        return jsonify({'error': message}), 400
        
    @staticmethod
    def not_found_error(resource: str) -> Tuple[Dict[str, str], int]:
        """Handle not found errors"""
        return jsonify({'error': f'{resource} not found'}), 404
        
    @staticmethod
    def service_error(message: str) -> Tuple[Dict[str, str], int]:
        """Handle service-level errors"""
        return jsonify({'error': message}), 500
