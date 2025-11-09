"""
Smoke test for Plant API endpoints.

Simple test to verify the API router loads correctly without TestClient.
"""

import pytest


def test_plant_router_imports():
    """Verify plant router can be imported"""
    from app.presentation.api.v1.plants import router

    assert router is not None

    # Verify all routes are registered
    routes = [route.path for route in router.routes]

    assert "/" in routes  # List and Create endpoints
    assert "/{plant_id}" in routes  # Get, Update, Delete endpoints


def test_plant_dto_imports():
    """Verify plant DTOs can be imported"""
    from app.application.dtos.plant_dto import (
        PlantCreateRequest,
        PlantUpdateRequest,
        PlantResponse,
        PlantListResponse
    )

    # Test DTO instantiation
    create_dto = PlantCreateRequest(
        organization_id=1,
        plant_code="P001",
        plant_name="Test Plant"
    )

    assert create_dto.organization_id == 1
    assert create_dto.plant_code == "P001"
    assert create_dto.plant_name == "Test Plant"
    assert create_dto.is_active is True  # Default value


def test_plant_repository_imports():
    """Verify plant repository can be imported"""
    from app.infrastructure.repositories.plant_repository import PlantRepository

    assert PlantRepository is not None


def test_plant_model_imports():
    """Verify plant model can be imported"""
    from app.models.plant import Plant

    assert Plant is not None
    assert Plant.__tablename__ == "plants"
