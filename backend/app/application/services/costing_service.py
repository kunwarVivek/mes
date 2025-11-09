"""
Costing Service - Application layer service for material cost calculations.
Phase 2: Material Management - Material Costing

Supports FIFO, LIFO, Weighted Average, and Standard costing methods.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.costing import MaterialCosting, CostLayer, CostingMethod


class CostingService:
    """
    Application service for material costing calculations.

    Implements FIFO, LIFO, Weighted Average, and Standard costing methods.
    Uses CostLayer entities for FIFO/LIFO tracking.
    """

    def __init__(self, db_session: Session):
        """
        Initialize CostingService with database session.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session

    def _validate_quantity(self, quantity: Decimal) -> None:
        """Validate that quantity is positive."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

    def _calculate_layered_cost(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_date: datetime,
        order_ascending: bool = True
    ) -> Dict:
        """
        Common logic for FIFO/LIFO cost calculation.

        Args:
            material_id: ID of the material
            quantity: Quantity to be issued
            transaction_date: Date of the transaction
            order_ascending: True for FIFO (oldest first), False for LIFO (newest first)

        Returns:
            Dict with total_cost, unit_cost, and batches_used

        Raises:
            ValueError: If quantity <= 0 or insufficient inventory
        """
        self._validate_quantity(quantity)

        # Fetch cost layers ordered by receipt_date
        order_clause = CostLayer.receipt_date.asc() if order_ascending else CostLayer.receipt_date.desc()
        cost_layers = self.db.query(CostLayer).filter(
            CostLayer.material_id == material_id,
            CostLayer.quantity_remaining > 0,
            CostLayer.receipt_date <= transaction_date
        ).order_by(order_clause).all()

        # Calculate total available quantity
        total_available = sum(layer.quantity_remaining for layer in cost_layers)
        if total_available < quantity:
            raise ValueError(
                f"Insufficient inventory. Available: {total_available}, Requested: {quantity}"
            )

        # Consume batches
        remaining_to_consume = quantity
        total_cost = Decimal("0.00")
        batches_used = []

        for layer in cost_layers:
            if remaining_to_consume <= 0:
                break

            # Determine how much to consume from this layer
            quantity_from_layer = min(layer.quantity_remaining, remaining_to_consume)

            # Calculate cost from this layer
            layer_cost = quantity_from_layer * layer.unit_cost
            total_cost += layer_cost

            # Track batch usage
            batches_used.append({
                "batch_number": layer.batch_number,
                "quantity_consumed": quantity_from_layer,
                "unit_cost": layer.unit_cost,
                "layer_cost": layer_cost
            })

            # Update remaining quantity to consume
            remaining_to_consume -= quantity_from_layer

        # Calculate unit cost (round to 2 decimal places)
        unit_cost = (total_cost / quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "total_cost": total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "unit_cost": unit_cost,
            "batches_used": batches_used
        }

    def calculate_fifo_cost(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_date: datetime
    ) -> Dict:
        """
        Calculate cost using FIFO (First In First Out) method.

        Consumes oldest batches first based on receipt_date.
        Handles multi-batch scenarios with partial batch consumption.

        Args:
            material_id: ID of the material
            quantity: Quantity to be issued
            transaction_date: Date of the transaction

        Returns:
            Dict with:
                - total_cost: Total cost for the quantity (Decimal)
                - unit_cost: Average unit cost (Decimal)
                - batches_used: List of batches consumed with quantities

        Raises:
            ValueError: If quantity <= 0 or insufficient inventory
        """
        return self._calculate_layered_cost(
            material_id=material_id,
            quantity=quantity,
            transaction_date=transaction_date,
            order_ascending=True  # FIFO: oldest first
        )

    def calculate_lifo_cost(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_date: datetime
    ) -> Dict:
        """
        Calculate cost using LIFO (Last In First Out) method.

        Consumes newest batches first based on receipt_date.
        Handles multi-batch scenarios with partial batch consumption.

        Args:
            material_id: ID of the material
            quantity: Quantity to be issued
            transaction_date: Date of the transaction

        Returns:
            Dict with:
                - total_cost: Total cost for the quantity (Decimal)
                - unit_cost: Average unit cost (Decimal)
                - batches_used: List of batches consumed with quantities

        Raises:
            ValueError: If quantity <= 0 or insufficient inventory
        """
        return self._calculate_layered_cost(
            material_id=material_id,
            quantity=quantity,
            transaction_date=transaction_date,
            order_ascending=False  # LIFO: newest first
        )

    def calculate_weighted_average_cost(
        self,
        material_id: int,
        quantity: Decimal,
        transaction_date: datetime
    ) -> Dict:
        """
        Calculate cost using Weighted Average method.

        Calculates weighted average unit cost across all available batches.
        Does not track specific batch consumption.

        Args:
            material_id: ID of the material
            quantity: Quantity to be issued
            transaction_date: Date of the transaction

        Returns:
            Dict with:
                - total_cost: Total cost for the quantity (Decimal)
                - unit_cost: Weighted average unit cost (Decimal)
                - batches_used: Empty list (weighted average doesn't track batches)

        Raises:
            ValueError: If quantity <= 0 or insufficient inventory
        """
        self._validate_quantity(quantity)

        # Fetch all cost layers for the material
        cost_layers = self.db.query(CostLayer).filter(
            CostLayer.material_id == material_id,
            CostLayer.quantity_remaining > 0,
            CostLayer.receipt_date <= transaction_date
        ).all()

        if not cost_layers:
            raise ValueError(f"No inventory available for material {material_id}")

        # Calculate total quantity and total value
        total_quantity = Decimal("0.00")
        total_value = Decimal("0.00")

        for layer in cost_layers:
            layer_value = layer.quantity_remaining * layer.unit_cost
            total_quantity += layer.quantity_remaining
            total_value += layer_value

        if total_quantity < quantity:
            raise ValueError(
                f"Insufficient inventory. Available: {total_quantity}, Requested: {quantity}"
            )

        # Calculate weighted average unit cost
        weighted_avg_cost = (total_value / total_quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Calculate total cost
        total_cost = (weighted_avg_cost * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "total_cost": total_cost,
            "unit_cost": weighted_avg_cost,
            "batches_used": []  # Weighted average doesn't track specific batches
        }

    def calculate_standard_cost(
        self,
        material_id: int,
        quantity: Decimal
    ) -> Dict:
        """
        Calculate cost using Standard Cost method.

        Uses predefined standard_cost from MaterialCosting record.
        Simple multiplication: total_cost = quantity * standard_cost.

        Args:
            material_id: ID of the material
            quantity: Quantity to be issued

        Returns:
            Dict with:
                - total_cost: Total cost for the quantity (Decimal)
                - unit_cost: Standard unit cost (Decimal)
                - batches_used: Empty list (standard cost doesn't track batches)

        Raises:
            ValueError: If quantity <= 0 or no costing record found
        """
        self._validate_quantity(quantity)

        # Fetch MaterialCosting record
        costing = self.db.query(MaterialCosting).filter(
            MaterialCosting.material_id == material_id,
            MaterialCosting.costing_method == CostingMethod.STANDARD,
            MaterialCosting.is_active == True
        ).first()

        if not costing:
            raise ValueError(f"No costing record found for material {material_id}")

        if costing.standard_cost is None:
            raise ValueError(f"Standard cost not set for material {material_id}")

        # Calculate total cost
        standard_cost = Decimal(str(costing.standard_cost))
        total_cost = (standard_cost * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "total_cost": total_cost,
            "unit_cost": standard_cost,
            "batches_used": []  # Standard cost doesn't track batches
        }

    def update_moving_average(
        self,
        material_id: int,
        current_quantity: Decimal,
        current_average_cost: Decimal,
        new_quantity: Decimal,
        new_unit_cost: Decimal
    ) -> Decimal:
        """
        Update moving average cost with new receipt.

        Formula: new_avg = (current_qty * current_avg + new_qty * new_cost) / (current_qty + new_qty)

        Args:
            material_id: ID of the material
            current_quantity: Current inventory quantity
            current_average_cost: Current average unit cost
            new_quantity: Quantity received in new receipt
            new_unit_cost: Unit cost of new receipt

        Returns:
            New weighted average unit cost (Decimal)

        Raises:
            ValueError: If quantities or costs are invalid
        """
        if current_quantity < 0 or new_quantity <= 0:
            raise ValueError("Quantities must be non-negative (new quantity must be positive)")

        if current_average_cost < 0 or new_unit_cost < 0:
            raise ValueError("Costs must be non-negative")

        # Calculate new weighted average
        current_value = current_quantity * current_average_cost
        new_value = new_quantity * new_unit_cost
        total_quantity = current_quantity + new_quantity

        new_average = ((current_value + new_value) / total_quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return new_average
