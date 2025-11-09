"""
Domain entities for Quality Management - NCR (Non-Conformance Report).
Pure Python classes representing quality business domain concepts.
"""
from datetime import datetime
from typing import Optional
from enum import Enum


class NCRStatus(str, Enum):
    """NCR workflow status"""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class NCRDomain:
    """Domain entity for Non-Conformance Report (NCR)"""

    def __init__(
        self,
        id: Optional[int],
        organization_id: int,
        plant_id: int,
        ncr_number: str,
        work_order_id: int,
        material_id: int,
        defect_type: str,
        defect_description: str,
        quantity_defective: float,
        status: NCRStatus,
        reported_by_user_id: int,
        attachment_urls: Optional[list] = None,
        resolution_notes: Optional[str] = None,
        resolved_by_user_id: Optional[int] = None,
        resolved_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self._id = id
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._ncr_number = ncr_number.upper().strip()
        self._work_order_id = work_order_id
        self._material_id = material_id
        self._defect_type = defect_type
        self._defect_description = defect_description
        self._quantity_defective = quantity_defective
        self._status = status
        self._reported_by_user_id = reported_by_user_id
        self._attachment_urls = attachment_urls or []
        self._resolution_notes = resolution_notes
        self._resolved_by_user_id = resolved_by_user_id
        self._resolved_at = resolved_at
        self._created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate NCR business rules"""
        if self._organization_id <= 0:
            raise ValueError("Organization ID must be positive")
        if self._plant_id <= 0:
            raise ValueError("Plant ID must be positive")
        if not self._ncr_number:
            raise ValueError("NCR number cannot be empty")
        if self._work_order_id <= 0:
            raise ValueError("Work order ID must be positive")
        if self._material_id <= 0:
            raise ValueError("Material ID must be positive")
        if self._quantity_defective <= 0:
            raise ValueError("Quantity defective must be positive")
        if self._defect_type not in ["DIMENSIONAL", "VISUAL", "FUNCTIONAL", "MATERIAL", "OTHER"]:
            raise ValueError("Invalid defect type")
        if not self._defect_description:
            raise ValueError("Defect description cannot be empty")

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def organization_id(self) -> int:
        return self._organization_id

    @property
    def plant_id(self) -> int:
        return self._plant_id

    @property
    def ncr_number(self) -> str:
        return self._ncr_number

    @property
    def work_order_id(self) -> int:
        return self._work_order_id

    @property
    def material_id(self) -> int:
        return self._material_id

    @property
    def defect_type(self) -> str:
        return self._defect_type

    @property
    def defect_description(self) -> str:
        return self._defect_description

    @property
    def quantity_defective(self) -> float:
        return self._quantity_defective

    @property
    def status(self) -> NCRStatus:
        return self._status

    @property
    def reported_by_user_id(self) -> int:
        return self._reported_by_user_id

    @property
    def attachment_urls(self) -> list:
        return self._attachment_urls

    @property
    def resolution_notes(self) -> Optional[str]:
        return self._resolution_notes

    def move_to_review(self) -> None:
        """Business logic: Move NCR to review status"""
        if self._status != NCRStatus.OPEN:
            raise ValueError("NCR can only move to review from OPEN status")
        self._status = NCRStatus.IN_REVIEW

    def resolve(self, resolution_notes: str, resolved_by_user_id: int) -> None:
        """Business logic: Resolve NCR"""
        if self._status != NCRStatus.IN_REVIEW:
            raise ValueError("NCR can only be resolved from IN_REVIEW status")
        if not resolution_notes:
            raise ValueError("Resolution notes are required")
        self._status = NCRStatus.RESOLVED
        self._resolution_notes = resolution_notes
        self._resolved_by_user_id = resolved_by_user_id
        self._resolved_at = datetime.utcnow()

    def close(self) -> None:
        """Business logic: Close NCR"""
        if self._status != NCRStatus.RESOLVED:
            raise ValueError("NCR can only be closed from RESOLVED status")
        self._status = NCRStatus.CLOSED

    def add_attachment(self, url: str) -> None:
        """Business logic: Add attachment URL"""
        if not url:
            raise ValueError("Attachment URL cannot be empty")
        self._attachment_urls.append(url)

    def __repr__(self):
        return f"<NCR(number='{self._ncr_number}', status='{self._status}')>"
