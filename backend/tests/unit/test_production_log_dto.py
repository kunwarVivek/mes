"""
Unit tests for Production Log DTOs.

Tests Pydantic validation in the application layer.
TDD: Write tests FIRST, then implement DTOs.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError


class TestProductionLogCreateRequest:
    """Test ProductionLogCreateRequest DTO validation"""

    def test_create_valid_production_log_request(self):
        """Should create valid production log request with required fields"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        dto = ProductionLogCreateRequest(
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            quantity_produced=Decimal("50.500")
        )

        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.work_order_id == 100
        assert dto.quantity_produced == Decimal("50.500")
        assert dto.quantity_scrapped == Decimal("0")
        assert dto.quantity_reworked == Decimal("0")
        assert dto.operation_id is None
        assert dto.machine_id is None

    def test_create_with_all_fields(self):
        """Should create production log with all optional fields"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        dto = ProductionLogCreateRequest(
            organization_id=1,
            plant_id=2,
            work_order_id=100,
            operation_id=5,
            machine_id=10,
            quantity_produced=Decimal("100.000"),
            quantity_scrapped=Decimal("5.000"),
            quantity_reworked=Decimal("2.500"),
            operator_id=50,
            shift_id=3,
            notes="Production run completed successfully",
            custom_metadata={"batch": "A123", "temperature": 25.5}
        )

        assert dto.operation_id == 5
        assert dto.machine_id == 10
        assert dto.quantity_scrapped == Decimal("5.000")
        assert dto.quantity_reworked == Decimal("2.500")
        assert dto.operator_id == 50
        assert dto.shift_id == 3
        assert dto.notes == "Production run completed successfully"
        assert dto.custom_metadata["batch"] == "A123"

    def test_negative_organization_id_raises_error(self):
        """Should reject organization_id <= 0"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        with pytest.raises(ValidationError) as exc_info:
            ProductionLogCreateRequest(
                organization_id=0,
                plant_id=1,
                work_order_id=100,
                quantity_produced=Decimal("50")
            )

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('organization_id',) for error in errors)

    def test_negative_quantity_produced_raises_error(self):
        """Should reject negative quantity_produced"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        with pytest.raises(ValidationError) as exc_info:
            ProductionLogCreateRequest(
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                quantity_produced=Decimal("-10.5")
            )

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity_produced',) for error in errors)

    def test_negative_quantity_scrapped_raises_error(self):
        """Should reject negative quantity_scrapped"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        with pytest.raises(ValidationError) as exc_info:
            ProductionLogCreateRequest(
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                quantity_produced=Decimal("50"),
                quantity_scrapped=Decimal("-5")
            )

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity_scrapped',) for error in errors)

    def test_negative_quantity_reworked_raises_error(self):
        """Should reject negative quantity_reworked"""
        from app.application.dtos.production_log_dto import ProductionLogCreateRequest

        with pytest.raises(ValidationError) as exc_info:
            ProductionLogCreateRequest(
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                quantity_produced=Decimal("50"),
                quantity_reworked=Decimal("-2.5")
            )

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('quantity_reworked',) for error in errors)


class TestProductionLogResponse:
    """Test ProductionLogResponse DTO"""

    def test_response_from_orm_model(self):
        """Should create response DTO from ORM model attributes"""
        from app.application.dtos.production_log_dto import ProductionLogResponse

        # Simulate ORM model data
        class MockLog:
            id = 1
            organization_id = 1
            plant_id = 1
            work_order_id = 100
            operation_id = 5
            machine_id = 10
            timestamp = datetime(2025, 1, 15, 10, 30, 0)
            quantity_produced = Decimal("100.000")
            quantity_scrapped = Decimal("5.000")
            quantity_reworked = Decimal("2.500")
            operator_id = 50
            shift_id = 3
            notes = "Test production"
            custom_metadata = {"batch": "A123"}

        response = ProductionLogResponse.model_validate(MockLog())

        assert response.id == 1
        assert response.work_order_id == 100
        assert response.quantity_produced == Decimal("100.000")
        assert response.custom_metadata["batch"] == "A123"


class TestProductionSummaryResponse:
    """Test ProductionSummaryResponse DTO"""

    def test_create_production_summary(self):
        """Should create production summary with aggregated statistics"""
        from app.application.dtos.production_log_dto import ProductionSummaryResponse

        summary = ProductionSummaryResponse(
            work_order_id=100,
            total_produced=Decimal("1000.000"),
            total_scrapped=Decimal("50.000"),
            total_reworked=Decimal("25.000"),
            yield_rate=Decimal("93.02"),
            log_count=15,
            first_log=datetime(2025, 1, 15, 8, 0, 0),
            last_log=datetime(2025, 1, 15, 16, 30, 0)
        )

        assert summary.work_order_id == 100
        assert summary.total_produced == Decimal("1000.000")
        assert summary.yield_rate == Decimal("93.02")
        assert summary.log_count == 15
