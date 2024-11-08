import pytest
from utils.error_handler import ErrorHandler
from utils.exceptions import ValidationError, ResourceNotFoundError, ServiceError

def test_handle_error():
    """Test generic error handling"""
    error = Exception("Test error")
    response, status_code = ErrorHandler.handle_error(error)
    assert response.json["error"] == "Test error"
    assert response.json["type"] == "Exception"
    assert status_code == 500

def test_validation_error():
    """Test validation error handling"""
    response, status_code = ErrorHandler.validation_error("Invalid input")
    assert response.json["error"] == "Invalid input"
    assert status_code == 400

def test_not_found_error():
    """Test not found error handling"""
    response, status_code = ErrorHandler.not_found_error("Resource")
    assert response.json["error"] == "Resource not found"
    assert status_code == 404

def test_service_error():
    """Test service error handling"""
    response, status_code = ErrorHandler.service_error("Service failed")
    assert response.json["error"] == "Service failed"
    assert status_code == 500

def test_custom_exceptions():
    """Test handling of custom exceptions"""
    errors = [
        (ValidationError("Invalid"), 400),
        (ResourceNotFoundError("Missing"), 404),
        (ServiceError("Failed"), 500)
    ]
    
    for error, expected_code in errors:
        response, status_code = ErrorHandler.handle_error(error)
        assert status_code == expected_code
        assert response.json["error"] == str(error)
