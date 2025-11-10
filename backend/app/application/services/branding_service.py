"""
Branding Service - Business logic for white-label branding and email templates
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.branding import (
    OrganizationBranding,
    EmailTemplate
)
from app.infrastructure.repositories.branding_repository import (
    OrganizationBrandingRepository,
    EmailTemplateRepository,
)
from app.application.dtos.branding_dto import (
    OrganizationBrandingCreateDTO,
    OrganizationBrandingUpdateDTO,
    EmailTemplateCreateDTO,
    EmailTemplateUpdateDTO,
    EmailRenderRequest,
    EmailRenderResponse,
)


class BrandingService:
    """Service for Organization Branding operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = OrganizationBrandingRepository(db)

    def create_branding(self, dto: OrganizationBrandingCreateDTO) -> OrganizationBranding:
        """Create organization branding (only one per organization)"""
        # Check if branding already exists for this organization
        existing = self.repo.get_by_organization(dto.organization_id)
        if existing:
            raise ValueError(f"Branding already exists for organization {dto.organization_id}")

        # Check for subdomain uniqueness if provided
        if dto.custom_subdomain:
            existing_subdomain = self.repo.get_by_subdomain(dto.custom_subdomain)
            if existing_subdomain:
                raise ValueError(f"Subdomain '{dto.custom_subdomain}' is already taken")

        # Check for domain uniqueness if provided
        if dto.custom_domain:
            existing_domain = self.repo.get_by_domain(dto.custom_domain)
            if existing_domain:
                raise ValueError(f"Domain '{dto.custom_domain}' is already taken")

        return self.repo.create(dto)

    def get_branding(self, branding_id: int) -> Optional[OrganizationBranding]:
        """Get branding by ID"""
        return self.repo.get_by_id(branding_id)

    def get_by_organization(self, organization_id: int) -> Optional[OrganizationBranding]:
        """Get branding by organization ID"""
        return self.repo.get_by_organization(organization_id)

    def get_by_subdomain(self, subdomain: str) -> Optional[OrganizationBranding]:
        """Get branding by custom subdomain"""
        return self.repo.get_by_subdomain(subdomain)

    def get_by_domain(self, domain: str) -> Optional[OrganizationBranding]:
        """Get branding by custom domain"""
        return self.repo.get_by_domain(domain)

    def update_branding(self, branding_id: int, dto: OrganizationBrandingUpdateDTO,
                       updated_by: int) -> Optional[OrganizationBranding]:
        """Update organization branding"""
        branding = self.repo.get_by_id(branding_id)
        if not branding:
            return None

        # Check subdomain uniqueness if changing
        if dto.custom_subdomain and dto.custom_subdomain != branding.custom_subdomain:
            existing = self.repo.get_by_subdomain(dto.custom_subdomain)
            if existing:
                raise ValueError(f"Subdomain '{dto.custom_subdomain}' is already taken")

        # Check domain uniqueness if changing
        if dto.custom_domain and dto.custom_domain != branding.custom_domain:
            existing = self.repo.get_by_domain(dto.custom_domain)
            if existing:
                raise ValueError(f"Domain '{dto.custom_domain}' is already taken")

        return self.repo.update(branding_id, dto, updated_by)

    def delete_branding(self, branding_id: int) -> bool:
        """Delete branding (soft delete)"""
        return self.repo.delete(branding_id)

    def get_logo_for_variant(self, organization_id: int, variant: str = 'default') -> Optional[str]:
        """Get logo URL for specific variant"""
        branding = self.repo.get_by_organization(organization_id)
        if not branding:
            return None
        return branding.get_logo(variant)

    def is_feature_enabled(self, organization_id: int, feature_name: str) -> bool:
        """Check if a white-label feature is enabled"""
        branding = self.repo.get_by_organization(organization_id)
        if not branding:
            return False
        return branding.is_feature_enabled(feature_name)

    def get_contact_info(self, organization_id: int) -> Optional[Dict[str, Any]]:
        """Get formatted contact information"""
        branding = self.repo.get_by_organization(organization_id)
        if not branding:
            return None

        return {
            'support_email': branding.support_email,
            'support_phone': branding.support_phone,
            'website_url': branding.website_url,
            'address': branding.get_full_address(),
        }


class EmailTemplateService:
    """Service for Email Template operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = EmailTemplateRepository(db)
        self.branding_repo = OrganizationBrandingRepository(db)

    def create_template(self, dto: EmailTemplateCreateDTO) -> EmailTemplate:
        """Create email template"""
        # Check for duplicate template code
        existing = self.repo.get_by_code(dto.organization_id, dto.template_code)
        if existing:
            raise ValueError(f"Template code '{dto.template_code}' already exists")

        return self.repo.create(dto)

    def get_template(self, template_id: int) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.repo.get_by_id(template_id)

    def get_by_code(self, organization_id: int, template_code: str) -> Optional[EmailTemplate]:
        """Get template by code"""
        return self.repo.get_by_code(organization_id, template_code)

    def list_templates(self, organization_id: int, skip: int = 0, limit: int = 100,
                      template_type: Optional[str] = None,
                      active_only: bool = True) -> List[EmailTemplate]:
        """List email templates"""
        return self.repo.list_by_organization(organization_id, skip, limit, template_type, active_only)

    def list_by_type(self, organization_id: int, template_type: str) -> List[EmailTemplate]:
        """List templates by type"""
        return self.repo.list_by_type(organization_id, template_type)

    def get_default_for_type(self, organization_id: int, template_type: str) -> Optional[EmailTemplate]:
        """Get default template for a type"""
        return self.repo.get_default_for_type(organization_id, template_type)

    def list_system_templates(self, organization_id: int) -> List[EmailTemplate]:
        """List system templates"""
        return self.repo.list_system_templates(organization_id)

    def update_template(self, template_id: int, dto: EmailTemplateUpdateDTO,
                       updated_by: int) -> Optional[EmailTemplate]:
        """Update email template"""
        return self.repo.update(template_id, dto, updated_by)

    def delete_template(self, template_id: int) -> bool:
        """Delete email template (not allowed for system templates)"""
        return self.repo.delete(template_id)

    def render_template(self, organization_id: int, request: EmailRenderRequest) -> EmailRenderResponse:
        """Render email template with context variables"""
        # Get template
        template = self.repo.get_by_code(organization_id, request.template_code)
        if not template:
            raise ValueError(f"Template '{request.template_code}' not found")

        if not template.is_active:
            raise ValueError(f"Template '{request.template_code}' is not active")

        # Validate required variables
        if template.variables:
            for var_def in template.variables:
                if isinstance(var_def, dict) and var_def.get('required', False):
                    var_name = var_def.get('name')
                    if var_name not in request.context:
                        raise ValueError(f"Required variable '{var_name}' is missing from context")

        # Render template
        rendered = template.render(request.context)

        # Include branding if requested
        if request.include_branding:
            branding = self.branding_repo.get_by_organization(organization_id)
            full_html = template.get_full_html(request.context, branding)
            rendered['body_html'] = full_html

        return EmailRenderResponse(
            subject=rendered['subject'],
            body_html=rendered['body_html'],
            body_text=rendered['body_text'],
            from_name=template.from_name,
            from_email=template.from_email,
            reply_to_email=template.reply_to_email,
        )

    def preview_template(self, template_id: int, context: Dict[str, Any]) -> Dict[str, str]:
        """Preview template rendering with sample context"""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        return template.render(context)

    def validate_template_variables(self, template_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all required variables are present"""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        result = {
            'is_valid': True,
            'missing_required': [],
            'missing_optional': [],
            'extra_variables': [],
        }

        if not template.variables:
            return result

        # Extract expected variable names
        expected_vars = set()
        required_vars = set()
        for var_def in template.variables:
            if isinstance(var_def, dict):
                var_name = var_def.get('name')
                expected_vars.add(var_name)
                if var_def.get('required', False):
                    required_vars.add(var_name)

        # Check for missing required variables
        for var_name in required_vars:
            if var_name not in context:
                result['missing_required'].append(var_name)
                result['is_valid'] = False

        # Check for missing optional variables
        optional_vars = expected_vars - required_vars
        for var_name in optional_vars:
            if var_name not in context:
                result['missing_optional'].append(var_name)

        # Check for extra variables
        for var_name in context.keys():
            if var_name not in expected_vars:
                result['extra_variables'].append(var_name)

        return result

    def get_template_variables(self, template_id: int) -> List[Dict[str, Any]]:
        """Get list of variables defined in template"""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        return template.variables or []
