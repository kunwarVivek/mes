"""
Unit tests for SAP Costing Adapter - Material Costing Data Sync
RED Phase: Write failing tests first
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal


class TestCostingAdapterSync:
    """Test material costing data synchronization"""

    @pytest.mark.asyncio
    async def test_fetch_standard_cost_from_sap(self):
        """Should fetch standard cost from SAP"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_cost_data = {
            "Material": "MAT001",
            "Plant": "1000",
            "ValuationArea": "1000",
            "CostingType": "01",  # Standard cost
            "StandardPrice": "125.50",
            "PriceUnit": "1",
            "Currency": "USD",
            "ValidFrom": "2024-01-01"
        }

        with patch.object(client, 'execute_query', return_value=[sap_cost_data]):
            result = await adapter.fetch_standard_cost("MAT001", "1000")

            assert result.material_number == "MAT001"
            assert result.standard_cost == Decimal("125.50")
            assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_fetch_moving_average_price_from_sap(self):
        """Should fetch moving average price from SAP"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_cost_data = {
            "Material": "MAT002",
            "Plant": "1000",
            "ValuationArea": "1000",
            "PriceControl": "V",  # Moving average
            "MovingAveragePrice": "98.75",
            "PriceUnit": "1",
            "Currency": "USD",
            "TotalValueAtPrice": "9875.00",
            "TotalStock": "100.00"
        }

        with patch.object(client, 'execute_query', return_value=[sap_cost_data]):
            result = await adapter.fetch_moving_average_price("MAT002", "1000")

            assert result.material_number == "MAT002"
            assert result.moving_average_price == Decimal("98.75")
            assert result.total_value == Decimal("9875.00")

    @pytest.mark.asyncio
    async def test_sync_standard_cost_to_unison(self):
        """Should sync standard cost from SAP to Unison"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_cost_data = {
            "Material": "MAT001",
            "Plant": "1000",
            "ValuationArea": "1000",
            "CostingType": "01",
            "StandardPrice": "125.50",
            "PriceUnit": "1",
            "Currency": "USD",
            "ValidFrom": "2024-01-01"
        }

        with patch.object(client, 'execute_query', return_value=[sap_cost_data]):
            with patch('app.infrastructure.adapters.sap.costing_adapter.CostingRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                result = await adapter.sync_standard_cost_to_unison(
                    "MAT001",
                    organization_id=1,
                    plant_id=1
                )

                assert result.standard_cost == Decimal("125.50")
                mock_repo_instance.update_standard_cost.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_price_change_history_from_sap(self):
        """Should fetch price change history from SAP"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_price_changes = [
            {
                "Material": "MAT001",
                "Plant": "1000",
                "ChangeDate": "2024-01-15",
                "OldPrice": "120.00",
                "NewPrice": "125.50",
                "Currency": "USD",
                "ChangedBy": "SAPUSER1"
            },
            {
                "Material": "MAT001",
                "Plant": "1000",
                "ChangeDate": "2024-02-01",
                "OldPrice": "125.50",
                "NewPrice": "130.00",
                "Currency": "USD",
                "ChangedBy": "SAPUSER2"
            }
        ]

        with patch.object(client, 'execute_query', return_value=sap_price_changes):
            results = await adapter.fetch_price_change_history(
                "MAT001",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 2, 28)
            )

            assert len(results) == 2
            assert results[0].old_price == Decimal("120.00")
            assert results[0].new_price == Decimal("125.50")
            assert results[1].new_price == Decimal("130.00")

    @pytest.mark.asyncio
    async def test_push_cost_update_to_sap(self):
        """Should push cost update from Unison to SAP"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.models import SAPCostUpdateDTO

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        cost_update_dto = SAPCostUpdateDTO(
            material_number="MAT001",
            plant="1000",
            new_standard_cost=Decimal("135.00"),
            currency="USD",
            valid_from=datetime(2024, 3, 1),
            reason="Market price increase"
        )

        with patch.object(client, 'execute_post') as mock_post:
            mock_post.return_value = {
                "Material": "MAT001",
                "Plant": "1000",
                "StandardPrice": "135.00",
                "Status": "Updated"
            }

            result = await adapter.push_cost_update_to_sap(cost_update_dto)

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_sync_material_costs(self):
        """Should sync multiple material costs in batch"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_costs = [
            {"Material": "MAT001", "Plant": "1000", "StandardPrice": "125.50"},
            {"Material": "MAT002", "Plant": "1000", "StandardPrice": "98.75"},
            {"Material": "MAT003", "Plant": "1000", "StandardPrice": "215.00"}
        ]

        with patch.object(client, 'execute_query', return_value=sap_costs):
            with patch('app.infrastructure.adapters.sap.costing_adapter.CostingRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                results = await adapter.batch_sync_costs(
                    organization_id=1,
                    plant_id=1,
                    material_numbers=["MAT001", "MAT002", "MAT003"]
                )

                assert len(results) == 3
                assert mock_repo_instance.update_standard_cost.call_count == 3

    @pytest.mark.asyncio
    async def test_calculate_weighted_average_cost_from_sap_layers(self):
        """Should calculate weighted average cost from SAP cost layers"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_cost_layers = [
            {"Quantity": "50.00", "UnitCost": "100.00"},  # Layer 1
            {"Quantity": "30.00", "UnitCost": "110.00"},  # Layer 2
            {"Quantity": "20.00", "UnitCost": "105.00"}   # Layer 3
        ]

        weighted_avg = adapter.calculate_weighted_average(sap_cost_layers)

        # (50*100 + 30*110 + 20*105) / (50+30+20) = 10,400 / 100 = 104.00
        assert weighted_avg == Decimal("104.00")

    @pytest.mark.asyncio
    async def test_transform_sap_costing_type_to_unison(self):
        """Should transform SAP costing types to Unison format"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        # Test costing type mappings
        assert adapter.transform_costing_type("01") == "STANDARD"
        assert adapter.transform_price_control("S") == "STANDARD"
        assert adapter.transform_price_control("V") == "WEIGHTED_AVERAGE"

    @pytest.mark.asyncio
    async def test_log_costing_sync_activity(self):
        """Should log all costing sync operations for audit trail"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        sap_cost_data = {
            "Material": "MAT001",
            "Plant": "1000",
            "StandardPrice": "125.50",
            "Currency": "USD"
        }

        with patch.object(client, 'execute_query', return_value=[sap_cost_data]):
            with patch('app.infrastructure.adapters.sap.costing_adapter.CostingRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                with patch('app.infrastructure.adapters.sap.costing_adapter.AuditLogger') as mock_logger:
                    await adapter.sync_standard_cost_to_unison(
                        "MAT001",
                        organization_id=1,
                        plant_id=1
                    )

                    mock_logger.log.assert_called_once()
                    call_args = mock_logger.log.call_args[1]
                    assert call_args['action'] == 'costing_sync_from_sap'
                    assert call_args['material_number'] == 'MAT001'

    @pytest.mark.asyncio
    async def test_validate_cost_data_before_sync(self):
        """Should validate cost data before syncing to prevent invalid costs"""
        from app.infrastructure.adapters.sap.costing_adapter import CostingAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.exceptions import SAPDataValidationError

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = CostingAdapter(client)

        # Invalid cost data (negative cost)
        invalid_sap_cost_data = {
            "Material": "MAT001",
            "Plant": "1000",
            "StandardPrice": "-125.50",  # Invalid negative cost
            "Currency": "USD"
        }

        with patch.object(client, 'execute_query', return_value=[invalid_sap_cost_data]):
            with pytest.raises(SAPDataValidationError, match="Cost cannot be negative"):
                await adapter.sync_standard_cost_to_unison(
                    "MAT001",
                    organization_id=1,
                    plant_id=1
                )
