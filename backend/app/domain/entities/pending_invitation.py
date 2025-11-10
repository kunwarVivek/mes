"""
PendingInvitation domain entity - Team member invitation tracking

Represents pending team member invitations for onboarding.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PendingInvitation:
    """
    PendingInvitation entity - Tracks team invitation lifecycle

    Business Rules:
    - token must be cryptographically secure (32 bytes hex)
    - expires_at enforced (7 days from creation)
    - One invitation per email per organization (unique constraint)
    - Custom role requires role_description
    """
    id: Optional[int]
    organization_id: int
    email: str
    role: str  # admin, operator, viewer, custom
    role_description: Optional[str]
    token: str  # 32 bytes hex (64 characters)
    expires_at: datetime
    created_at: datetime
    invited_by_user_id: int

    def __post_init__(self):
        """Validate invitation data"""
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")

        if self.role not in ['admin', 'operator', 'viewer', 'custom']:
            raise ValueError("Invalid role. Must be admin, operator, viewer, or custom")

        if self.role == 'custom' and not self.role_description:
            raise ValueError("role_description required for custom role")

        if not self.token or len(self.token) != 64:
            raise ValueError("token must be 64 character hex string (32 bytes)")

    def is_expired(self) -> bool:
        """Check if invitation is expired"""
        return datetime.utcnow() >= self.expires_at
