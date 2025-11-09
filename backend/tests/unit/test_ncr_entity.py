"""
Unit tests for NCR (Non-Conformance Report) domain entities.

Test Coverage (TDD - RED phase):
- NCRDomain: Workflow transitions, validation
- InspectionPlanDomain: Characteristics, tolerances
- InspectionLogDomain: Pass/fail results
- FPY calculation logic
"""

import pytest
from datetime import datetime


class TestNCRDomain:
    """Test NCR domain entity business logic"""

    def test_create_ncr_with_valid_data(self):
        """Should create NCR with valid data"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="DIMENSIONAL",
            defect_description="Part dimension out of tolerance",
            quantity_defective=5.0,
            status=NCRStatus.OPEN,
            reported_by_user_id=1
        )

        assert ncr.ncr_number == "NCR-2025-001"
        assert ncr.defect_type == "DIMENSIONAL"
        assert ncr.quantity_defective == 5.0
        assert ncr.status == NCRStatus.OPEN
        assert ncr.organization_id == 1

    def test_ncr_workflow_open_to_review(self):
        """Should transition NCR from OPEN to IN_REVIEW"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="VISUAL",
            defect_description="Surface scratches",
            quantity_defective=3.0,
            status=NCRStatus.OPEN,
            reported_by_user_id=1
        )

        ncr.move_to_review()
        assert ncr.status == NCRStatus.IN_REVIEW

    def test_ncr_workflow_review_to_resolved(self):
        """Should transition NCR from IN_REVIEW to RESOLVED"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="FUNCTIONAL",
            defect_description="Component does not meet specs",
            quantity_defective=2.0,
            status=NCRStatus.IN_REVIEW,
            reported_by_user_id=1
        )

        ncr.resolve("Reworked parts, re-tested and passed", resolved_by_user_id=2)
        assert ncr.status == NCRStatus.RESOLVED
        assert ncr.resolution_notes == "Reworked parts, re-tested and passed"

    def test_ncr_workflow_resolved_to_closed(self):
        """Should transition NCR from RESOLVED to CLOSED"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="DIMENSIONAL",
            defect_description="Out of spec",
            quantity_defective=1.0,
            status=NCRStatus.RESOLVED,
            reported_by_user_id=1,
            resolution_notes="Fixed",
            resolved_by_user_id=2
        )

        ncr.close()
        assert ncr.status == NCRStatus.CLOSED

    def test_ncr_cannot_skip_workflow_steps(self):
        """Should enforce NCR workflow sequence"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="DIMENSIONAL",
            defect_description="Out of spec",
            quantity_defective=1.0,
            status=NCRStatus.OPEN,
            reported_by_user_id=1
        )

        # Cannot resolve from OPEN
        with pytest.raises(ValueError, match="can only be resolved from IN_REVIEW"):
            ncr.resolve("Attempted skip", resolved_by_user_id=2)

        # Cannot close from OPEN
        with pytest.raises(ValueError, match="can only be closed from RESOLVED"):
            ncr.close()

    def test_ncr_add_attachment(self):
        """Should add attachment URL to NCR"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        ncr = NCRDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            ncr_number="NCR-2025-001",
            work_order_id=1,
            material_id=1,
            defect_type="VISUAL",
            defect_description="Defect visible",
            quantity_defective=1.0,
            status=NCRStatus.OPEN,
            reported_by_user_id=1
        )

        ncr.add_attachment("s3://bucket/ncr-001-photo1.jpg")
        ncr.add_attachment("s3://bucket/ncr-001-photo2.jpg")

        assert len(ncr.attachment_urls) == 2
        assert "s3://bucket/ncr-001-photo1.jpg" in ncr.attachment_urls

    def test_ncr_validation_rules(self):
        """Should validate NCR business rules"""
        from app.domain.entities.ncr import NCRDomain, NCRStatus

        # Invalid organization_id
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            NCRDomain(
                id=None,
                organization_id=0,
                plant_id=1,
                ncr_number="NCR-001",
                work_order_id=1,
                material_id=1,
                defect_type="DIMENSIONAL",
                defect_description="Defect",
                quantity_defective=1.0,
                status=NCRStatus.OPEN,
                reported_by_user_id=1
            )

        # Invalid defect_type
        with pytest.raises(ValueError, match="Invalid defect type"):
            NCRDomain(
                id=None,
                organization_id=1,
                plant_id=1,
                ncr_number="NCR-001",
                work_order_id=1,
                material_id=1,
                defect_type="INVALID_TYPE",
                defect_description="Defect",
                quantity_defective=1.0,
                status=NCRStatus.OPEN,
                reported_by_user_id=1
            )


class TestInspectionPlanDomain:
    """Test Inspection Plan domain entity"""

    def test_create_inspection_plan(self):
        """Should create inspection plan with characteristics"""
        from app.domain.entities.inspection import InspectionPlanDomain, InspectionCharacteristic

        plan = InspectionPlanDomain(
            id=None,
            organization_id=1,
            plant_id=1,
            plan_name="Final Assembly Inspection",
            material_id=1,
            inspection_frequency="PER_LOT",
            sample_size=5,
            is_active=True
        )

        assert plan.plan_name == "Final Assembly Inspection"
        assert plan.inspection_frequency == "PER_LOT"
        assert plan.sample_size == 5


class TestFPYCalculation:
    """Test First Pass Yield (FPY) calculation logic"""

    def test_calculate_fpy_perfect_quality(self):
        """Should calculate 100% FPY when no defects"""
        from app.domain.entities.inspection import FPYCalculator

        fpy = FPYCalculator.calculate_fpy(
            total_inspected=100,
            total_passed=100
        )

        assert fpy == 1.0

    def test_calculate_fpy_with_defects(self):
        """Should calculate FPY correctly with defects"""
        from app.domain.entities.inspection import FPYCalculator

        fpy = FPYCalculator.calculate_fpy(
            total_inspected=100,
            total_passed=95
        )

        assert fpy == pytest.approx(0.95, rel=1e-9)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
