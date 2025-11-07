import re
from app.domain.exceptions.domain_exception import DomainValidationException


class Email:
    """Value Object: Email

    Immutable value object representing an email address.
    Validates email format and enforces business rules.
    """

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, value: str):
        if not value:
            raise DomainValidationException("Email cannot be empty")

        if not self._is_valid_email(value):
            raise DomainValidationException(f"Invalid email format: {value}")

        self._value = value.lower().strip()

    @property
    def value(self) -> str:
        return self._value

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.EMAIL_REGEX.match(email))

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
