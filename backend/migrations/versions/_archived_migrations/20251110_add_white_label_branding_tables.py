"""Add white-label branding tables (organization_branding, email_templates)

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-11-10 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization_branding table
    op.create_table(
        'organization_branding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Company identification
        sa.Column('company_name', sa.String(length=200), nullable=True),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('tagline', sa.String(length=500), nullable=True),

        # Logo files
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('logo_dark_url', sa.String(length=500), nullable=True),  # For dark mode
        sa.Column('logo_small_url', sa.String(length=500), nullable=True),  # Favicon/small icon
        sa.Column('logo_email_url', sa.String(length=500), nullable=True),  # For email headers

        # Color scheme
        # Structure: {
        #   "primary": "#1976d2",
        #   "secondary": "#dc004e",
        #   "accent": "#9c27b0",
        #   "background": "#ffffff",
        #   "surface": "#f5f5f5",
        #   "text_primary": "#000000",
        #   "text_secondary": "#666666"
        # }
        sa.Column('color_scheme', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Theme settings
        # Structure: {
        #   "mode": "light|dark|auto",
        #   "font_family": "Roboto",
        #   "border_radius": "4px",
        #   "spacing_unit": "8px",
        #   "custom_css": "..."
        # }
        sa.Column('theme_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Custom domain
        sa.Column('custom_domain', sa.String(length=255), nullable=True),
        sa.Column('custom_subdomain', sa.String(length=100), nullable=True),

        # Contact information
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('support_phone', sa.String(length=50), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),

        # Address
        sa.Column('address_line1', sa.String(length=255), nullable=True),
        sa.Column('address_line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state_province', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),

        # Email footer
        sa.Column('email_footer_text', sa.Text(), nullable=True),
        sa.Column('email_signature', sa.Text(), nullable=True),

        # Social media links
        # Structure: {
        #   "linkedin": "https://linkedin.com/company/...",
        #   "twitter": "https://twitter.com/...",
        #   "facebook": "https://facebook.com/...",
        #   "instagram": "https://instagram.com/..."
        # }
        sa.Column('social_media_links', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Feature flags
        # Structure: {
        #   "show_powered_by": false,
        #   "custom_login_page": true,
        #   "custom_error_pages": true,
        #   "whitelabel_emails": true
        # }
        sa.Column('feature_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Login page customization
        # Structure: {
        #   "background_image": "url",
        #   "welcome_message": "Welcome to...",
        #   "login_box_style": {...}
        # }
        sa.Column('login_page_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', name='uq_branding_per_org'),
        sa.Index('idx_organization_branding_org', 'organization_id'),
        sa.Index('idx_organization_branding_subdomain', 'custom_subdomain'),
    )

    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Template identification
        sa.Column('template_code', sa.String(length=100), nullable=False),
        sa.Column('template_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Template type
        sa.Column('template_type', sa.String(length=50), nullable=False),  # TRANSACTIONAL, MARKETING, NOTIFICATION

        # Email content
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=True),  # Plain text fallback

        # Template variables
        # Structure: [
        #   {"name": "user_name", "type": "string", "required": true, "description": "User's full name"},
        #   {"name": "order_number", "type": "string", "required": true}
        # ]
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Header/Footer
        sa.Column('include_header', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('include_footer', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('custom_header_html', sa.Text(), nullable=True),
        sa.Column('custom_footer_html', sa.Text(), nullable=True),

        # Sender information
        sa.Column('from_name', sa.String(length=200), nullable=True),
        sa.Column('from_email', sa.String(length=255), nullable=True),
        sa.Column('reply_to_email', sa.String(length=255), nullable=True),

        # Settings
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),  # Default template for this type
        sa.Column('is_system_template', sa.Boolean(), nullable=False, server_default='false'),  # Can't be deleted
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Version control
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'template_code', name='uq_email_template_code_per_org'),
        sa.Index('idx_email_templates_org', 'organization_id'),
        sa.Index('idx_email_templates_type', 'template_type'),
        sa.Index('idx_email_templates_code', 'template_code'),
        sa.CheckConstraint(
            "template_type IN ('TRANSACTIONAL', 'MARKETING', 'NOTIFICATION', 'SYSTEM')",
            name='chk_email_template_type_valid'
        ),
    )

    # Enable RLS on both tables
    op.execute("ALTER TABLE organization_branding ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY organization_branding_org_isolation ON organization_branding
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY email_templates_org_isolation ON email_templates
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Insert default system email templates for all organizations
    op.execute("""
        INSERT INTO email_templates (organization_id, template_code, template_name, template_type, subject, body_html, body_text, is_system_template, is_default, created_by, variables)
        SELECT
            id as organization_id,
            'WELCOME_EMAIL' as template_code,
            'Welcome Email' as template_name,
            'TRANSACTIONAL' as template_type,
            'Welcome to {{company_name}}!' as subject,
            '<h1>Welcome {{user_name}}!</h1><p>Thank you for joining {{company_name}}. We are excited to have you on board.</p>' as body_html,
            'Welcome {{user_name}}! Thank you for joining {{company_name}}. We are excited to have you on board.' as body_text,
            true as is_system_template,
            true as is_default,
            1 as created_by,
            '[{"name":"user_name","type":"string","required":true},{"name":"company_name","type":"string","required":true}]'::jsonb as variables
        FROM organizations
        WHERE is_active = true;
    """)

    op.execute("""
        INSERT INTO email_templates (organization_id, template_code, template_name, template_type, subject, body_html, body_text, is_system_template, is_default, created_by, variables)
        SELECT
            id as organization_id,
            'PASSWORD_RESET' as template_code,
            'Password Reset' as template_name,
            'TRANSACTIONAL' as template_type,
            'Password Reset Request' as subject,
            '<h1>Password Reset</h1><p>Hello {{user_name}},</p><p>We received a request to reset your password. Click the link below to reset it:</p><p><a href="{{reset_link}}">Reset Password</a></p><p>This link expires in {{expiry_hours}} hours.</p>' as body_html,
            'Hello {{user_name}}, We received a request to reset your password. Click the link below: {{reset_link}}. This link expires in {{expiry_hours}} hours.' as body_text,
            true as is_system_template,
            true as is_default,
            1 as created_by,
            '[{"name":"user_name","type":"string","required":true},{"name":"reset_link","type":"string","required":true},{"name":"expiry_hours","type":"number","required":true}]'::jsonb as variables
        FROM organizations
        WHERE is_active = true;
    """)

    op.execute("""
        INSERT INTO email_templates (organization_id, template_code, template_name, template_type, subject, body_html, body_text, is_system_template, is_default, created_by, variables)
        SELECT
            id as organization_id,
            'NCR_NOTIFICATION' as template_code,
            'NCR Notification' as template_name,
            'NOTIFICATION' as template_type,
            'New Non-Conformance Report: {{ncr_number}}' as subject,
            '<h1>Non-Conformance Report</h1><p>A new NCR has been created:</p><p><strong>NCR Number:</strong> {{ncr_number}}</p><p><strong>Work Order:</strong> {{work_order_number}}</p><p><strong>Defect Type:</strong> {{defect_type}}</p><p><strong>Description:</strong> {{description}}</p>' as body_html,
            'A new NCR has been created: {{ncr_number}}. Work Order: {{work_order_number}}. Defect Type: {{defect_type}}.' as body_text,
            true as is_system_template,
            true as is_default,
            1 as created_by,
            '[{"name":"ncr_number","type":"string","required":true},{"name":"work_order_number","type":"string","required":true},{"name":"defect_type","type":"string","required":true},{"name":"description","type":"string","required":false}]'::jsonb as variables
        FROM organizations
        WHERE is_active = true;
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS organization_branding_org_isolation ON organization_branding")
    op.execute("DROP POLICY IF EXISTS email_templates_org_isolation ON email_templates")

    # Drop tables
    op.drop_table('email_templates')
    op.drop_table('organization_branding')
