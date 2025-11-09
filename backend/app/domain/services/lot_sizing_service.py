"""
Domain service for Lot Sizing calculations.
Determines optimal order quantities based on lot sizing rules.
Phase 3: Production Planning Module - Component 4
"""
import math
from typing import Optional, List, Dict, Any
from datetime import datetime


class PeriodType:
    """Constants for POQ period types"""
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'

    # Period multipliers for converting to days
    MULTIPLIERS = {
        DAILY: 1,
        WEEKLY: 7,
        MONTHLY: 30
    }

    @classmethod
    def is_valid(cls, period_type: str) -> bool:
        """Check if period type is valid"""
        return period_type in cls.MULTIPLIERS

    @classmethod
    def get_multiplier(cls, period_type: str) -> int:
        """Get period multiplier for given type"""
        return cls.MULTIPLIERS.get(period_type, 1)


class LotSizingService:
    """Service for calculating lot sizes using various rules"""

    def calculate_lot_size(
        self,
        material_id: int,
        net_requirement: float,
        lot_sizing_rule: str,
        fixed_lot_size: Optional[float] = None,
        annual_demand: Optional[float] = None,
        ordering_cost: Optional[float] = None,
        holding_cost_rate: Optional[float] = None,
        unit_cost: Optional[float] = None,
        poq_requirements: Optional[List[Dict[str, Any]]] = None,
        poq_period_type: Optional[str] = None,
        poq_periods_to_cover: Optional[int] = None
    ) -> float:
        """
        Calculate lot size based on lot sizing rule.

        Args:
            material_id: ID of material
            net_requirement: Net quantity needed
            lot_sizing_rule: LOT_FOR_LOT, FIXED_LOT_SIZE, EOQ, or POQ
            fixed_lot_size: Fixed lot size (for FIXED_LOT_SIZE rule)
            annual_demand: Annual demand (for EOQ rule)
            ordering_cost: Cost per order (for EOQ rule)
            holding_cost_rate: Holding cost rate (for EOQ rule)
            unit_cost: Unit cost (for EOQ rule)
            poq_requirements: List of period requirements (for POQ rule)
            poq_period_type: Period type - DAILY, WEEKLY, MONTHLY (for POQ rule)
            poq_periods_to_cover: Number of periods to cover (for POQ rule)

        Returns:
            Calculated lot size
        """
        if lot_sizing_rule != 'POQ' and net_requirement <= 0:
            raise ValueError("Net requirement must be positive")

        if lot_sizing_rule == 'LOT_FOR_LOT':
            return self._lot_for_lot(net_requirement)

        elif lot_sizing_rule == 'FIXED_LOT_SIZE':
            if fixed_lot_size is None or fixed_lot_size <= 0:
                raise ValueError("Fixed lot size must be provided and positive")
            return self._fixed_lot_size(net_requirement, fixed_lot_size)

        elif lot_sizing_rule == 'EOQ':
            if any([
                annual_demand is None,
                ordering_cost is None,
                holding_cost_rate is None,
                unit_cost is None
            ]):
                raise ValueError("All EOQ parameters must be provided")
            return self._economic_order_quantity(
                annual_demand, ordering_cost, holding_cost_rate, unit_cost
            )

        elif lot_sizing_rule == 'POQ':
            if poq_requirements is None:
                raise ValueError("POQ requires requirements list")
            if poq_period_type is None:
                raise ValueError("POQ requires period_type")
            if poq_periods_to_cover is None:
                raise ValueError("POQ requires periods_to_cover")
            return self.calculate_poq_lot_size(
                requirements=poq_requirements,
                period_type=poq_period_type,
                periods_to_cover=poq_periods_to_cover
            )

        else:
            raise ValueError(f"Unknown lot sizing rule: {lot_sizing_rule}")

    def _lot_for_lot(self, net_requirement: float) -> float:
        """
        LOT_FOR_LOT: Order exactly what's needed.

        Args:
            net_requirement: Net quantity needed

        Returns:
            Same as net requirement
        """
        return net_requirement

    def _fixed_lot_size(self, net_requirement: float, fixed_lot_size: float) -> float:
        """
        FIXED_LOT_SIZE: Round up to nearest multiple of fixed lot size.

        Args:
            net_requirement: Net quantity needed
            fixed_lot_size: Fixed lot size

        Returns:
            Rounded up to fixed lot size
        """
        # Calculate number of lots needed (round up)
        lots_needed = math.ceil(net_requirement / fixed_lot_size)
        return lots_needed * fixed_lot_size

    def _economic_order_quantity(
        self,
        annual_demand: float,
        ordering_cost: float,
        holding_cost_rate: float,
        unit_cost: float
    ) -> float:
        """
        EOQ: Calculate Economic Order Quantity.

        Formula: EOQ = sqrt((2 * D * S) / (H * C))
        Where:
            D = Annual demand
            S = Ordering cost per order
            H = Holding cost rate (as decimal)
            C = Unit cost

        Args:
            annual_demand: Annual demand quantity
            ordering_cost: Cost per order
            holding_cost_rate: Holding cost rate (e.g., 0.2 for 20%)
            unit_cost: Unit cost

        Returns:
            Calculated EOQ
        """
        if annual_demand <= 0:
            raise ValueError("Annual demand must be positive")
        if ordering_cost <= 0:
            raise ValueError("Ordering cost must be positive")
        if holding_cost_rate <= 0:
            raise ValueError("Holding cost rate must be positive")
        if unit_cost <= 0:
            raise ValueError("Unit cost must be positive")

        # EOQ formula
        numerator = 2 * annual_demand * ordering_cost
        denominator = holding_cost_rate * unit_cost
        eoq = math.sqrt(numerator / denominator)

        return round(eoq, 2)

    def calculate_poq_lot_size(
        self,
        requirements: List[Dict[str, Any]],
        period_type: str,
        periods_to_cover: int
    ) -> float:
        """
        POQ: Period Order Quantity - Aggregate demand over N periods.

        Places one order to cover requirements for a specified number of periods.
        Period types:
            - DAILY: Aggregate N days of demand
            - WEEKLY: Aggregate N weeks (7-day periods) of demand
            - MONTHLY: Aggregate N months (30-day periods) of demand

        Args:
            requirements: List of dicts with 'period' (datetime) and 'quantity' (float)
            period_type: Period type - DAILY, WEEKLY, or MONTHLY
            periods_to_cover: Number of periods to aggregate

        Returns:
            Total quantity to cover the specified periods

        Raises:
            ValueError: If period_type is invalid or periods_to_cover is not positive
        """
        # Validate inputs
        if not PeriodType.is_valid(period_type):
            raise ValueError(f"Invalid period type: {period_type}")

        if periods_to_cover <= 0:
            raise ValueError("periods_to_cover must be positive")

        # Handle empty requirements
        if not requirements:
            return 0.0

        # Calculate number of periods based on period type
        period_multiplier = PeriodType.get_multiplier(period_type)
        periods_needed = periods_to_cover * period_multiplier

        # Take only the periods we need to cover (or all available if less)
        periods_to_aggregate = min(periods_needed, len(requirements))

        # Sum up quantities for the periods
        total_quantity = sum(
            req['quantity'] for req in requirements[:periods_to_aggregate]
        )

        return total_quantity
