"""
Department domain entity - Organizational unit within plant

Represents functional departments (Production, Quality, Maintenance, etc.)
for organizing users and workflows.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Department:
    """
    Department entity - Functional unit within plant

    Business Rules:
    - dept_code unique within plant (not globally)
    - Used for user assignment and role-based access
    - Maps to PRD's organizational hierarchy
    - Optional department-level reporting and metrics
    """
    id: int
    plant_id: int
    dept_code: str         # Unique within plant (e.g., "PROD", "QA", "MAINT")
    dept_name: str         # Display name (e.g., "Production", "Quality Assurance")
    description: Optional[str]  # Purpose and responsibilities
    is_active: bool        # Department operational status
    created_at: datetime
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate department data"""
        if not self.dept_code or len(self.dept_code) > 20:
            raise ValueError("dept_code must be 1-20 characters")

        if not self.dept_name or len(self.dept_name) > 200:
            raise ValueError("dept_name must be 1-200 characters")

        if self.description and len(self.description) > 1000:
            raise ValueError("description must be ≤1000 characters")
