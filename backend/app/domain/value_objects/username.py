import re
from app.domain.exceptions.domain_exception import DomainValidationException


class Username:
    """Value Object: Username

    Immutable value object representing a username.
    Validates username format and enforces business rules.
    """

    MIN_LENGTH = 3
    MAX_LENGTH = 50
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')

    def __init__(self, value: str):
        if not value:
            raise DomainValidationException("Username cannot be empty")

        value = value.strip()

        if len(value) < self.MIN_LENGTH:
            raise DomainValidationException(
                f"Username must be at least {self.MIN_LENGTH} characters"
            )

        if len(value) > self.MAX_LENGTH:
            raise DomainValidationException(
                f"Username cannot exceed {self.MAX_LENGTH} characters"
            )

        if not self.USERNAME_REGEX.match(value):
            raise DomainValidationException(
                "Username can only contain letters, numbers, hyphens, and underscores"
            )

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __eq__(self, other) -> bool:
        if not isinstance(other, Username):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
