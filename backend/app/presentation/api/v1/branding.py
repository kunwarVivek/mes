"""
API endpoints for White-Label Branding module
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.application.dtos.branding_dto import (
    OrganizationBrandingCreateDTO,
    OrganizationBrandingUpdateDTO,
    OrganizationBrandingResponse,
    EmailTemplateCreateDTO,
    EmailTemplateUpdateDTO,
    EmailTemplateResponse,
    EmailRenderRequest,
    EmailRenderResponse,
)
from app.application.services.branding_service import (
    BrandingService,
    EmailTemplateService,
)

router = APIRouter(prefix="/branding", tags=["branding"])


# ==================== Organization Branding Endpoints ====================

@router.post("/organizations", response_model=OrganizationBrandingResponse, status_code=status.HTTP_201_CREATED)
def create_organization_branding(
    branding_data: OrganizationBrandingCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create organization branding configuration"""
    service = BrandingService(db)
    try:
        return service.create_branding(branding_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{branding_id}", response_model=OrganizationBrandingResponse)
def get_organization_branding(
    branding_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization branding by ID"""
    service = BrandingService(db)
    branding = service.get_branding(branding_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding {branding_id} not found")
    return branding


@router.get("/organizations/by-org/{organization_id}", response_model=OrganizationBrandingResponse)
def get_branding_by_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization branding by organization ID"""
    service = BrandingService(db)
    branding = service.get_by_organization(organization_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding not found for organization {organization_id}")
    return branding


@router.get("/organizations/by-subdomain/{subdomain}", response_model=OrganizationBrandingResponse)
def get_branding_by_subdomain(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Get organization branding by custom subdomain (public endpoint)"""
    service = BrandingService(db)
    branding = service.get_by_subdomain(subdomain)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding not found for subdomain '{subdomain}'")
    return branding


@router.get("/organizations/by-domain/{domain}", response_model=OrganizationBrandingResponse)
def get_branding_by_domain(
    domain: str,
    db: Session = Depends(get_db)
):
    """Get organization branding by custom domain (public endpoint)"""
    service = BrandingService(db)
    branding = service.get_by_domain(domain)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding not found for domain '{domain}'")
    return branding


@router.patch("/organizations/{branding_id}", response_model=OrganizationBrandingResponse)
def update_organization_branding(
    branding_id: int,
    branding_data: OrganizationBrandingUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update organization branding"""
    service = BrandingService(db)
    user_id = current_user.get("id", 0)
    try:
        branding = service.update_branding(branding_id, branding_data, user_id)
        if not branding:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding {branding_id} not found")
        return branding
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/organizations/{branding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_branding(
    branding_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete organization branding (soft delete)"""
    service = BrandingService(db)
    if not service.delete_branding(branding_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding {branding_id} not found")


@router.get("/organizations/{organization_id}/logo", response_model=Dict[str, Optional[str]])
def get_organization_logos(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all logo variants for an organization"""
    service = BrandingService(db)
    return {
        'default': service.get_logo_for_variant(organization_id, 'default'),
        'dark': service.get_logo_for_variant(organization_id, 'dark'),
        'small': service.get_logo_for_variant(organization_id, 'small'),
        'email': service.get_logo_for_variant(organization_id, 'email'),
    }


@router.get("/organizations/{organization_id}/feature/{feature_name}", response_model=Dict[str, bool])
def check_feature_enabled(
    organization_id: int,
    feature_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if a white-label feature is enabled"""
    service = BrandingService(db)
    return {
        'feature_name': feature_name,
        'enabled': service.is_feature_enabled(organization_id, feature_name)
    }


@router.get("/organizations/{organization_id}/contact", response_model=Dict[str, Any])
def get_contact_info(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization contact information"""
    service = BrandingService(db)
    contact_info = service.get_contact_info(organization_id)
    if not contact_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branding not found for organization {organization_id}")
    return contact_info


# ==================== Email Template Endpoints ====================

@router.post("/email-templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_email_template(
    template_data: EmailTemplateCreateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create email template"""
    service = EmailTemplateService(db)
    try:
        return service.create_template(template_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/email-templates", response_model=List[EmailTemplateResponse])
def list_email_templates(
    organization_id: int = Query(..., gt=0),
    template_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List email templates"""
    service = EmailTemplateService(db)
    return service.list_templates(organization_id, skip, limit, template_type, active_only)


@router.get("/email-templates/{template_id}", response_model=EmailTemplateResponse)
def get_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get email template by ID"""
    service = EmailTemplateService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_id} not found")
    return template


@router.get("/email-templates/by-code/{template_code}", response_model=EmailTemplateResponse)
def get_template_by_code(
    template_code: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get email template by code"""
    service = EmailTemplateService(db)
    template = service.get_by_code(organization_id, template_code)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{template_code}' not found")
    return template


@router.get("/email-templates/by-type/{template_type}", response_model=List[EmailTemplateResponse])
def list_templates_by_type(
    template_type: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List email templates by type"""
    service = EmailTemplateService(db)
    return service.list_by_type(organization_id, template_type)


@router.get("/email-templates/default/{template_type}", response_model=EmailTemplateResponse)
def get_default_template(
    template_type: str,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get default email template for a type"""
    service = EmailTemplateService(db)
    template = service.get_default_for_type(organization_id, template_type)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No default template found for type '{template_type}'")
    return template


@router.get("/email-templates/system-templates", response_model=List[EmailTemplateResponse])
def list_system_templates(
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List system email templates"""
    service = EmailTemplateService(db)
    return service.list_system_templates(organization_id)


@router.patch("/email-templates/{template_id}", response_model=EmailTemplateResponse)
def update_email_template(
    template_id: int,
    template_data: EmailTemplateUpdateDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update email template"""
    service = EmailTemplateService(db)
    user_id = current_user.get("id", 0)
    template = service.update_template(template_id, template_data, user_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_id} not found")
    return template


@router.delete("/email-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete email template (not allowed for system templates)"""
    service = EmailTemplateService(db)
    if not service.delete_template(template_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot delete template {template_id} (not found or is system template)")


@router.post("/email-templates/render", response_model=EmailRenderResponse)
def render_email_template(
    render_request: EmailRenderRequest,
    organization_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Render email template with context variables"""
    service = EmailTemplateService(db)
    try:
        return service.render_template(organization_id, render_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/email-templates/{template_id}/preview", response_model=Dict[str, str])
def preview_email_template(
    template_id: int,
    context: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Preview email template rendering with sample context"""
    service = EmailTemplateService(db)
    try:
        return service.preview_template(template_id, context)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/email-templates/{template_id}/validate-variables", response_model=Dict[str, Any])
def validate_template_variables(
    template_id: int,
    context: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate that all required template variables are present"""
    service = EmailTemplateService(db)
    try:
        return service.validate_template_variables(template_id, context)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/email-templates/{template_id}/variables", response_model=List[Dict[str, Any]])
def get_template_variables(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of variables defined in template"""
    service = EmailTemplateService(db)
    try:
        return service.get_template_variables(template_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
