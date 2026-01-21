"""
Custom exceptions.
"""

class ServiceException(Exception):
    """Base exception for service layer errors."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'error'
        super().__init__(self.message)


class NotFoundError(ServiceException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code='not_found')


class ValidationError(ServiceException):
    """Raised when validation fails in the service layer."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code='validation_error')


class PermissionDeniedError(ServiceException):
    """Raised when a user doesn't have permission to perform an action."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code='permission_denied')


class ConflictError(ServiceException):
    """Raised when there is a conflict with the current state."""
    
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, code='conflict')
