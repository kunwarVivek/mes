"""
Organization domain entity - Multi-tenant foundation

Represents the top-level organizational structure for B2B SaaS multi-tenancy.
Each organization is a customer with independent data isolation via RLS.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Organization:
    """
    Organization entity - Top-level multi-tenant boundary

    Business Rules:
    - org_code must be globally unique (used in API routing)
    - subdomain must be unique (for white-label access)
    - is_active controls access to all child data (plants, users, etc.)
    - Row-Level Security (RLS) policies enforce data isolation
    """
    id: int
    org_code: str           # Unique identifier (e.g., "ACME", "EMERSON")
    org_name: str           # Display name (e.g., "Acme Manufacturing Inc.")
    subdomain: Optional[str] # For white-label access (e.g., "acme.unison.app")
    is_active: bool         # Master switch for organization access
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate organization data"""
        if not self.org_code or len(self.org_code) > 20:
            raise ValueError("org_code must be 1-20 characters")

        if not self.org_name or len(self.org_name) > 200:
            raise ValueError("org_name must be 1-200 characters")

        if self.subdomain and len(self.subdomain) > 100:
            raise ValueError("subdomain must be ≤100 characters")
