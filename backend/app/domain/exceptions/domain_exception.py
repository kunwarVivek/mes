class DomainException(Exception):
    """Base exception for domain-related errors"""
    pass


class DomainValidationException(DomainException):
    """Exception raised when domain validation fails"""
    pass


class EntityNotFoundException(DomainException):
    """Exception raised when an entity is not found"""
    pass


class DuplicateEntityException(DomainException):
    """Exception raised when attempting to create a duplicate entity"""
    pass
