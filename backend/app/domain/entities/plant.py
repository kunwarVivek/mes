"""
Plant domain entity - Manufacturing site within organization

Represents physical manufacturing locations with independent operations.
Sub-tenant level isolation for multi-plant organizations.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Plant:
    """
    Plant entity - Manufacturing site and sub-tenant boundary

    Business Rules:
    - plant_code unique within organization (not globally)
    - Each plant has independent work centers, inventory, production
    - RLS policies can filter by plant_id for plant-level isolation
    - is_active controls access to plant data
    """
    id: int
    organization_id: int
    plant_code: str        # Unique within org (e.g., "PLANT01", "NASHVILLE")
    plant_name: str        # Display name (e.g., "Nashville Assembly Plant")
    location: Optional[str] # Physical address/location description
    is_active: bool        # Plant operational status
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate plant data"""
        if not self.plant_code or len(self.plant_code) > 20:
            raise ValueError("plant_code must be 1-20 characters")

        if not self.plant_name or len(self.plant_name) > 200:
            raise ValueError("plant_name must be 1-200 characters")

        if self.location and len(self.location) > 500:
            raise ValueError("location must be ≤500 characters")
