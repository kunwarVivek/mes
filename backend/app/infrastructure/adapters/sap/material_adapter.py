"""
SAP Material Adapter - Material Master Data Sync
Handles bidirectional synchronization of material master data between SAP and Unison
"""
from typing import List, Optional
from decimal import Decimal
from .sap_client import SAPClient
from .models import SAPMaterialDTO
from .exceptions import SAPDataNotFoundError
import logging

logger = logging.getLogger(__name__)


class MaterialAdapter:
    """Adapter for syncing material master data with SAP"""

    # SAP to Unison UOM mapping
    UOM_MAPPING = {
        "ST": "EA",  # SAP Stück to Unison Each
        "KGM": "KG",
        "LTR": "L",
        "MTR": "M",
    }

    def __init__(self, client: SAPClient):
        """
        Initialize material adapter

        Args:
            client: SAP client instance
        """
        self.client = client

    async def fetch_material(self, material_number: str) -> SAPMaterialDTO:
        """
        Fetch material master data from SAP

        Args:
            material_number: Material number to fetch

        Returns:
            Material data DTO

        Raises:
            SAPDataNotFoundError: If material not found
        """
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL/MaterialSet('{material_number}')"

        results = await self.client.execute_query(endpoint)

        if not results:
            raise SAPDataNotFoundError(f"Material {material_number} not found in SAP")

        sap_data = results[0]

        # Use transform to ensure consistent handling
        return self.transform_sap_to_unison(sap_data)

    async def sync_material_to_unison(
        self,
        material_number: str,
        organization_id: int,
        plant_id: int
    ) -> SAPMaterialDTO:
        """
        Sync material from SAP to Unison database

        Args:
            material_number: Material number to sync
            organization_id: Unison organization ID
            plant_id: Unison plant ID

        Returns:
            Synced material DTO
        """
        # Fetch from SAP (already transformed)
        material_dto = await self.fetch_material(material_number)

        # Save to database
        repo = MaterialRepository()
        repo.create_or_update({
            "material_number": material_dto.material_number,
            "description": material_dto.description,
            "base_uom": material_dto.base_uom,
            "category": material_dto.category,
            "organization_id": organization_id,
            "plant_id": plant_id
        })

        logger.info(f"Synced material {material_number} to Unison org={organization_id} plant={plant_id}")

        # Log audit trail
        AuditLogger.log(
            action='material_sync_from_sap',
            material_number=material_number,
            organization_id=organization_id,
            plant_id=plant_id
        )

        return material_dto

    async def push_material_to_sap(self, material_dto: SAPMaterialDTO) -> bool:
        """
        Push material master data from Unison to SAP

        Args:
            material_dto: Material data to push

        Returns:
            True if successful
        """
        endpoint = "/sap/opu/odata/sap/API_MATERIAL/MaterialSet"

        payload = {
            "MaterialNumber": material_dto.material_number,
            "MaterialDescription": material_dto.description,
            "BaseUnitOfMeasure": material_dto.base_uom,
            "MaterialGroup": material_dto.category
        }

        result = await self.client.execute_post(endpoint, payload)

        logger.info(f"Pushed material {material_dto.material_number} to SAP")

        return result is not None

    async def batch_sync_materials(
        self,
        organization_id: int,
        plant_id: int,
        material_numbers: List[str]
    ) -> List[SAPMaterialDTO]:
        """
        Sync multiple materials from SAP in batch

        Args:
            organization_id: Unison organization ID
            plant_id: Unison plant ID
            material_numbers: List of material numbers to sync

        Returns:
            List of synced material DTOs
        """
        # Fetch all materials in one query
        filter_condition = " or ".join([f"MaterialNumber eq '{num}'" for num in material_numbers])
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL/MaterialSet?$filter={filter_condition}"

        results = await self.client.execute_query(endpoint)

        repo = MaterialRepository()
        synced_materials = []
        for sap_data in results:
            transformed = self.transform_sap_to_unison(sap_data)
            # Save to database
            repo.create_or_update({
                "material_number": transformed.material_number,
                "description": transformed.description,
                "organization_id": organization_id,
                "plant_id": plant_id
            })
            synced_materials.append(transformed)

        logger.info(f"Batch synced {len(synced_materials)} materials")

        return synced_materials

    def transform_sap_to_unison(self, sap_data: dict) -> SAPMaterialDTO:
        """
        Transform SAP material data to Unison format

        Args:
            sap_data: Raw SAP material data

        Returns:
            Transformed material DTO
        """
        # Remove leading zeros from SAP 18-character material number
        material_number = sap_data.get("MaterialNumber", "")
        if material_number:
            material_number = material_number.lstrip("0") or material_number  # Keep at least one char

        # Transform UOM
        sap_uom = sap_data.get("BaseUnitOfMeasure", "EA")
        base_uom = self.UOM_MAPPING.get(sap_uom, sap_uom)

        # Handle string values from SAP (may have commas)
        def to_float(value, default=0.0):
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).replace(",", "")) if value else default

        return SAPMaterialDTO(
            material_number=material_number,
            description=sap_data.get("MaterialDescription", ""),
            base_uom=base_uom,
            category=sap_data.get("MaterialGroup", ""),
            safety_stock=to_float(sap_data.get("SafetyStock")),
            reorder_point=to_float(sap_data.get("ReorderPoint")),
            lot_size=to_float(sap_data.get("LotSize"), 1.0),
            lead_time_days=int(sap_data.get("PlannedDeliveryTime", "0") or 0)
        )


class AuditLogger:
    """Mock audit logger for demonstration"""

    @staticmethod
    def log(**kwargs):
        """Log audit event"""
        logger.info(f"Audit log: {kwargs}")


class MaterialRepository:
    """Mock material repository for demonstration"""

    def create_or_update(self, material_data: dict):
        """Create or update material"""
        pass
