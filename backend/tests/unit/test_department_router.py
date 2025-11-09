"""
Unit tests for Department Router.

Tests route registration and dependencies without full integration.
"""

import pytest


def test_department_router_import():
    """Should import department router successfully"""
    from app.presentation.api.v1.departments import router

    assert router is not None


def test_department_router_routes():
    """Should have all expected routes registered"""
    from app.presentation.api.v1.departments import router

    routes = [route.path for route in router.routes]

    assert "/" in routes  # List and Create
    assert "/{dept_id}" in routes  # Get, Update, Delete

    # Check all HTTP methods are present
    methods_by_path = {}
    for route in router.routes:
        if route.path not in methods_by_path:
            methods_by_path[route.path] = set()
        methods_by_path[route.path].update(route.methods)

    # List and Create on /
    assert "GET" in methods_by_path["/"]
    assert "POST" in methods_by_path["/"]

    # Get, Update, Delete on /{dept_id}
    assert "GET" in methods_by_path["/{dept_id}"]
    assert "PUT" in methods_by_path["/{dept_id}"]
    assert "DELETE" in methods_by_path["/{dept_id}"]


def test_department_dto_imports():
    """Should import all DTOs successfully"""
    from app.application.dtos.department_dto import (
        DepartmentCreateRequest,
        DepartmentUpdateRequest,
        DepartmentResponse,
        DepartmentListResponse,
    )

    assert DepartmentCreateRequest is not None
    assert DepartmentUpdateRequest is not None
    assert DepartmentResponse is not None
    assert DepartmentListResponse is not None


def test_department_repository_import():
    """Should import repository successfully"""
    from app.infrastructure.repositories.department_repository import DepartmentRepository

    assert DepartmentRepository is not None
