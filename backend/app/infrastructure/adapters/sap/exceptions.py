"""
SAP Adapter Exceptions
Custom exceptions for SAP integration error handling
"""


class SAPAdapterError(Exception):
    """Base exception for SAP adapter errors"""
    pass


class SAPConnectionError(SAPAdapterError):
    """Exception raised when SAP connection fails"""
    pass


class SAPDataNotFoundError(SAPAdapterError):
    """Exception raised when requested data not found in SAP"""
    pass


class SAPDataValidationError(SAPAdapterError):
    """Exception raised when SAP data validation fails"""
    pass


class SAPAuthenticationError(SAPAdapterError):
    """Exception raised when SAP authentication fails"""
    pass


class SAPTimeoutError(SAPAdapterError):
    """Exception raised when SAP request times out"""
    pass
