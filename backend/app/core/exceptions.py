"""
Custom exception hierarchy for the MES application.

This module defines domain-specific exceptions that represent business logic errors,
validation failures, and other exceptional conditions. These exceptions are mapped
to appropriate HTTP status codes by the global exception handler.
"""


class DomainException(Exception):
    """
    Base exception for all domain-level errors.

    Domain exceptions represent business rule violations, validation errors,
    and other logical errors that are expected and should be handled gracefully.
    """

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """
    Raised when a requested entity cannot be found in the database.

    Example: Requesting work order with ID 123 that doesn't exist.
    HTTP Status: 404 Not Found
    """

    def __init__(self, entity_type: str, entity_id: any, details: dict = None):
        message = f"{entity_type} with ID '{entity_id}' not found"
        super().__init__(message, details)
        self.entity_type = entity_type
        self.entity_id = entity_id


class ValidationException(DomainException):
    """
    Raised when business rule validation fails.

    Examples:
    - Quantity to issue exceeds available inventory
    - Work order status transition is invalid
    - Start date is after end date
    - Lane already occupied by another work order

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field


class UnauthorizedException(DomainException):
    """
    Raised when user lacks permission to perform an action.

    Examples:
    - User tries to delete work order without delete permission
    - User tries to access data from another organization (RLS violation)

    HTTP Status: 403 Forbidden
    """

    def __init__(self, message: str = "You don't have permission to perform this action", details: dict = None):
        super().__init__(message, details)


class DuplicateEntityException(DomainException):
    """
    Raised when attempting to create an entity that already exists.

    Examples:
    - Material code already exists
    - Work order number is duplicate
    - Email already registered

    HTTP Status: 409 Conflict
    """

    def __init__(self, entity_type: str, field: str, value: any, details: dict = None):
        message = f"{entity_type} with {field}='{value}' already exists"
        super().__init__(message, details)
        self.entity_type = entity_type
        self.field = field
        self.value = value


class BusinessRuleViolationException(DomainException):
    """
    Raised when an operation violates a business rule.

    Examples:
    - Cannot deactivate material with active inventory
    - Cannot close NCR without root cause analysis (for critical severity)
    - Cannot complete work order with incomplete operations

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, rule: str, message: str, details: dict = None):
        super().__init__(message, details)
        self.rule = rule


class InsufficientInventoryException(ValidationException):
    """
    Raised when material quantity is insufficient for the requested operation.

    Examples:
    - Trying to issue 100 units when only 50 available
    - Negative inventory would result from operation

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, material_code: str, requested: float, available: float):
        message = f"Insufficient inventory for material '{material_code}'. Requested: {requested}, Available: {available}"
        super().__init__(message, field="quantity")
        self.material_code = material_code
        self.requested = requested
        self.available = available


class InvalidStateTransitionException(BusinessRuleViolationException):
    """
    Raised when an invalid state transition is attempted.

    Examples:
    - Work order status: COMPLETED → IN_PROGRESS (invalid)
    - NCR status: CLOSED → OPEN (invalid)

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, entity_type: str, current_state: str, requested_state: str, valid_transitions: list):
        message = (
            f"Invalid {entity_type} state transition: {current_state} → {requested_state}. "
            f"Valid transitions from {current_state}: {', '.join(valid_transitions)}"
        )
        super().__init__(
            rule=f"{entity_type}_state_transition",
            message=message,
            details={
                "current_state": current_state,
                "requested_state": requested_state,
                "valid_transitions": valid_transitions
            }
        )
        self.entity_type = entity_type
        self.current_state = current_state
        self.requested_state = requested_state


class ConflictException(DomainException):
    """
    Raised when a resource conflict is detected.

    Examples:
    - Lane already occupied by another work order in the same time period
    - Machine already scheduled for maintenance

    HTTP Status: 409 Conflict
    """

    def __init__(self, resource_type: str, message: str, details: dict = None):
        super().__init__(message, details)
        self.resource_type = resource_type


class CostingException(DomainException):
    """
    Raised when cost calculation fails.

    Examples:
    - No cost layers available for FIFO costing
    - Division by zero in unit cost calculation

    HTTP Status: 422 Unprocessable Entity
    """

    def __init__(self, message: str, costing_method: str = None, details: dict = None):
        super().__init__(message, details)
        self.costing_method = costing_method


class IntegrationException(DomainException):
    """
    Raised when external system integration fails.

    Examples:
    - SAP ERP sync failure
    - MinIO file upload failure
    - Email send failure

    HTTP Status: 502 Bad Gateway
    """

    def __init__(self, system: str, message: str, details: dict = None):
        super().__init__(f"{system} integration error: {message}", details)
        self.system = system


class ConfigurationException(DomainException):
    """
    Raised when system configuration is invalid or missing.

    Examples:
    - Missing costing method for organization
    - Invalid email template configuration
    - Missing SAP credentials

    HTTP Status: 500 Internal Server Error
    """

    def __init__(self, config_key: str, message: str, details: dict = None):
        super().__init__(f"Configuration error ({config_key}): {message}", details)
        self.config_key = config_key
