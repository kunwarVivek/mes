"""
DTOs for Dashboard Metrics API.

Provides aggregated counts for dashboard without pagination limits.
"""
from pydantic import BaseModel
from typing import Dict


class DashboardMetricsResponseDTO(BaseModel):
    """Response DTO for dashboard metrics endpoint.

    Returns aggregated counts using SQL COUNT queries,
    not limited by pagination (100-item limits).
    """
    materials_count: int
    work_orders_count: int
    ncrs_count: int
    work_orders_by_status: Dict[str, int]
    ncrs_by_status: Dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "materials_count": 150,
                "work_orders_count": 120,
                "ncrs_count": 200,
                "work_orders_by_status": {
                    "PLANNED": 30,
                    "RELEASED": 40,
                    "IN_PROGRESS": 25,
                    "COMPLETED": 20,
                    "CANCELLED": 5
                },
                "ncrs_by_status": {
                    "OPEN": 50,
                    "IN_REVIEW": 75,
                    "RESOLVED": 60,
                    "CLOSED": 15
                }
            }
        }
