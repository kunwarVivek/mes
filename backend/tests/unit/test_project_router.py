"""
Unit tests for Project Router.

Tests route registration and dependencies without full integration.
"""

import pytest


def test_project_router_import():
    """Should import project router successfully"""
    from app.presentation.api.v1.projects import router

    assert router is not None


def test_project_router_routes():
    """Should have all expected routes registered"""
    from app.presentation.api.v1.projects import router

    routes = [route.path for route in router.routes]

    assert "/" in routes  # List and Create
    assert "/{project_id}" in routes  # Get, Update, Delete

    # Check all HTTP methods are present
    methods_by_path = {}
    for route in router.routes:
        if route.path not in methods_by_path:
            methods_by_path[route.path] = set()
        methods_by_path[route.path].update(route.methods)

    # List and Create on /
    assert "GET" in methods_by_path["/"]
    assert "POST" in methods_by_path["/"]

    # Get, Update, Delete on /{project_id}
    assert "GET" in methods_by_path["/{project_id}"]
    assert "PUT" in methods_by_path["/{project_id}"]
    assert "DELETE" in methods_by_path["/{project_id}"]


def test_project_dto_imports():
    """Should import all DTOs successfully"""
    from app.application.dtos.project_dto import (
        ProjectCreateRequest,
        ProjectUpdateRequest,
        ProjectResponse,
        ProjectListResponse,
    )

    assert ProjectCreateRequest is not None
    assert ProjectUpdateRequest is not None
    assert ProjectResponse is not None
    assert ProjectListResponse is not None


def test_project_repository_import():
    """Should import repository successfully"""
    from app.infrastructure.repositories.project_repository import ProjectRepository

    assert ProjectRepository is not None


def test_project_entity_import():
    """Should import domain entities successfully"""
    from app.domain.entities.project import ProjectDomain, ProjectStatus

    assert ProjectDomain is not None
    assert ProjectStatus is not None


def test_project_model_import():
    """Should import SQLAlchemy model successfully"""
    from app.models.project import Project

    assert Project is not None
