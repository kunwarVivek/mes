"""
Unit tests for POQ (Period Order Quantity) lot sizing strategy.
Following TDD approach: RED -> GREEN -> REFACTOR

POQ aggregates demand over N periods and places one order to cover the entire period.
Period types: DAILY, WEEKLY, MONTHLY
"""
import pytest
from datetime import datetime, timedelta
from app.domain.services.lot_sizing_service import LotSizingService


class TestPOQLotSizing:
    """Test POQ (Period Order Quantity) lot sizing strategy"""

    @pytest.fixture
    def lot_sizing_service(self):
        """Create lot sizing service instance"""
        return LotSizingService()

    def test_poq_daily_single_period(self, lot_sizing_service):
        """
        RED TEST: POQ with daily periods, 1 period
        Should aggregate 1 day of demand
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=1
        )

        # Assert
        assert result == 100.0

    def test_poq_daily_multiple_periods(self, lot_sizing_service):
        """
        RED TEST: POQ with daily periods, 3 periods
        Should aggregate 3 days of demand
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
            {'period': datetime(2025, 1, 2), 'quantity': 150.0},
            {'period': datetime(2025, 1, 3), 'quantity': 200.0},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=3
        )

        # Assert
        assert result == 450.0  # 100 + 150 + 200

    def test_poq_weekly_single_week(self, lot_sizing_service):
        """
        RED TEST: POQ with weekly periods, 1 week
        Should aggregate 1 week (7 days) of demand
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
            {'period': datetime(2025, 1, 2), 'quantity': 150.0},
            {'period': datetime(2025, 1, 3), 'quantity': 200.0},
            {'period': datetime(2025, 1, 4), 'quantity': 120.0},
            {'period': datetime(2025, 1, 5), 'quantity': 180.0},
            {'period': datetime(2025, 1, 6), 'quantity': 90.0},
            {'period': datetime(2025, 1, 7), 'quantity': 160.0},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='WEEKLY',
            periods_to_cover=1
        )

        # Assert
        assert result == 1000.0  # Sum of all 7 days

    def test_poq_weekly_multiple_weeks(self, lot_sizing_service):
        """
        RED TEST: POQ with weekly periods, 2 weeks
        Should aggregate 2 weeks (14 days) of demand
        """
        # Arrange
        requirements = []
        for day in range(14):
            requirements.append({
                'period': datetime(2025, 1, 1) + timedelta(days=day),
                'quantity': 100.0
            })

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='WEEKLY',
            periods_to_cover=2
        )

        # Assert
        assert result == 1400.0  # 14 days * 100

    def test_poq_monthly_single_month(self, lot_sizing_service):
        """
        RED TEST: POQ with monthly periods, 1 month
        Should aggregate 1 month (30 days) of demand
        """
        # Arrange
        requirements = []
        for day in range(30):
            requirements.append({
                'period': datetime(2025, 1, 1) + timedelta(days=day),
                'quantity': 50.0
            })

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='MONTHLY',
            periods_to_cover=1
        )

        # Assert
        assert result == 1500.0  # 30 days * 50

    def test_poq_monthly_multiple_months(self, lot_sizing_service):
        """
        RED TEST: POQ with monthly periods, 2 months
        Should aggregate 2 months (60 days) of demand
        """
        # Arrange
        requirements = []
        for day in range(60):
            requirements.append({
                'period': datetime(2025, 1, 1) + timedelta(days=day),
                'quantity': 25.0
            })

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='MONTHLY',
            periods_to_cover=2
        )

        # Assert
        assert result == 1500.0  # 60 days * 25

    def test_poq_with_zero_requirements(self, lot_sizing_service):
        """
        RED TEST: POQ with zero requirements
        Should return 0.0
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 0.0},
            {'period': datetime(2025, 1, 2), 'quantity': 0.0},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=2
        )

        # Assert
        assert result == 0.0

    def test_poq_with_partial_period_coverage(self, lot_sizing_service):
        """
        RED TEST: POQ with partial period coverage
        If requirements have fewer periods than requested, cover what's available
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
            {'period': datetime(2025, 1, 2), 'quantity': 150.0},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=5  # Request 5, but only 2 available
        )

        # Assert
        assert result == 250.0  # Only sum available periods

    def test_poq_invalid_period_type(self, lot_sizing_service):
        """
        RED TEST: POQ with invalid period type
        Should raise ValueError
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid period type"):
            lot_sizing_service.calculate_poq_lot_size(
                requirements=requirements,
                period_type='INVALID',
                periods_to_cover=1
            )

    def test_poq_invalid_periods_to_cover(self, lot_sizing_service):
        """
        RED TEST: POQ with invalid periods_to_cover (zero or negative)
        Should raise ValueError
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="periods_to_cover must be positive"):
            lot_sizing_service.calculate_poq_lot_size(
                requirements=requirements,
                period_type='DAILY',
                periods_to_cover=0
            )

    def test_poq_empty_requirements(self, lot_sizing_service):
        """
        RED TEST: POQ with empty requirements list
        Should return 0.0
        """
        # Arrange
        requirements = []

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=1
        )

        # Assert
        assert result == 0.0

    def test_poq_with_fractional_quantities(self, lot_sizing_service):
        """
        RED TEST: POQ with fractional quantities
        Should handle decimal values correctly
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 10.5},
            {'period': datetime(2025, 1, 2), 'quantity': 20.3},
            {'period': datetime(2025, 1, 3), 'quantity': 15.7},
        ]

        # Act
        result = lot_sizing_service.calculate_poq_lot_size(
            requirements=requirements,
            period_type='DAILY',
            periods_to_cover=3
        )

        # Assert
        assert result == 46.5  # 10.5 + 20.3 + 15.7


class TestPOQIntegrationWithLotSizingService:
    """Test POQ integration with main calculate_lot_size method"""

    @pytest.fixture
    def lot_sizing_service(self):
        """Create lot sizing service instance"""
        return LotSizingService()

    def test_calculate_lot_size_with_poq_rule(self, lot_sizing_service):
        """
        RED TEST: Test calculate_lot_size with POQ rule
        Should call POQ calculation method
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
            {'period': datetime(2025, 1, 2), 'quantity': 150.0},
            {'period': datetime(2025, 1, 3), 'quantity': 200.0},
        ]

        # Act
        result = lot_sizing_service.calculate_lot_size(
            material_id=1,
            net_requirement=0,  # Not used for POQ
            lot_sizing_rule='POQ',
            poq_requirements=requirements,
            poq_period_type='DAILY',
            poq_periods_to_cover=3
        )

        # Assert
        assert result == 450.0

    def test_calculate_lot_size_poq_missing_requirements(self, lot_sizing_service):
        """
        RED TEST: Test calculate_lot_size with POQ but missing requirements
        Should raise ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError, match="POQ requires requirements list"):
            lot_sizing_service.calculate_lot_size(
                material_id=1,
                net_requirement=0,
                lot_sizing_rule='POQ',
                poq_period_type='DAILY',
                poq_periods_to_cover=3
            )

    def test_calculate_lot_size_poq_missing_period_type(self, lot_sizing_service):
        """
        RED TEST: Test calculate_lot_size with POQ but missing period_type
        Should raise ValueError
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="POQ requires period_type"):
            lot_sizing_service.calculate_lot_size(
                material_id=1,
                net_requirement=0,
                lot_sizing_rule='POQ',
                poq_requirements=requirements,
                poq_periods_to_cover=3
            )

    def test_calculate_lot_size_poq_missing_periods_to_cover(self, lot_sizing_service):
        """
        RED TEST: Test calculate_lot_size with POQ but missing periods_to_cover
        Should raise ValueError
        """
        # Arrange
        requirements = [
            {'period': datetime(2025, 1, 1), 'quantity': 100.0},
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="POQ requires periods_to_cover"):
            lot_sizing_service.calculate_lot_size(
                material_id=1,
                net_requirement=0,
                lot_sizing_rule='POQ',
                poq_requirements=requirements,
                poq_period_type='DAILY'
            )
