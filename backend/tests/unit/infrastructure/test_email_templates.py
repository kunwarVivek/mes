"""Unit tests for email template rendering."""
import pytest


def test_template_manager_initialization():
    """Test TemplateManager initializes correctly."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()
    assert manager is not None


def test_render_material_created_template():
    """Test rendering material created email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "material_code": "MAT-001",
        "material_description": "Test Material",
        "created_by": "John Doe",
        "base_uom": "EA"
    }

    html = manager.render("material_created", context)

    assert "MAT-001" in html
    assert "Test Material" in html
    assert "John Doe" in html


def test_render_work_order_released_template():
    """Test rendering work order released email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "work_order_number": "WO-12345",
        "material_code": "MAT-001",
        "quantity": 100,
        "status": "Released"
    }

    html = manager.render("work_order_released", context)

    assert "WO-12345" in html
    assert "MAT-001" in html
    assert "100" in html


def test_render_low_stock_alert_template():
    """Test rendering low stock alert email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "material_code": "MAT-001",
        "material_description": "Test Material",
        "current_stock": 5,
        "reorder_point": 10,
        "warehouse": "WH-01"
    }

    html = manager.render("low_stock_alert", context)

    assert "MAT-001" in html
    assert "5" in html
    assert "10" in html
    assert "WH-01" in html


def test_render_mrp_completed_template():
    """Test rendering MRP completion email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "run_id": "MRP-2024-001",
        "planned_orders_count": 15,
        "execution_time": "3 minutes"
    }

    html = manager.render("mrp_completed", context)

    assert "MRP-2024-001" in html
    assert "15" in html


def test_render_user_welcome_template():
    """Test rendering user welcome email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "username": "john.doe",
        "email": "john@example.com",
        "app_url": "https://unison.example.com"
    }

    html = manager.render("user_welcome", context)

    assert "john.doe" in html
    assert "unison.example.com" in html


def test_render_password_reset_template():
    """Test rendering password reset email template."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "username": "john.doe",
        "reset_token": "abc123def456",
        "reset_url": "https://unison.example.com/reset?token=abc123def456"
    }

    html = manager.render("password_reset", context)

    assert "john.doe" in html
    assert "abc123def456" in html or "reset?token=" in html


def test_render_missing_template_raises_error():
    """Test rendering non-existent template raises error."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    with pytest.raises(Exception):  # Will be TemplateNotFound
        manager.render("non_existent_template", {})


def test_template_manager_supports_plain_text():
    """Test TemplateManager can render plain text versions."""
    from app.infrastructure.email.templates import TemplateManager

    manager = TemplateManager()

    context = {
        "material_code": "MAT-001",
        "material_description": "Test Material",
        "created_by": "John Doe",
        "base_uom": "EA"
    }

    text = manager.render_text("material_created", context)

    assert "MAT-001" in text
    assert "Test Material" in text
    # Plain text shouldn't have HTML tags
    assert "<" not in text
