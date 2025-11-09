"""
SAP Inventory Adapter - Inventory Transaction Sync
Handles bidirectional synchronization of inventory transactions between SAP and Unison
"""
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
from .sap_client import SAPClient
from .models import SAPInventoryTransactionDTO
from .exceptions import SAPDataNotFoundError
import logging

logger = logging.getLogger(__name__)


class InventoryAdapter:
    """Adapter for syncing inventory transactions with SAP"""

    # SAP movement type to Unison transaction type mapping
    MOVEMENT_TYPE_MAPPING = {
        "101": "GOODS_RECEIPT",   # GR from PO
        "102": "GOODS_RECEIPT",   # GR reversal
        "261": "GOODS_ISSUE",     # GI to production
        "262": "GOODS_ISSUE",     # GI reversal
        "311": "TRANSFER_OUT",    # Stock transfer posting
        "312": "TRANSFER_IN",     # Stock transfer receipt
        "701": "ADJUSTMENT",      # Physical inventory posting
    }

    def __init__(self, client: SAPClient):
        """
        Initialize inventory adapter

        Args:
            client: SAP client instance
        """
        self.client = client

    async def fetch_goods_receipt(self, document_number: str, year: str) -> SAPInventoryTransactionDTO:
        """Fetch goods receipt transaction from SAP"""
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL_DOCUMENT/MaterialDocumentSet(MaterialDocument='{document_number}',MaterialDocumentYear='{year}')"
        results = await self.client.execute_query(endpoint)

        if not results:
            raise SAPDataNotFoundError(f"Document {document_number}/{year} not found")

        sap_data = results[0]
        return self._transform_sap_transaction(sap_data)

    async def fetch_goods_issue(self, document_number: str, year: str) -> SAPInventoryTransactionDTO:
        """Fetch goods issue transaction from SAP"""
        return await self.fetch_goods_receipt(document_number, year)

    async def sync_transaction_to_unison(
        self,
        document_number: str,
        year: str,
        organization_id: int,
        plant_id: int
    ) -> SAPInventoryTransactionDTO:
        """Sync inventory transaction from SAP to Unison"""
        transaction_dto = await self.fetch_goods_receipt(document_number, year)

        # Save to database
        repo = InventoryRepository()
        repo.create_transaction({
            "material_number": transaction_dto.material_number,
            "quantity": transaction_dto.quantity,
            "movement_type": transaction_dto.movement_type,
            "organization_id": organization_id,
            "plant_id": plant_id
        })

        logger.info(f"Synced transaction {document_number}/{year}")

        # Log audit trail
        AuditLogger.log(
            action='inventory_sync_from_sap',
            document_number=document_number,
            organization_id=organization_id,
            plant_id=plant_id
        )

        return transaction_dto

    async def post_goods_receipt_to_sap(self, transaction_dto: SAPInventoryTransactionDTO) -> Dict[str, Any]:
        """Post goods receipt from Unison to SAP"""
        endpoint = "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT/MaterialDocumentSet"

        payload = {
            "Material": transaction_dto.material_number,
            "Plant": transaction_dto.plant,
            "StorageLocation": transaction_dto.storage_location,
            "Batch": transaction_dto.batch,
            "QuantityInBaseUnit": str(transaction_dto.quantity),
            "MovementType": "101",
            "PostingDate": transaction_dto.posting_date.isoformat()
        }

        result = await self.client.execute_post(endpoint, payload)
        logger.info(f"Posted GR to SAP for material {transaction_dto.material_number}")
        return result

    async def fetch_stock_transfers(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[SAPInventoryTransactionDTO]:
        """Fetch stock transfer transactions from SAP"""
        filter_condition = f"PostingDate ge datetime'{start_date.isoformat()}' and PostingDate le datetime'{end_date.isoformat()}'"
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL_DOCUMENT/MaterialDocumentSet?$filter={filter_condition}"

        results = await self.client.execute_query(endpoint)
        return [self._transform_sap_transaction(data) for data in results]

    async def batch_sync_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        organization_id: int,
        plant_id: int
    ) -> List[SAPInventoryTransactionDTO]:
        """Sync multiple inventory transactions in batch"""
        transactions = await self.fetch_stock_transfers(start_date, end_date)

        repo = InventoryRepository()
        for txn in transactions:
            repo.create_transaction({
                "material_number": txn.material_number,
                "quantity": txn.quantity,
                "movement_type": txn.movement_type,
                "organization_id": organization_id,
                "plant_id": plant_id
            })

        logger.info(f"Batch synced {len(transactions)} transactions")
        return transactions

    def transform_movement_type(self, sap_movement_type: str) -> str:
        """Transform SAP movement types to Unison transaction types"""
        return self.MOVEMENT_TYPE_MAPPING.get(sap_movement_type, "ADJUSTMENT")

    def _transform_sap_transaction(self, sap_data: dict) -> SAPInventoryTransactionDTO:
        """Transform SAP transaction data to Unison format"""
        movement_type = self.transform_movement_type(sap_data.get("MovementType", ""))

        # Parse posting date
        posting_date_str = sap_data.get("PostingDate", "")
        if posting_date_str and not posting_date_str.endswith("Z"):
            # Add time component if missing
            if "T" not in posting_date_str:
                posting_date_str = f"{posting_date_str}T00:00:00"
        posting_date = datetime.fromisoformat(posting_date_str) if posting_date_str else datetime.now()

        return SAPInventoryTransactionDTO(
            document_number=sap_data.get("MaterialDocument", ""),
            material_number=sap_data.get("Material", ""),
            plant=sap_data.get("Plant", ""),
            storage_location=sap_data.get("StorageLocation", ""),
            batch=sap_data.get("Batch", ""),
            quantity=Decimal(str(sap_data.get("QuantityInBaseUnit", "0"))),
            base_uom=sap_data.get("BaseUnit", ""),
            movement_type=movement_type,
            posting_date=posting_date,
            reference_document=sap_data.get("PurchaseOrder", "")
        )


class AuditLogger:
    """Mock audit logger"""
    @staticmethod
    def log(**kwargs):
        logger.info(f"Audit log: {kwargs}")


class InventoryRepository:
    """Mock inventory repository"""
    def create_transaction(self, transaction_data: dict):
        pass
