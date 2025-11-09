"""
SAP Costing Adapter - Material Costing Data Sync
Handles bidirectional synchronization of material costing data between SAP and Unison
"""
from typing import List
from datetime import datetime
from decimal import Decimal
from .sap_client import SAPClient
from .models import (
    SAPStandardCostDTO,
    SAPMovingAveragePriceDTO,
    SAPPriceChangeDTO,
    SAPCostUpdateDTO
)
from .exceptions import SAPDataNotFoundError, SAPDataValidationError
import logging

logger = logging.getLogger(__name__)


class CostingAdapter:
    """Adapter for syncing material costing data with SAP"""

    def __init__(self, client: SAPClient):
        """
        Initialize costing adapter

        Args:
            client: SAP client instance
        """
        self.client = client

    async def fetch_standard_cost(self, material_number: str, plant: str) -> SAPStandardCostDTO:
        """Fetch standard cost from SAP"""
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL_VALUATION/MaterialValuationSet(Material='{material_number}',Plant='{plant}')"
        results = await self.client.execute_query(endpoint)

        if not results:
            raise SAPDataNotFoundError(f"Costing data for {material_number}/{plant} not found")

        sap_data = results[0]
        standard_cost = Decimal(str(sap_data.get("StandardPrice", "0")))

        return SAPStandardCostDTO(
            material_number=material_number,
            plant=plant,
            standard_cost=standard_cost,
            currency=sap_data.get("Currency", "USD")
        )

    async def fetch_moving_average_price(self, material_number: str, plant: str) -> SAPMovingAveragePriceDTO:
        """Fetch moving average price from SAP"""
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL_VALUATION/MaterialValuationSet(Material='{material_number}',Plant='{plant}')"
        results = await self.client.execute_query(endpoint)

        if not results:
            raise SAPDataNotFoundError(f"Costing data for {material_number}/{plant} not found")

        sap_data = results[0]

        return SAPMovingAveragePriceDTO(
            material_number=material_number,
            plant=plant,
            moving_average_price=Decimal(str(sap_data.get("MovingAveragePrice", "0"))),
            currency=sap_data.get("Currency", "USD"),
            total_value=Decimal(str(sap_data.get("TotalValueAtPrice", "0"))),
            total_stock=Decimal(str(sap_data.get("TotalStock", "0")))
        )

    async def sync_standard_cost_to_unison(
        self,
        material_number: str,
        organization_id: int,
        plant_id: int
    ) -> SAPStandardCostDTO:
        """Sync standard cost from SAP to Unison"""
        cost_dto = await self.fetch_standard_cost(material_number, str(plant_id))

        # Validate cost data
        if cost_dto.standard_cost < 0:
            raise SAPDataValidationError("Cost cannot be negative")

        # Save to database
        repo = CostingRepository()
        repo.update_standard_cost({
            "material_number": material_number,
            "standard_cost": cost_dto.standard_cost,
            "organization_id": organization_id,
            "plant_id": plant_id
        })

        logger.info(f"Synced standard cost for {material_number}")

        # Log audit trail
        AuditLogger.log(
            action='costing_sync_from_sap',
            material_number=material_number,
            organization_id=organization_id,
            plant_id=plant_id
        )

        return cost_dto

    async def fetch_price_change_history(
        self,
        material_number: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[SAPPriceChangeDTO]:
        """Fetch price change history from SAP"""
        filter_condition = f"Material eq '{material_number}' and ChangeDate ge datetime'{start_date.isoformat()}' and ChangeDate le datetime'{end_date.isoformat()}'"
        endpoint = f"/sap/opu/odata/sap/API_PRICE_CHANGE/PriceChangeSet?$filter={filter_condition}"

        results = await self.client.execute_query(endpoint)

        price_changes = []
        for data in results:
            price_changes.append(SAPPriceChangeDTO(
                material_number=data.get("Material", ""),
                plant=data.get("Plant", ""),
                change_date=datetime.fromisoformat(data.get("ChangeDate", datetime.now().isoformat())),
                old_price=Decimal(str(data.get("OldPrice", "0"))),
                new_price=Decimal(str(data.get("NewPrice", "0"))),
                currency=data.get("Currency", "USD"),
                changed_by=data.get("ChangedBy", "")
            ))

        return price_changes

    async def push_cost_update_to_sap(self, cost_update_dto: SAPCostUpdateDTO) -> bool:
        """Push cost update from Unison to SAP"""
        endpoint = "/sap/opu/odata/sap/API_MATERIAL_VALUATION/PriceUpdateSet"

        payload = {
            "Material": cost_update_dto.material_number,
            "Plant": cost_update_dto.plant,
            "StandardPrice": str(cost_update_dto.new_standard_cost),
            "Currency": cost_update_dto.currency,
            "ValidFrom": cost_update_dto.valid_from.isoformat()
        }

        result = await self.client.execute_post(endpoint, payload)
        logger.info(f"Pushed cost update to SAP for {cost_update_dto.material_number}")
        return result is not None

    async def batch_sync_costs(
        self,
        organization_id: int,
        plant_id: int,
        material_numbers: List[str]
    ) -> List[SAPStandardCostDTO]:
        """Sync multiple material costs in batch"""
        filter_condition = " or ".join([f"Material eq '{num}'" for num in material_numbers])
        endpoint = f"/sap/opu/odata/sap/API_MATERIAL_VALUATION/MaterialValuationSet?$filter={filter_condition}"

        results = await self.client.execute_query(endpoint)

        repo = CostingRepository()
        synced_costs = []
        for data in results:
            cost_dto = SAPStandardCostDTO(
                material_number=data.get("Material", ""),
                plant=data.get("Plant", ""),
                standard_cost=Decimal(str(data.get("StandardPrice", "0"))),
                currency=data.get("Currency", "USD")
            )

            repo.update_standard_cost({
                "material_number": cost_dto.material_number,
                "standard_cost": cost_dto.standard_cost,
                "organization_id": organization_id,
                "plant_id": plant_id
            })

            synced_costs.append(cost_dto)

        logger.info(f"Batch synced {len(synced_costs)} material costs")
        return synced_costs

    def calculate_weighted_average(self, cost_layers: List[dict]) -> Decimal:
        """Calculate weighted average cost from SAP cost layers"""
        total_value = Decimal("0")
        total_quantity = Decimal("0")

        for layer in cost_layers:
            quantity = Decimal(str(layer.get("Quantity", "0")))
            unit_cost = Decimal(str(layer.get("UnitCost", "0")))
            total_value += quantity * unit_cost
            total_quantity += quantity

        if total_quantity == 0:
            return Decimal("0")

        return total_value / total_quantity

    def transform_costing_type(self, sap_costing_type: str) -> str:
        """Transform SAP costing types to Unison format"""
        if sap_costing_type == "01":
            return "STANDARD"
        return "STANDARD"

    def transform_price_control(self, sap_price_control: str) -> str:
        """Transform SAP price control to Unison costing method"""
        if sap_price_control == "S":
            return "STANDARD"
        elif sap_price_control == "V":
            return "WEIGHTED_AVERAGE"
        return "STANDARD"


class AuditLogger:
    """Mock audit logger"""
    @staticmethod
    def log(**kwargs):
        logger.info(f"Audit log: {kwargs}")


class CostingRepository:
    """Mock costing repository"""
    def update_standard_cost(self, cost_data: dict):
        pass
