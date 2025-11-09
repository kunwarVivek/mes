"""
Unit tests for SAP Material Adapter - Material Master Data Sync
RED Phase: Write failing tests first
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal


class TestMaterialAdapterSync:
    """Test material master data synchronization"""

    @pytest.mark.asyncio
    async def test_fetch_material_from_sap(self):
        """Should fetch material master data from SAP"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        sap_material_data = {
            "MaterialNumber": "MAT001",
            "MaterialDescription": "Test Material",
            "BaseUnitOfMeasure": "EA",
            "MaterialGroup": "RAW"
        }

        with patch.object(client, 'execute_query', return_value=[sap_material_data]):
            result = await adapter.fetch_material("MAT001")

            assert result.material_number == "MAT001"
            assert result.description == "Test Material"
            assert result.base_uom == "EA"
            assert result.category == "RAW"

    @pytest.mark.asyncio
    async def test_fetch_material_not_found_in_sap(self):
        """Should raise exception when material not found in SAP"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.exceptions import SAPDataNotFoundError

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        with patch.object(client, 'execute_query', return_value=[]):
            with pytest.raises(SAPDataNotFoundError, match="Material MAT999 not found"):
                await adapter.fetch_material("MAT999")

    @pytest.mark.asyncio
    async def test_sync_material_from_sap_to_unison(self):
        """Should sync material from SAP to Unison database"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        sap_material_data = {
            "MaterialNumber": "MAT001",
            "MaterialDescription": "Test Material",
            "BaseUnitOfMeasure": "EA",
            "MaterialGroup": "RAW",
            "SafetyStock": "10.00",
            "ReorderPoint": "5.00",
            "LotSize": "1.00",
            "PlannedDeliveryTime": "7"
        }

        with patch.object(client, 'execute_query', return_value=[sap_material_data]):
            with patch('app.infrastructure.adapters.sap.material_adapter.MaterialRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                result = await adapter.sync_material_to_unison(
                    "MAT001",
                    organization_id=1,
                    plant_id=1
                )

                assert result.material_number == "MAT001"
                assert result.description == "Test Material"
                mock_repo_instance.create_or_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_material_from_unison_to_sap(self):
        """Should push material master data from Unison to SAP"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.models import SAPMaterialDTO

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        material_dto = SAPMaterialDTO(
            material_number="MAT002",
            description="New Material",
            base_uom="KG",
            category="FIN"
        )

        with patch.object(client, 'execute_post') as mock_post:
            mock_post.return_value = {
                "MaterialNumber": "MAT002",
                "MaterialDescription": "New Material"
            }

            result = await adapter.push_material_to_sap(material_dto)

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_sync_materials_from_sap(self):
        """Should sync multiple materials from SAP in batch"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        sap_materials = [
            {"MaterialNumber": "MAT001", "MaterialDescription": "Material 1", "BaseUnitOfMeasure": "EA", "MaterialGroup": "RAW"},
            {"MaterialNumber": "MAT002", "MaterialDescription": "Material 2", "BaseUnitOfMeasure": "KG", "MaterialGroup": "FIN"},
            {"MaterialNumber": "MAT003", "MaterialDescription": "Material 3", "BaseUnitOfMeasure": "L", "MaterialGroup": "SEM"}
        ]

        with patch.object(client, 'execute_query', return_value=sap_materials):
            with patch('app.infrastructure.adapters.sap.material_adapter.MaterialRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                results = await adapter.batch_sync_materials(
                    organization_id=1,
                    plant_id=1,
                    material_numbers=["MAT001", "MAT002", "MAT003"]
                )

                assert len(results) == 3
                assert mock_repo_instance.create_or_update.call_count == 3

    @pytest.mark.asyncio
    async def test_transform_sap_material_to_unison_format(self):
        """Should transform SAP material data to Unison format correctly"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        sap_data = {
            "MaterialNumber": "000000000000100001",  # SAP 18-char format
            "MaterialDescription": "Test Material Description",
            "BaseUnitOfMeasure": "ST",  # SAP uses different codes
            "MaterialGroup": "0001",
            "SafetyStock": "10.000",
            "ReorderPoint": "5.000",
            "PlannedDeliveryTime": "7"
        }

        transformed = adapter.transform_sap_to_unison(sap_data)

        assert transformed.material_number == "100001"  # Leading zeros removed
        assert transformed.description == "Test Material Description"
        assert transformed.base_uom == "EA"  # Transformed to Unison format
        assert transformed.safety_stock == 10.0
        assert transformed.lead_time_days == 7

    @pytest.mark.asyncio
    async def test_log_material_sync_activity(self):
        """Should log all material sync operations for audit trail"""
        from app.infrastructure.adapters.sap.material_adapter import MaterialAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = MaterialAdapter(client)

        sap_material_data = {
            "MaterialNumber": "MAT001",
            "MaterialDescription": "Test Material",
            "BaseUnitOfMeasure": "EA",
            "MaterialGroup": "RAW"
        }

        with patch.object(client, 'execute_query', return_value=[sap_material_data]):
            with patch('app.infrastructure.adapters.sap.material_adapter.MaterialRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                with patch('app.infrastructure.adapters.sap.material_adapter.AuditLogger') as mock_logger:
                    await adapter.sync_material_to_unison(
                        "MAT001",
                        organization_id=1,
                        plant_id=1
                    )

                    mock_logger.log.assert_called_once()
                    call_args = mock_logger.log.call_args[1]
                    assert call_args['action'] == 'material_sync_from_sap'
                    assert call_args['material_number'] == 'MAT001'
