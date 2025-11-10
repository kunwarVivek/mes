"""add_onboarding_fields_and_pending_invitations

Adds onboarding tracking fields to users table and creates pending_invitations table
for team invitation workflow during self-service onboarding.

Onboarding Flow:
1. pending_verification: User signed up, awaiting email verification
2. email_verified: Email verified, needs to create organization
3. org_setup: Organization created, needs to create plant
4. plant_created: Plant created, can optionally invite team members
5. invites_sent: Invitations sent (optional step)
6. completed: Onboarding complete, redirect to dashboard

Revision ID: 6b45b7106468
Revises: ef6ec56e007e
Create Date: 2025-11-10 00:18:06.353394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b45b7106468'
down_revision = 'ef6ec56e007e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for onboarding status
    onboarding_status_enum = sa.Enum(
        'pending_verification',
        'email_verified',
        'org_setup',
        'plant_created',
        'invites_sent',
        'completed',
        name='onboarding_status_enum',
        create_type=True
    )
    onboarding_status_enum.create(op.get_bind(), checkfirst=True)

    # Add onboarding fields to users table
    op.add_column('users', sa.Column(
        'onboarding_status',
        onboarding_status_enum,
        nullable=False,
        server_default='pending_verification'
    ))
    op.add_column('users', sa.Column(
        'verification_token',
        sa.Text(),
        nullable=True,
        comment='JWT token for email verification (24h expiry)'
    ))
    op.add_column('users', sa.Column(
        'verification_token_expires_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Expiry timestamp for verification token'
    ))
    op.add_column('users', sa.Column(
        'onboarding_completed_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Timestamp when onboarding was completed'
    ))

    # Create index on onboarding_status for filtering incomplete onboardings
    op.create_index(
        'idx_users_onboarding_status',
        'users',
        ['onboarding_status'],
        unique=False
    )

    # Create pending_invitations table for team invitations during onboarding
    op.create_table(
        'pending_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inviter_id', sa.Integer(), nullable=False, comment='User who sent the invitation'),
        sa.Column('organization_id', sa.Integer(), nullable=False, comment='Organization to join'),
        sa.Column('plant_id', sa.Integer(), nullable=True, comment='Specific plant (optional)'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Invitee email address'),
        sa.Column('role', sa.String(length=50), nullable=False, comment='Assigned role (e.g., operator, manager)'),
        sa.Column('token', sa.Text(), nullable=False, comment='Unique invitation token (JWT)'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='email_queued', comment='email_queued, email_sent, accepted, expired'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Invitation expiry (7 days default)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when invitation was accepted'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['inviter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token', name='uq_pending_invitations_token')
    )

    # Create indexes for pending_invitations
    op.create_index('idx_pending_invitations_email', 'pending_invitations', ['email'], unique=False)
    op.create_index('idx_pending_invitations_token', 'pending_invitations', ['token'], unique=False)
    op.create_index('idx_pending_invitations_status', 'pending_invitations', ['status'], unique=False)
    op.create_index('idx_pending_invitations_org', 'pending_invitations', ['organization_id'], unique=False)


def downgrade() -> None:
    # Drop pending_invitations table and indexes
    op.drop_index('idx_pending_invitations_org', table_name='pending_invitations')
    op.drop_index('idx_pending_invitations_status', table_name='pending_invitations')
    op.drop_index('idx_pending_invitations_token', table_name='pending_invitations')
    op.drop_index('idx_pending_invitations_email', table_name='pending_invitations')
    op.drop_table('pending_invitations')

    # Drop users table onboarding fields
    op.drop_index('idx_users_onboarding_status', table_name='users')
    op.drop_column('users', 'onboarding_completed_at')
    op.drop_column('users', 'verification_token_expires_at')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'onboarding_status')

    # Drop ENUM type
    sa.Enum(name='onboarding_status_enum').drop(op.get_bind(), checkfirst=True)
