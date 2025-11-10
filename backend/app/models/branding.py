"""
White-Label Branding models - Organization customization and email templates
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from typing import Optional, Dict, List
import re


# Enums
class TemplateType(str, Enum):
    """Email template type enumeration"""
    TRANSACTIONAL = "TRANSACTIONAL"  # Order confirmations, password resets
    MARKETING = "MARKETING"  # Newsletters, promotions
    NOTIFICATION = "NOTIFICATION"  # System notifications, alerts
    SYSTEM = "SYSTEM"  # System-generated emails


class OrganizationBranding(Base):
    """
    Organization Branding model.

    Supports complete white-label customization:
    - Logo and branding assets
    - Color schemes and themes
    - Custom domains
    - Contact information
    - Email branding
    - Social media links
    - Feature flags for white-labeling
    """
    __tablename__ = 'organization_branding'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Company identification
    company_name = Column(String(200), nullable=True)
    display_name = Column(String(200), nullable=True)
    tagline = Column(String(500), nullable=True)

    # Logo files
    logo_url = Column(String(500), nullable=True)
    logo_dark_url = Column(String(500), nullable=True)
    logo_small_url = Column(String(500), nullable=True)
    logo_email_url = Column(String(500), nullable=True)

    # Color scheme
    color_scheme = Column(JSONB, nullable=True)

    # Theme settings
    theme_settings = Column(JSONB, nullable=True)

    # Custom domain
    custom_domain = Column(String(255), nullable=True)
    custom_subdomain = Column(String(100), nullable=True, index=True)

    # Contact information
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    website_url = Column(String(500), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Email footer
    email_footer_text = Column(Text, nullable=True)
    email_signature = Column(Text, nullable=True)

    # Social media links
    social_media_links = Column(JSONB, nullable=True)

    # Feature flags
    feature_flags = Column(JSONB, nullable=True)

    # Login page customization
    login_page_config = Column(JSONB, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    # organization = relationship("Organization", backref="branding")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', name='uq_branding_per_org'),
        Index('idx_organization_branding_org', 'organization_id'),
        Index('idx_organization_branding_subdomain', 'custom_subdomain'),
    )

    def __repr__(self):
        return f"<OrganizationBranding(id={self.id}, org_id={self.organization_id}, company='{self.company_name}')>"

    def get_primary_color(self) -> Optional[str]:
        """Get primary brand color"""
        if self.color_scheme and isinstance(self.color_scheme, dict):
            return self.color_scheme.get('primary')
        return None

    def get_logo(self, variant: str = 'default') -> Optional[str]:
        """
        Get logo URL by variant.

        Args:
            variant: 'default', 'dark', 'small', 'email'

        Returns:
            Logo URL or None
        """
        if variant == 'dark':
            return self.logo_dark_url or self.logo_url
        elif variant == 'small':
            return self.logo_small_url or self.logo_url
        elif variant == 'email':
            return self.logo_email_url or self.logo_url
        else:
            return self.logo_url

    def get_full_address(self) -> Optional[str]:
        """Get formatted full address"""
        address_parts = []

        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)

        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state_province:
            city_state_zip.append(self.state_province)
        if self.postal_code:
            city_state_zip.append(self.postal_code)

        if city_state_zip:
            address_parts.append(", ".join(city_state_zip))

        if self.country:
            address_parts.append(self.country)

        return "\n".join(address_parts) if address_parts else None

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a white-label feature is enabled"""
        if not self.feature_flags or not isinstance(self.feature_flags, dict):
            return False
        return self.feature_flags.get(feature_name, False)

    def get_social_link(self, platform: str) -> Optional[str]:
        """Get social media link by platform"""
        if not self.social_media_links or not isinstance(self.social_media_links, dict):
            return None
        return self.social_media_links.get(platform)


class EmailTemplate(Base):
    """
    Email Template model.

    Supports customizable email templates for white-labeling:
    - HTML and plain text versions
    - Template variables
    - Custom headers/footers
    - Version control
    - Organization-specific branding
    """
    __tablename__ = 'email_templates'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Template identification
    template_code = Column(String(100), nullable=False, index=True)
    template_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Template type
    template_type = Column(String(50), nullable=False, index=True)

    # Email content
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)

    # Template variables
    variables = Column(JSONB, nullable=True)

    # Header/Footer
    include_header = Column(Boolean, nullable=False, default=True)
    include_footer = Column(Boolean, nullable=False, default=True)
    custom_header_html = Column(Text, nullable=True)
    custom_footer_html = Column(Text, nullable=True)

    # Sender information
    from_name = Column(String(200), nullable=True)
    from_email = Column(String(255), nullable=True)
    reply_to_email = Column(String(255), nullable=True)

    # Settings
    is_default = Column(Boolean, nullable=False, default=False)
    is_system_template = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Version control
    version = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'template_code', name='uq_email_template_code_per_org'),
        Index('idx_email_templates_org', 'organization_id'),
        Index('idx_email_templates_type', 'template_type'),
        Index('idx_email_templates_code', 'template_code'),
        CheckConstraint(
            "template_type IN ('TRANSACTIONAL', 'MARKETING', 'NOTIFICATION', 'SYSTEM')",
            name='chk_email_template_type_valid'
        ),
    )

    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, code='{self.template_code}', type='{self.template_type}')>"

    def render(self, context: Dict) -> Dict[str, str]:
        """
        Render template with provided context.

        Args:
            context: Dictionary of variables to substitute

        Returns:
            Dictionary with 'subject', 'body_html', 'body_text'
        """
        rendered = {
            'subject': self._substitute_variables(self.subject, context),
            'body_html': self._substitute_variables(self.body_html, context),
            'body_text': self._substitute_variables(self.body_text or '', context) if self.body_text else None,
        }

        return rendered

    def _substitute_variables(self, text: str, context: Dict) -> str:
        """
        Substitute {{variable}} placeholders with context values.

        Args:
            text: Template text with {{variable}} placeholders
            context: Dictionary of variable values

        Returns:
            Text with variables substituted
        """
        if not text:
            return ''

        # Find all {{variable}} patterns
        pattern = r'\{\{(\w+)\}\}'

        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))  # Keep {{var}} if not found

        return re.sub(pattern, replace_var, text)

    def get_required_variables(self) -> List[str]:
        """Get list of required template variables"""
        if not self.variables or not isinstance(self.variables, list):
            return []

        return [
            var['name']
            for var in self.variables
            if isinstance(var, dict) and var.get('required', False)
        ]

    def validate_context(self, context: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate that context contains all required variables.

        Args:
            context: Dictionary of variable values

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_vars = self.get_required_variables()
        missing_vars = [var for var in required_vars if var not in context]

        if missing_vars:
            return False, f"Missing required variables: {', '.join(missing_vars)}"

        return True, None

    def get_full_html(self, context: Dict, branding: Optional[OrganizationBranding] = None) -> str:
        """
        Get full HTML email with header and footer.

        Args:
            context: Template context
            branding: Optional organization branding for header/footer

        Returns:
            Complete HTML email
        """
        parts = []

        # Add header
        if self.include_header:
            if self.custom_header_html:
                parts.append(self.custom_header_html)
            elif branding and branding.logo_email_url:
                parts.append(f'<div style="text-align:center;padding:20px;"><img src="{branding.logo_email_url}" alt="Logo" style="max-height:60px;"/></div>')

        # Add body
        parts.append(self._substitute_variables(self.body_html, context))

        # Add footer
        if self.include_footer:
            if self.custom_footer_html:
                parts.append(self.custom_footer_html)
            elif branding:
                footer_parts = []
                if branding.email_footer_text:
                    footer_parts.append(f'<p style="color:#666;font-size:12px;">{branding.email_footer_text}</p>')
                if branding.support_email:
                    footer_parts.append(f'<p style="color:#666;font-size:12px;">Support: <a href="mailto:{branding.support_email}">{branding.support_email}</a></p>')

                if footer_parts:
                    parts.append(f'<div style="border-top:1px solid #ddd;margin-top:30px;padding-top:20px;text-align:center;">{"".join(footer_parts)}</div>')

        return '\n'.join(parts)
