"""Create Currency and ExchangeRate tables for multi-currency costing

Revision ID: 004_create_currency_tables
Revises: 003_material_search_idx
Create Date: 2025-11-08 14:00:00.000000

Creates currency and exchange_rate tables to support multi-currency costing:
- Currency table: Stores supported currencies with rounding rules
- ExchangeRate table: Historical exchange rates with audit trail
- Foreign keys to currency in costing tables
- Seed common currencies (USD, EUR, GBP, INR, JPY, CNY)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '004_create_currency_tables'
down_revision = '003_material_search_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create currency and exchange_rate tables.

    Tables created:
    1. currency - Supported currencies with metadata
    2. exchange_rate - Historical exchange rates
    3. Add currency_code columns to existing costing tables
    """
    print("\n💱 Creating Multi-Currency Costing tables...")

    # Create currency table
    print("  Creating currency table...")
    op.create_table(
        'currency',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('decimal_places', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_currency_code'),
        sa.CheckConstraint('decimal_places >= 0', name='chk_decimal_places_non_negative'),
        sa.CheckConstraint('decimal_places <= 6', name='chk_decimal_places_max')
    )
    op.create_index('idx_currency_code', 'currency', ['code'], unique=False)
    print("    ✓ Currency table created")

    # Create exchange_rate table
    print("  Creating exchange_rate table...")
    op.create_table(
        'exchange_rate',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_currency_code', sa.String(length=3), nullable=False),
        sa.Column('to_currency_code', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['from_currency_code'], ['currency.code'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_currency_code'], ['currency.code'], ondelete='CASCADE'),
        sa.CheckConstraint('rate > 0', name='chk_rate_positive'),
        sa.CheckConstraint('from_currency_code != to_currency_code', name='chk_different_currencies')
    )
    op.create_index('idx_exchange_rate_currencies', 'exchange_rate', ['from_currency_code', 'to_currency_code'], unique=False)
    op.create_index('idx_exchange_rate_effective_date', 'exchange_rate', ['effective_date'], unique=False)
    op.create_index('idx_exchange_rate_lookup', 'exchange_rate', ['from_currency_code', 'to_currency_code', 'effective_date'], unique=False)
    print("    ✓ Exchange rate table created")

    # Seed common currencies
    print("  Seeding common currencies...")
    conn = op.get_bind()

    currencies = [
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'decimal_places': 2},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'decimal_places': 2},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'decimal_places': 2},
        {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹', 'decimal_places': 2},
        {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥', 'decimal_places': 0},
        {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥', 'decimal_places': 2},
        {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$', 'decimal_places': 2},
        {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$', 'decimal_places': 2},
        {'code': 'CHF', 'name': 'Swiss Franc', 'symbol': 'CHF', 'decimal_places': 2},
        {'code': 'SGD', 'name': 'Singapore Dollar', 'symbol': 'S$', 'decimal_places': 2},
    ]

    for currency in currencies:
        conn.execute(text("""
            INSERT INTO currency (code, name, symbol, decimal_places)
            VALUES (:code, :name, :symbol, :decimal_places)
        """), currency)

    conn.commit()
    print(f"    ✓ Seeded {len(currencies)} currencies")

    # Add currency_code column to material_costing table
    print("  Adding currency support to material_costing table...")
    op.add_column('material_costing', sa.Column('currency_code', sa.String(length=3), nullable=True))
    op.create_foreign_key('fk_material_costing_currency', 'material_costing', 'currency', ['currency_code'], ['code'])
    op.create_index('idx_material_costing_currency', 'material_costing', ['currency_code'], unique=False)

    # Set default currency to USD for existing records
    conn.execute(text("""
        UPDATE material_costing SET currency_code = 'USD' WHERE currency_code IS NULL
    """))
    conn.commit()

    # Make currency_code NOT NULL after setting defaults
    op.alter_column('material_costing', 'currency_code', nullable=False)
    print("    ✓ Added currency_code to material_costing")

    # Add currency_code column to cost_layer table
    print("  Adding currency support to cost_layer table...")
    op.add_column('cost_layer', sa.Column('currency_code', sa.String(length=3), nullable=True))
    op.create_foreign_key('fk_cost_layer_currency', 'cost_layer', 'currency', ['currency_code'], ['code'])
    op.create_index('idx_cost_layer_currency', 'cost_layer', ['currency_code'], unique=False)

    # Set default currency to USD for existing records
    conn.execute(text("""
        UPDATE cost_layer SET currency_code = 'USD' WHERE currency_code IS NULL
    """))
    conn.commit()

    # Make currency_code NOT NULL after setting defaults
    op.alter_column('cost_layer', 'currency_code', nullable=False)
    print("    ✓ Added currency_code to cost_layer")

    print("\n✅ Multi-currency costing tables created successfully!")
    print("   Supported currencies: USD, EUR, GBP, INR, JPY, CNY, AUD, CAD, CHF, SGD")


def downgrade() -> None:
    """
    Drop currency and exchange_rate tables.

    Removes multi-currency support from costing tables.
    """
    print("\n⚠️  Removing multi-currency costing tables...")

    # Remove currency_code from cost_layer
    print("  Removing currency support from cost_layer...")
    op.drop_index('idx_cost_layer_currency', table_name='cost_layer')
    op.drop_constraint('fk_cost_layer_currency', 'cost_layer', type_='foreignkey')
    op.drop_column('cost_layer', 'currency_code')
    print("    ✓ Removed currency_code from cost_layer")

    # Remove currency_code from material_costing
    print("  Removing currency support from material_costing...")
    op.drop_index('idx_material_costing_currency', table_name='material_costing')
    op.drop_constraint('fk_material_costing_currency', 'material_costing', type_='foreignkey')
    op.drop_column('material_costing', 'currency_code')
    print("    ✓ Removed currency_code from material_costing")

    # Drop exchange_rate table
    print("  Dropping exchange_rate table...")
    op.drop_index('idx_exchange_rate_lookup', table_name='exchange_rate')
    op.drop_index('idx_exchange_rate_effective_date', table_name='exchange_rate')
    op.drop_index('idx_exchange_rate_currencies', table_name='exchange_rate')
    op.drop_table('exchange_rate')
    print("    ✓ Exchange rate table dropped")

    # Drop currency table
    print("  Dropping currency table...")
    op.drop_index('idx_currency_code', table_name='currency')
    op.drop_table('currency')
    print("    ✓ Currency table dropped")

    print("\n✅ Multi-currency costing tables removed")
