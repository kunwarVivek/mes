"""Add RBAC tables (roles, user_roles, user_plant_access)

Revision ID: a1b2c3d4e5f6
Revises: ef6ec56e007e
Create Date: 2025-11-09 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ef6ec56e007e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('role_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'role_code', name='uq_role_code_per_org'),
        sa.Index('idx_role_org', 'organization_id'),
        sa.Index('idx_role_code', 'organization_id', 'role_code'),
    )

    # Create user_roles table (many-to-many with optional scope)
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=True),  # Optional: role scoped to specific plant
        sa.Column('department_id', sa.Integer(), nullable=True),  # Optional: role scoped to department
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),  # User ID who assigned the role
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),  # Optional: role expiration
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('user_id', 'role_id', 'plant_id', 'department_id',
                           name='uq_user_role_scope'),
        sa.Index('idx_user_roles_user', 'user_id'),
        sa.Index('idx_user_roles_role', 'role_id'),
        sa.Index('idx_user_roles_org', 'organization_id'),
        sa.Index('idx_user_roles_active', 'user_id', 'is_active'),
    )

    # Create user_plant_access table (granular plant-level access control)
    op.create_table(
        'user_plant_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('access_level', sa.String(length=50), nullable=False),  # READ, WRITE, ADMIN
        sa.Column('can_create', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_read', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_update', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_delete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('user_id', 'plant_id', name='uq_user_plant_access'),
        sa.Index('idx_user_plant_access_user', 'user_id'),
        sa.Index('idx_user_plant_access_plant', 'plant_id'),
        sa.Index('idx_user_plant_access_org', 'organization_id'),
        sa.CheckConstraint(
            "access_level IN ('READ', 'WRITE', 'ADMIN')",
            name='chk_access_level_valid'
        ),
    )

    # Enable RLS on all three tables
    op.execute("ALTER TABLE roles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_plant_access ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY roles_org_isolation ON roles
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY user_roles_org_isolation ON user_roles
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY user_plant_access_org_isolation ON user_plant_access
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Insert default system roles
    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Super Admin',
            'SUPER_ADMIN',
            'Full system access with all permissions',
            true,
            '{"*": ["*"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Plant Manager',
            'PLANT_MANAGER',
            'Plant-level management with full operational control',
            true,
            '{"materials": ["create", "read", "update", "delete"], "work_orders": ["*"], "production": ["*"], "quality": ["*"], "machines": ["*"], "users": ["read"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Production Supervisor',
            'PRODUCTION_SUPERVISOR',
            'Production floor supervision and work order management',
            true,
            '{"work_orders": ["read", "update"], "production": ["create", "read", "update"], "quality": ["read", "create"], "machines": ["read"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Production Operator',
            'PRODUCTION_OPERATOR',
            'Production floor operator with data entry permissions',
            true,
            '{"work_orders": ["read"], "production": ["create", "read"], "machines": ["read"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Quality Inspector',
            'QUALITY_INSPECTOR',
            'Quality inspection and NCR management',
            true,
            '{"quality": ["create", "read", "update"], "ncr": ["create", "read", "update"], "inspections": ["*"], "work_orders": ["read"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Maintenance Technician',
            'MAINTENANCE_TECH',
            'Equipment maintenance and repair',
            true,
            '{"machines": ["read", "update"], "maintenance": ["*"], "work_orders": ["read"]}'::jsonb
        FROM organizations o
    """)

    op.execute("""
        INSERT INTO roles (organization_id, role_name, role_code, description, is_system_role, permissions)
        SELECT
            o.id,
            'Viewer',
            'VIEWER',
            'Read-only access to all modules',
            true,
            '{"*": ["read"]}'::jsonb
        FROM organizations o
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS roles_org_isolation ON roles")
    op.execute("DROP POLICY IF EXISTS user_roles_org_isolation ON user_roles")
    op.execute("DROP POLICY IF EXISTS user_plant_access_org_isolation ON user_plant_access")

    # Drop tables
    op.drop_table('user_plant_access')
    op.drop_table('user_roles')
    op.drop_table('roles')
