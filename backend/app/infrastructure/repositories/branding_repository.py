"""
Repository for White-Label Branding (Organization Branding, Email Templates)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.branding import (
    OrganizationBranding,
    EmailTemplate
)
from app.application.dtos.branding_dto import (
    OrganizationBrandingCreateDTO,
    OrganizationBrandingUpdateDTO,
    EmailTemplateCreateDTO,
    EmailTemplateUpdateDTO,
)


class OrganizationBrandingRepository:
    """Repository for OrganizationBranding operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: OrganizationBrandingCreateDTO) -> OrganizationBranding:
        """Create organization branding"""
        branding = OrganizationBranding(
            organization_id=dto.organization_id,
            company_name=dto.company_name,
            display_name=dto.display_name,
            tagline=dto.tagline,
            logo_url=dto.logo_url,
            logo_dark_url=dto.logo_dark_url,
            logo_small_url=dto.logo_small_url,
            logo_email_url=dto.logo_email_url,
            color_scheme=dto.color_scheme,
            theme_settings=dto.theme_settings,
            custom_domain=dto.custom_domain,
            custom_subdomain=dto.custom_subdomain,
            support_email=dto.support_email,
            support_phone=dto.support_phone,
            website_url=dto.website_url,
            address_line1=dto.address_line1,
            address_line2=dto.address_line2,
            city=dto.city,
            state_province=dto.state_province,
            postal_code=dto.postal_code,
            country=dto.country,
            email_footer_text=dto.email_footer_text,
            email_signature=dto.email_signature,
            social_media_links=dto.social_media_links,
            feature_flags=dto.feature_flags,
            login_page_config=dto.login_page_config,
        )
        self.db.add(branding)
        self.db.commit()
        self.db.refresh(branding)
        return branding

    def get_by_id(self, branding_id: int) -> Optional[OrganizationBranding]:
        """Get organization branding by ID"""
        return self.db.query(OrganizationBranding).filter(
            OrganizationBranding.id == branding_id
        ).first()

    def get_by_organization(self, organization_id: int) -> Optional[OrganizationBranding]:
        """Get organization branding by organization ID"""
        return self.db.query(OrganizationBranding).filter(
            and_(
                OrganizationBranding.organization_id == organization_id,
                OrganizationBranding.is_active == True
            )
        ).first()

    def get_by_subdomain(self, subdomain: str) -> Optional[OrganizationBranding]:
        """Get organization branding by custom subdomain"""
        return self.db.query(OrganizationBranding).filter(
            and_(
                OrganizationBranding.custom_subdomain == subdomain,
                OrganizationBranding.is_active == True
            )
        ).first()

    def get_by_domain(self, domain: str) -> Optional[OrganizationBranding]:
        """Get organization branding by custom domain"""
        return self.db.query(OrganizationBranding).filter(
            and_(
                OrganizationBranding.custom_domain == domain,
                OrganizationBranding.is_active == True
            )
        ).first()

    def update(self, branding_id: int, dto: OrganizationBrandingUpdateDTO,
               updated_by: int) -> Optional[OrganizationBranding]:
        """Update organization branding"""
        branding = self.get_by_id(branding_id)
        if not branding:
            return None

        if dto.company_name is not None:
            branding.company_name = dto.company_name
        if dto.display_name is not None:
            branding.display_name = dto.display_name
        if dto.tagline is not None:
            branding.tagline = dto.tagline
        if dto.logo_url is not None:
            branding.logo_url = dto.logo_url
        if dto.logo_dark_url is not None:
            branding.logo_dark_url = dto.logo_dark_url
        if dto.logo_small_url is not None:
            branding.logo_small_url = dto.logo_small_url
        if dto.logo_email_url is not None:
            branding.logo_email_url = dto.logo_email_url
        if dto.color_scheme is not None:
            branding.color_scheme = dto.color_scheme
        if dto.theme_settings is not None:
            branding.theme_settings = dto.theme_settings
        if dto.custom_domain is not None:
            branding.custom_domain = dto.custom_domain
        if dto.custom_subdomain is not None:
            branding.custom_subdomain = dto.custom_subdomain
        if dto.support_email is not None:
            branding.support_email = dto.support_email
        if dto.support_phone is not None:
            branding.support_phone = dto.support_phone
        if dto.website_url is not None:
            branding.website_url = dto.website_url
        if dto.address_line1 is not None:
            branding.address_line1 = dto.address_line1
        if dto.address_line2 is not None:
            branding.address_line2 = dto.address_line2
        if dto.city is not None:
            branding.city = dto.city
        if dto.state_province is not None:
            branding.state_province = dto.state_province
        if dto.postal_code is not None:
            branding.postal_code = dto.postal_code
        if dto.country is not None:
            branding.country = dto.country
        if dto.email_footer_text is not None:
            branding.email_footer_text = dto.email_footer_text
        if dto.email_signature is not None:
            branding.email_signature = dto.email_signature
        if dto.social_media_links is not None:
            branding.social_media_links = dto.social_media_links
        if dto.feature_flags is not None:
            branding.feature_flags = dto.feature_flags
        if dto.login_page_config is not None:
            branding.login_page_config = dto.login_page_config

        branding.updated_by = updated_by
        self.db.commit()
        self.db.refresh(branding)
        return branding

    def delete(self, branding_id: int) -> bool:
        """Delete organization branding (soft delete)"""
        branding = self.get_by_id(branding_id)
        if not branding:
            return False

        branding.is_active = False
        self.db.commit()
        return True


class EmailTemplateRepository:
    """Repository for EmailTemplate operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: EmailTemplateCreateDTO) -> EmailTemplate:
        """Create email template"""
        template = EmailTemplate(
            organization_id=dto.organization_id,
            template_code=dto.template_code,
            template_name=dto.template_name,
            description=dto.description,
            template_type=dto.template_type,
            subject=dto.subject,
            body_html=dto.body_html,
            body_text=dto.body_text,
            variables=dto.variables,
            include_header=dto.include_header,
            include_footer=dto.include_footer,
            custom_header_html=dto.custom_header_html,
            custom_footer_html=dto.custom_footer_html,
            from_name=dto.from_name,
            from_email=dto.from_email,
            reply_to_email=dto.reply_to_email,
            created_by=dto.created_by,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: int) -> Optional[EmailTemplate]:
        """Get email template by ID"""
        return self.db.query(EmailTemplate).filter(
            EmailTemplate.id == template_id
        ).first()

    def get_by_code(self, organization_id: int, template_code: str) -> Optional[EmailTemplate]:
        """Get email template by code"""
        return self.db.query(EmailTemplate).filter(
            and_(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.template_code == template_code,
                EmailTemplate.is_active == True
            )
        ).first()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            template_type: Optional[str] = None,
                            active_only: bool = True) -> List[EmailTemplate]:
        """List email templates for an organization"""
        query = self.db.query(EmailTemplate).filter(
            EmailTemplate.organization_id == organization_id
        )

        if active_only:
            query = query.filter(EmailTemplate.is_active == True)

        if template_type:
            query = query.filter(EmailTemplate.template_type == template_type)

        return query.order_by(desc(EmailTemplate.created_at)).offset(skip).limit(limit).all()

    def list_by_type(self, organization_id: int, template_type: str) -> List[EmailTemplate]:
        """List email templates by type"""
        return self.db.query(EmailTemplate).filter(
            and_(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.template_type == template_type,
                EmailTemplate.is_active == True
            )
        ).order_by(EmailTemplate.template_name).all()

    def get_default_for_type(self, organization_id: int, template_type: str) -> Optional[EmailTemplate]:
        """Get default email template for a type"""
        return self.db.query(EmailTemplate).filter(
            and_(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.template_type == template_type,
                EmailTemplate.is_default == True,
                EmailTemplate.is_active == True
            )
        ).first()

    def list_system_templates(self, organization_id: int) -> List[EmailTemplate]:
        """List system templates (cannot be deleted)"""
        return self.db.query(EmailTemplate).filter(
            and_(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.is_system_template == True,
                EmailTemplate.is_active == True
            )
        ).order_by(EmailTemplate.template_name).all()

    def update(self, template_id: int, dto: EmailTemplateUpdateDTO,
               updated_by: int) -> Optional[EmailTemplate]:
        """Update email template"""
        template = self.get_by_id(template_id)
        if not template:
            return None

        # Don't allow updating system templates' core properties
        if template.is_system_template:
            # Only allow updating from_name, from_email, reply_to_email, is_active
            if dto.from_name is not None:
                template.from_name = dto.from_name
            if dto.from_email is not None:
                template.from_email = dto.from_email
            if dto.reply_to_email is not None:
                template.reply_to_email = dto.reply_to_email
            if dto.is_active is not None:
                template.is_active = dto.is_active
        else:
            # Non-system templates can be fully updated
            if dto.template_name is not None:
                template.template_name = dto.template_name
            if dto.description is not None:
                template.description = dto.description
            if dto.subject is not None:
                template.subject = dto.subject
            if dto.body_html is not None:
                template.body_html = dto.body_html
            if dto.body_text is not None:
                template.body_text = dto.body_text
            if dto.variables is not None:
                template.variables = dto.variables
            if dto.include_header is not None:
                template.include_header = dto.include_header
            if dto.include_footer is not None:
                template.include_footer = dto.include_footer
            if dto.custom_header_html is not None:
                template.custom_header_html = dto.custom_header_html
            if dto.custom_footer_html is not None:
                template.custom_footer_html = dto.custom_footer_html
            if dto.from_name is not None:
                template.from_name = dto.from_name
            if dto.from_email is not None:
                template.from_email = dto.from_email
            if dto.reply_to_email is not None:
                template.reply_to_email = dto.reply_to_email
            if dto.is_active is not None:
                template.is_active = dto.is_active

            # Increment version on content changes
            if any([dto.subject, dto.body_html, dto.body_text]):
                template.version += 1

        template.updated_by = updated_by
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete(self, template_id: int) -> bool:
        """Delete email template (soft delete, not allowed for system templates)"""
        template = self.get_by_id(template_id)
        if not template:
            return False

        # Don't allow deleting system templates
        if template.is_system_template:
            return False

        template.is_active = False
        self.db.commit()
        return True
