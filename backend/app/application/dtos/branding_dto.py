"""
DTOs for White-Label Branding (Organization branding, Email templates)
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, Dict, List, Any
from datetime import datetime


# ========== Organization Branding DTOs ==========

class OrganizationBrandingCreateDTO(BaseModel):
    """DTO for creating organization branding"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    tagline: Optional[str] = Field(None, max_length=500, description="Company tagline")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    logo_dark_url: Optional[str] = Field(None, max_length=500, description="Dark mode logo URL")
    logo_small_url: Optional[str] = Field(None, max_length=500, description="Small logo/favicon URL")
    logo_email_url: Optional[str] = Field(None, max_length=500, description="Email logo URL")
    color_scheme: Optional[Dict[str, str]] = Field(None, description="Color scheme configuration")
    theme_settings: Optional[Dict[str, Any]] = Field(None, description="Theme settings")
    custom_domain: Optional[str] = Field(None, max_length=255, description="Custom domain")
    custom_subdomain: Optional[str] = Field(None, max_length=100, description="Custom subdomain")
    support_email: Optional[EmailStr] = Field(None, description="Support email")
    support_phone: Optional[str] = Field(None, max_length=50, description="Support phone")
    website_url: Optional[str] = Field(None, max_length=500, description="Website URL")
    address_line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state_province: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    email_footer_text: Optional[str] = Field(None, description="Email footer text")
    email_signature: Optional[str] = Field(None, description="Email signature")
    social_media_links: Optional[Dict[str, str]] = Field(None, description="Social media links")
    feature_flags: Optional[Dict[str, bool]] = Field(None, description="White-label feature flags")
    login_page_config: Optional[Dict[str, Any]] = Field(None, description="Login page customization")


class OrganizationBrandingUpdateDTO(BaseModel):
    """DTO for updating organization branding"""
    company_name: Optional[str] = Field(None, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    tagline: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    logo_dark_url: Optional[str] = Field(None, max_length=500)
    logo_small_url: Optional[str] = Field(None, max_length=500)
    logo_email_url: Optional[str] = Field(None, max_length=500)
    color_scheme: Optional[Dict[str, str]] = None
    theme_settings: Optional[Dict[str, Any]] = None
    custom_domain: Optional[str] = Field(None, max_length=255)
    custom_subdomain: Optional[str] = Field(None, max_length=100)
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = Field(None, max_length=50)
    website_url: Optional[str] = Field(None, max_length=500)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    email_footer_text: Optional[str] = None
    email_signature: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None
    feature_flags: Optional[Dict[str, bool]] = None
    login_page_config: Optional[Dict[str, Any]] = None


class OrganizationBrandingResponse(BaseModel):
    """DTO for organization branding response"""
    id: int
    organization_id: int
    company_name: Optional[str]
    display_name: Optional[str]
    tagline: Optional[str]
    logo_url: Optional[str]
    logo_dark_url: Optional[str]
    logo_small_url: Optional[str]
    logo_email_url: Optional[str]
    color_scheme: Optional[Dict[str, str]]
    theme_settings: Optional[Dict[str, Any]]
    custom_domain: Optional[str]
    custom_subdomain: Optional[str]
    support_email: Optional[str]
    support_phone: Optional[str]
    website_url: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    email_footer_text: Optional[str]
    email_signature: Optional[str]
    social_media_links: Optional[Dict[str, str]]
    feature_flags: Optional[Dict[str, bool]]
    login_page_config: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# ========== Email Template DTOs ==========

class EmailTemplateCreateDTO(BaseModel):
    """DTO for creating email template"""
    organization_id: int = Field(..., gt=0, description="Organization ID")
    template_code: str = Field(..., min_length=1, max_length=100, description="Template code")
    template_name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Description")
    template_type: str = Field(..., description="Template type")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body_html: str = Field(..., min_length=1, description="HTML body")
    body_text: Optional[str] = Field(None, description="Plain text body")
    variables: Optional[List[Dict[str, Any]]] = Field(None, description="Template variables")
    include_header: bool = Field(default=True, description="Include header")
    include_footer: bool = Field(default=True, description="Include footer")
    custom_header_html: Optional[str] = Field(None, description="Custom header HTML")
    custom_footer_html: Optional[str] = Field(None, description="Custom footer HTML")
    from_name: Optional[str] = Field(None, max_length=200, description="From name")
    from_email: Optional[EmailStr] = Field(None, description="From email")
    reply_to_email: Optional[EmailStr] = Field(None, description="Reply-to email")
    created_by: int = Field(..., gt=0, description="Created by user ID")

    @field_validator('template_type')
    @classmethod
    def validate_template_type(cls, v):
        valid_types = ['TRANSACTIONAL', 'MARKETING', 'NOTIFICATION', 'SYSTEM']
        if v not in valid_types:
            raise ValueError(f'template_type must be one of {valid_types}')
        return v


class EmailTemplateUpdateDTO(BaseModel):
    """DTO for updating email template"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    body_html: Optional[str] = Field(None, min_length=1)
    body_text: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    include_header: Optional[bool] = None
    include_footer: Optional[bool] = None
    custom_header_html: Optional[str] = None
    custom_footer_html: Optional[str] = None
    from_name: Optional[str] = Field(None, max_length=200)
    from_email: Optional[EmailStr] = None
    reply_to_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    """DTO for email template response"""
    id: int
    organization_id: int
    template_code: str
    template_name: str
    description: Optional[str]
    template_type: str
    subject: str
    body_html: str
    body_text: Optional[str]
    variables: Optional[List[Dict[str, Any]]]
    include_header: bool
    include_footer: bool
    custom_header_html: Optional[str]
    custom_footer_html: Optional[str]
    from_name: Optional[str]
    from_email: Optional[str]
    reply_to_email: Optional[str]
    is_default: bool
    is_system_template: bool
    is_active: bool
    version: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]

    class Config:
        from_attributes = True


# ========== Email Rendering DTOs ==========

class EmailRenderRequest(BaseModel):
    """DTO for rendering an email template"""
    template_code: str = Field(..., description="Template code to render")
    context: Dict[str, Any] = Field(..., description="Template context variables")
    include_branding: bool = Field(default=True, description="Include organization branding")


class EmailRenderResponse(BaseModel):
    """DTO for rendered email response"""
    subject: str
    body_html: str
    body_text: Optional[str]
    from_name: Optional[str]
    from_email: Optional[str]
    reply_to_email: Optional[str]


class EmailSendRequest(BaseModel):
    """DTO for sending email"""
    template_code: str = Field(..., description="Template code")
    to_email: EmailStr = Field(..., description="Recipient email")
    to_name: Optional[str] = Field(None, description="Recipient name")
    context: Dict[str, Any] = Field(..., description="Template context")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
