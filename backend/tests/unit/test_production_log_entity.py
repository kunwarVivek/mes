"""
Unit tests for Production Log Domain Entity.

Tests business logic validation in the domain layer.
TDD: Write tests FIRST, then implement entity.
"""

import pytest
from datetime import datetime
from decimal import Decimal


class TestProductionLogDomain:
    """Test ProductionLogDomain entity validation"""

    def test_create_valid_production_log(self):
        """Should create valid production log entity"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=5,
            machine_id=10,
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            quantity_produced=Decimal("100.500"),
            quantity_scrapped=Decimal("5.250"),
            quantity_reworked=Decimal("2.125"),
            operator_id=50,
            shift_id=3,
            notes="Production run 1",
            custom_metadata={"batch": "A123"}
        )

        assert log.id == 1
        assert log.work_order_id == 100
        assert log.quantity_produced == Decimal("100.500")
        assert log.quantity_scrapped == Decimal("5.250")
        assert log.quantity_reworked == Decimal("2.125")

    def test_create_minimal_production_log(self):
        """Should create production log with only required fields"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=None,
            machine_id=None,
            timestamp=datetime.now(),
            quantity_produced=Decimal("50.000"),
            quantity_scrapped=Decimal("0"),
            quantity_reworked=Decimal("0"),
            operator_id=None,
            shift_id=None,
            notes=None,
            custom_metadata=None
        )

        assert log.quantity_produced == Decimal("50.000")
        assert log.quantity_scrapped == Decimal("0")
        assert log.operation_id is None
        assert log.custom_metadata is None

    def test_negative_quantity_produced_raises_error(self):
        """Should reject negative quantity_produced"""
        from app.domain.entities.production_log import ProductionLogDomain

        with pytest.raises(ValueError, match="quantity_produced cannot be negative"):
            ProductionLogDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                operation_id=None,
                machine_id=None,
                timestamp=datetime.now(),
                quantity_produced=Decimal("-10.5"),
                quantity_scrapped=Decimal("0"),
                quantity_reworked=Decimal("0"),
                operator_id=None,
                shift_id=None,
                notes=None,
                custom_metadata=None
            )

    def test_negative_quantity_scrapped_raises_error(self):
        """Should reject negative quantity_scrapped"""
        from app.domain.entities.production_log import ProductionLogDomain

        with pytest.raises(ValueError, match="quantity_scrapped cannot be negative"):
            ProductionLogDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                operation_id=None,
                machine_id=None,
                timestamp=datetime.now(),
                quantity_produced=Decimal("50"),
                quantity_scrapped=Decimal("-5"),
                quantity_reworked=Decimal("0"),
                operator_id=None,
                shift_id=None,
                notes=None,
                custom_metadata=None
            )

    def test_negative_quantity_reworked_raises_error(self):
        """Should reject negative quantity_reworked"""
        from app.domain.entities.production_log import ProductionLogDomain

        with pytest.raises(ValueError, match="quantity_reworked cannot be negative"):
            ProductionLogDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                work_order_id=100,
                operation_id=None,
                machine_id=None,
                timestamp=datetime.now(),
                quantity_produced=Decimal("50"),
                quantity_scrapped=Decimal("0"),
                quantity_reworked=Decimal("-2.5"),
                operator_id=None,
                shift_id=None,
                notes=None,
                custom_metadata=None
            )

    def test_total_quantity_calculation(self):
        """Should calculate total quantity correctly"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=None,
            machine_id=None,
            timestamp=datetime.now(),
            quantity_produced=Decimal("100.000"),
            quantity_scrapped=Decimal("5.000"),
            quantity_reworked=Decimal("2.500"),
            operator_id=None,
            shift_id=None,
            notes=None,
            custom_metadata=None
        )

        assert log.total_quantity == Decimal("107.500")

    def test_yield_rate_calculation(self):
        """Should calculate yield rate correctly"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=None,
            machine_id=None,
            timestamp=datetime.now(),
            quantity_produced=Decimal("93.000"),
            quantity_scrapped=Decimal("5.000"),
            quantity_reworked=Decimal("2.000"),
            operator_id=None,
            shift_id=None,
            notes=None,
            custom_metadata=None
        )

        # Total = 93 + 5 + 2 = 100
        # Yield = (93 / 100) * 100 = 93%
        assert log.yield_rate == Decimal("93.0")

    def test_yield_rate_zero_when_no_production(self):
        """Should return zero yield rate when total quantity is zero"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=None,
            machine_id=None,
            timestamp=datetime.now(),
            quantity_produced=Decimal("0"),
            quantity_scrapped=Decimal("0"),
            quantity_reworked=Decimal("0"),
            operator_id=None,
            shift_id=None,
            notes=None,
            custom_metadata=None
        )

        assert log.yield_rate == Decimal("0")

    def test_yield_rate_100_percent_when_no_scrap(self):
        """Should return 100% yield rate when no scrap or rework"""
        from app.domain.entities.production_log import ProductionLogDomain

        log = ProductionLogDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            work_order_id=100,
            operation_id=None,
            machine_id=None,
            timestamp=datetime.now(),
            quantity_produced=Decimal("100.000"),
            quantity_scrapped=Decimal("0"),
            quantity_reworked=Decimal("0"),
            operator_id=None,
            shift_id=None,
            notes=None,
            custom_metadata=None
        )

        assert log.yield_rate == Decimal("100")
