"""
Unit tests for SAP Inventory Adapter - Inventory Transaction Sync
RED Phase: Write failing tests first
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal


class TestInventoryAdapterSync:
    """Test inventory transaction synchronization"""

    @pytest.mark.asyncio
    async def test_fetch_goods_receipt_from_sap(self):
        """Should fetch goods receipt transaction from SAP"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_gr_data = {
            "MaterialDocument": "5000000001",
            "MaterialDocumentYear": "2024",
            "MaterialDocumentItem": "0001",
            "Material": "MAT001",
            "Plant": "1000",
            "StorageLocation": "0001",
            "Batch": "BATCH001",
            "QuantityInBaseUnit": "100.000",
            "BaseUnit": "EA",
            "MovementType": "101",  # Goods Receipt
            "PostingDate": "2024-01-15",
            "DocumentDate": "2024-01-15"
        }

        with patch.object(client, 'execute_query', return_value=[sap_gr_data]):
            result = await adapter.fetch_goods_receipt("5000000001", "2024")

            assert result.document_number == "5000000001"
            assert result.material_number == "MAT001"
            assert result.quantity == Decimal("100.000")
            assert result.movement_type == "GOODS_RECEIPT"

    @pytest.mark.asyncio
    async def test_fetch_goods_issue_from_sap(self):
        """Should fetch goods issue transaction from SAP"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_gi_data = {
            "MaterialDocument": "5000000002",
            "MaterialDocumentYear": "2024",
            "MaterialDocumentItem": "0001",
            "Material": "MAT001",
            "Plant": "1000",
            "StorageLocation": "0001",
            "Batch": "BATCH001",
            "QuantityInBaseUnit": "-50.000",
            "BaseUnit": "EA",
            "MovementType": "261",  # Goods Issue
            "PostingDate": "2024-01-16",
            "DocumentDate": "2024-01-16"
        }

        with patch.object(client, 'execute_query', return_value=[sap_gi_data]):
            result = await adapter.fetch_goods_issue("5000000002", "2024")

            assert result.document_number == "5000000002"
            assert result.material_number == "MAT001"
            assert result.quantity == Decimal("-50.000")
            assert result.movement_type == "GOODS_ISSUE"

    @pytest.mark.asyncio
    async def test_sync_goods_receipt_to_unison(self):
        """Should sync goods receipt from SAP to Unison inventory"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_gr_data = {
            "MaterialDocument": "5000000001",
            "MaterialDocumentYear": "2024",
            "MaterialDocumentItem": "0001",
            "Material": "MAT001",
            "Plant": "1000",
            "StorageLocation": "0001",
            "Batch": "BATCH001",
            "QuantityInBaseUnit": "100.000",
            "BaseUnit": "EA",
            "MovementType": "101",
            "PostingDate": "2024-01-15T10:00:00Z",
            "AmountInLocalCurrency": "1000.00"
        }

        with patch.object(client, 'execute_query', return_value=[sap_gr_data]):
            with patch('app.infrastructure.adapters.sap.inventory_adapter.InventoryRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                result = await adapter.sync_transaction_to_unison(
                    "5000000001",
                    "2024",
                    organization_id=1,
                    plant_id=1
                )

                assert result.quantity == Decimal("100.000")
                mock_repo_instance.create_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_goods_receipt_to_sap(self):
        """Should post goods receipt from Unison to SAP"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig
        from app.infrastructure.adapters.sap.models import SAPInventoryTransactionDTO

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        transaction_dto = SAPInventoryTransactionDTO(
            material_number="MAT001",
            plant="1000",
            storage_location="0001",
            batch="BATCH002",
            quantity=Decimal("75.000"),
            base_uom="EA",
            movement_type="GOODS_RECEIPT",
            posting_date=datetime(2024, 1, 20),
            reference_document="PO-12345"
        )

        with patch.object(client, 'execute_post') as mock_post:
            mock_post.return_value = {
                "MaterialDocument": "5000000003",
                "MaterialDocumentYear": "2024"
            }

            result = await adapter.post_goods_receipt_to_sap(transaction_dto)

            assert result["MaterialDocument"] == "5000000003"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_stock_transfer_transactions(self):
        """Should fetch stock transfer transactions from SAP"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_transfer_data = [
            {
                "MaterialDocument": "5000000004",
                "MaterialDocumentYear": "2024",
                "Material": "MAT001",
                "Plant": "1000",
                "StorageLocation": "0001",
                "ReceivingStorageLocation": "0002",
                "QuantityInBaseUnit": "25.000",
                "MovementType": "311",  # Stock transfer
                "PostingDate": "2024-01-17"
            }
        ]

        with patch.object(client, 'execute_query', return_value=sap_transfer_data):
            results = await adapter.fetch_stock_transfers(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31)
            )

            assert len(results) == 1
            assert results[0].movement_type == "TRANSFER_OUT"

    @pytest.mark.asyncio
    async def test_batch_sync_inventory_transactions(self):
        """Should sync multiple inventory transactions in batch"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_transactions = [
            {"MaterialDocument": "5000000001", "MovementType": "101", "QuantityInBaseUnit": "100.000"},
            {"MaterialDocument": "5000000002", "MovementType": "261", "QuantityInBaseUnit": "-50.000"},
            {"MaterialDocument": "5000000003", "MovementType": "311", "QuantityInBaseUnit": "25.000"}
        ]

        with patch.object(client, 'execute_query', return_value=sap_transactions):
            with patch('app.infrastructure.adapters.sap.inventory_adapter.InventoryRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                results = await adapter.batch_sync_transactions(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 31),
                    organization_id=1,
                    plant_id=1
                )

                assert len(results) == 3
                assert mock_repo_instance.create_transaction.call_count == 3

    @pytest.mark.asyncio
    async def test_transform_sap_movement_type_to_unison(self):
        """Should transform SAP movement types to Unison transaction types"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        # Test movement type mappings
        assert adapter.transform_movement_type("101") == "GOODS_RECEIPT"  # GR from PO
        assert adapter.transform_movement_type("261") == "GOODS_ISSUE"   # GI to production
        assert adapter.transform_movement_type("311") == "TRANSFER_OUT"  # Stock transfer
        assert adapter.transform_movement_type("312") == "TRANSFER_IN"   # Stock transfer receipt
        assert adapter.transform_movement_type("701") == "ADJUSTMENT"    # Physical inventory

    @pytest.mark.asyncio
    async def test_log_inventory_sync_activity(self):
        """Should log all inventory sync operations for audit trail"""
        from app.infrastructure.adapters.sap.inventory_adapter import InventoryAdapter
        from app.infrastructure.adapters.sap.sap_client import SAPClient
        from app.infrastructure.adapters.sap.config import SAPConfig

        config = SAPConfig(
            host="sap.example.com",
            client="100",
            user="testuser",
            password="testpass"
        )

        client = SAPClient(config)
        adapter = InventoryAdapter(client)

        sap_gr_data = {
            "MaterialDocument": "5000000001",
            "MaterialDocumentYear": "2024",
            "Material": "MAT001",
            "QuantityInBaseUnit": "100.000",
            "MovementType": "101"
        }

        with patch.object(client, 'execute_query', return_value=[sap_gr_data]):
            with patch('app.infrastructure.adapters.sap.inventory_adapter.InventoryRepository') as mock_repo:
                mock_repo_instance = Mock()
                mock_repo.return_value = mock_repo_instance

                with patch('app.infrastructure.adapters.sap.inventory_adapter.AuditLogger') as mock_logger:
                    await adapter.sync_transaction_to_unison(
                        "5000000001",
                        "2024",
                        organization_id=1,
                        plant_id=1
                    )

                    mock_logger.log.assert_called_once()
                    call_args = mock_logger.log.call_args[1]
                    assert call_args['action'] == 'inventory_sync_from_sap'
                    assert call_args['document_number'] == '5000000001'
