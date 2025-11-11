# Subscription System Database Schema

## Overview

Comprehensive B2B SaaS subscription system for Unison Manufacturing ERP with 3-tier pricing (Starter, Professional, Enterprise), trial management, usage tracking, and Stripe integration.

**Migration File**: `/home/user/mes/backend/migrations/versions/017_add_subscription_tables.py`

## Tables Created

### 1. subscriptions

Core subscription management with Stripe integration and tier-based limits.

**Columns**:
- `id` - Primary key
- `organization_id` - FK to organizations (UNIQUE, one subscription per org)
- `tier` - VARCHAR(50), CHECK: 'starter' | 'professional' | 'enterprise'
- `status` - VARCHAR(50), CHECK: 'trial' | 'active' | 'cancelled' | 'past_due' | 'suspended'
- `billing_cycle` - VARCHAR(20), CHECK: 'monthly' | 'annual' (nullable during trial)

**Trial Management**:
- `trial_starts_at` - TIMESTAMP WITH TIME ZONE
- `trial_ends_at` - TIMESTAMP WITH TIME ZONE
- `trial_converted` - BOOLEAN (default: false)

**Stripe Integration**:
- `stripe_customer_id` - VARCHAR(255) UNIQUE
- `stripe_subscription_id` - VARCHAR(255) UNIQUE

**Billing**:
- `current_period_start` - TIMESTAMP WITH TIME ZONE
- `current_period_end` - TIMESTAMP WITH TIME ZONE
- `billing_email` - VARCHAR(255)

**Resource Limits** (NULL = unlimited for Enterprise):
- `max_users` - INTEGER
- `max_plants` - INTEGER
- `storage_limit_gb` - INTEGER

**Timestamps**:
- `created_at` - Auto-set on creation
- `updated_at` - Auto-updated by trigger
- `cancelled_at` - Set when subscription cancelled

**Indexes**:
- idx_subscriptions_org_id (organization_id)
- idx_subscriptions_stripe_customer (stripe_customer_id)
- idx_subscriptions_status (status)
- idx_subscriptions_trial_ends (trial_ends_at)
- idx_subscriptions_tier (tier)

**Row-Level Security**: Isolated by organization_id

---

### 2. subscription_usage

Tracks current resource usage vs subscription limits.

**Columns**:
- `id` - Primary key
- `organization_id` - FK to organizations
- `current_users` - INTEGER (default: 0)
- `current_plants` - INTEGER (default: 0)
- `storage_used_gb` - NUMERIC(10, 2) (default: 0.00)
- `measured_at` - TIMESTAMP WITH TIME ZONE (default: NOW())

**Indexes**:
- idx_subscription_usage_org_id (organization_id)
- idx_subscription_usage_measured_at (measured_at)

**Row-Level Security**: Isolated by organization_id

**Usage**:
- Updated periodically (e.g., via pg_cron job)
- Compare against subscriptions.max_* limits
- Historical tracking for analytics

---

### 3. invoices

Billing history and payment tracking with Stripe integration.

**Columns**:
- `id` - Primary key
- `organization_id` - FK to organizations
- `subscription_id` - FK to subscriptions

**Stripe Integration**:
- `stripe_invoice_id` - VARCHAR(255) UNIQUE
- `stripe_payment_intent_id` - VARCHAR(255)

**Invoice Details**:
- `invoice_number` - VARCHAR(100) UNIQUE
- `amount_due` - INTEGER (in cents)
- `amount_paid` - INTEGER (in cents, default: 0)
- `currency` - VARCHAR(3) (default: 'USD')

**Status**:
- `status` - VARCHAR(50), CHECK: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible'

**Dates**:
- `invoice_date` - TIMESTAMP WITH TIME ZONE (required)
- `due_date` - TIMESTAMP WITH TIME ZONE
- `paid_at` - TIMESTAMP WITH TIME ZONE

**PDF**:
- `invoice_pdf_url` - TEXT

**Timestamps**:
- `created_at` - Auto-set
- `updated_at` - Auto-updated by trigger

**Indexes**:
- idx_invoices_org_id (organization_id)
- idx_invoices_subscription_id (subscription_id)
- idx_invoices_stripe_id (stripe_invoice_id)
- idx_invoices_status (status)
- idx_invoices_due_date (due_date)
- idx_invoices_invoice_date (invoice_date)

**Row-Level Security**: Isolated by organization_id

---

### 4. subscription_add_ons

Additional purchased capacity (users, plants, storage).

**Columns**:
- `id` - Primary key
- `subscription_id` - FK to subscriptions

**Add-on Details**:
- `add_on_type` - VARCHAR(50), CHECK: 'extra_users' | 'extra_plants' | 'extra_storage_gb'
- `quantity` - INTEGER (how many additional units)
- `unit_price` - INTEGER (in cents per unit)

**Stripe Integration**:
- `stripe_price_id` - VARCHAR(255)

**Timestamps**:
- `created_at` - When add-on was added
- `removed_at` - When add-on was removed (nullable = active)

**Indexes**:
- idx_add_ons_subscription_id (subscription_id)
- idx_add_ons_type (add_on_type)
- idx_add_ons_active (subscription_id, removed_at) - for active add-ons

**Row-Level Security**: Isolated via subscription's organization_id

**Usage**:
- Add extra capacity beyond base tier limits
- Billed per unit (e.g., $5/extra user/month)
- Calculate total limits: base + SUM(active add-ons)

---

## Organizations Table Updates

Added columns to existing `organizations` table:

- `onboarding_completed` - BOOLEAN (default: false)
- `onboarding_completed_at` - TIMESTAMP WITH TIME ZONE

**Index**: idx_organizations_onboarding (onboarding_completed)

---

## Triggers & Automation

### 1. Auto-update Timestamps

**Trigger Function**: `update_subscription_updated_at()`

**Applied To**:
- subscriptions.updated_at (on UPDATE)
- invoices.updated_at (on UPDATE)

### 2. Auto-create Trial Subscription

**Trigger Function**: `create_default_trial_subscription()`

**Fires**: AFTER INSERT ON organizations

**Behavior**:
- Creates trial subscription (14-day trial)
- Default tier: 'starter'
- Default limits: 3 users, 1 plant, 10GB storage
- Creates initial subscription_usage record (all zeros)

**Business Rules**:
- Every new organization automatically gets a 14-day trial
- Status: 'trial'
- No billing_cycle during trial
- trial_converted defaults to false

---

## Pricing Tiers (Suggested Limits)

### Starter
- max_users: 3
- max_plants: 1
- storage_limit_gb: 10

### Professional
- max_users: 25
- max_plants: 5
- storage_limit_gb: 100

### Enterprise
- max_users: NULL (unlimited)
- max_plants: NULL (unlimited)
- storage_limit_gb: NULL (unlimited)

---

## Row-Level Security (RLS)

All subscription tables have RLS enabled with organization isolation:

```sql
-- Policy pattern applied to all tables
USING (
    organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
)
```

**subscription_add_ons** uses indirect isolation via subscription:
```sql
USING (
    subscription_id IN (
        SELECT id FROM subscriptions
        WHERE organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
    )
)
```

---

## Usage Examples

### Check Subscription Status

```sql
SELECT
    s.tier,
    s.status,
    s.trial_ends_at,
    s.max_users,
    u.current_users,
    (s.max_users IS NULL OR u.current_users <= s.max_users) AS within_user_limit
FROM subscriptions s
LEFT JOIN subscription_usage u ON u.organization_id = s.organization_id
WHERE s.organization_id = 123;
```

### Calculate Total Limits (Base + Add-ons)

```sql
SELECT
    s.tier,
    s.max_users AS base_users,
    COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_users' AND a.removed_at IS NULL
                      THEN a.quantity ELSE 0 END), 0) AS extra_users,
    s.max_users + COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_users' AND a.removed_at IS NULL
                                    THEN a.quantity ELSE 0 END), 0) AS total_user_limit
FROM subscriptions s
LEFT JOIN subscription_add_ons a ON a.subscription_id = s.id
WHERE s.organization_id = 123
GROUP BY s.id;
```

### Get Unpaid Invoices

```sql
SELECT
    i.invoice_number,
    i.amount_due,
    i.amount_paid,
    i.due_date,
    (i.amount_due - i.amount_paid) AS balance
FROM invoices i
WHERE i.organization_id = 123
  AND i.status IN ('open', 'past_due')
ORDER BY i.due_date ASC;
```

---

## Migration Commands

### Apply Migration

```bash
cd /home/user/mes/backend
alembic upgrade head
```

### Rollback Migration

```bash
cd /home/user/mes/backend
alembic downgrade -1
```

### Check Current Version

```bash
cd /home/user/mes/backend
alembic current
```

---

## Integration Notes

### Stripe Webhooks

Handle these events to keep data in sync:

- `customer.subscription.created` - Update subscriptions table
- `customer.subscription.updated` - Update status, period dates
- `customer.subscription.deleted` - Set status to 'cancelled'
- `invoice.payment_succeeded` - Update invoice status to 'paid'
- `invoice.payment_failed` - Update invoice status, subscription to 'past_due'

### Usage Tracking

Recommended pg_cron job (every 6 hours):

```sql
-- Update subscription_usage
INSERT INTO subscription_usage (organization_id, current_users, current_plants, storage_used_gb)
SELECT
    o.id AS organization_id,
    COUNT(DISTINCT u.id) AS current_users,
    COUNT(DISTINCT p.id) AS current_plants,
    COALESCE(SUM(f.file_size_bytes) / 1073741824.0, 0) AS storage_used_gb
FROM organizations o
LEFT JOIN users u ON u.organization_id = o.id AND u.is_active = true
LEFT JOIN plants p ON p.organization_id = o.id AND p.is_active = true
LEFT JOIN file_uploads f ON f.organization_id = o.id
GROUP BY o.id;
```

### Limit Enforcement

Before creating resources, check limits:

```python
# Example: Check user limit before creating new user
def can_add_user(org_id: int) -> bool:
    subscription = get_subscription(org_id)
    usage = get_latest_usage(org_id)

    # Enterprise (NULL) = unlimited
    if subscription.max_users is None:
        return True

    # Calculate total limit including add-ons
    total_limit = subscription.max_users
    active_add_ons = get_active_user_add_ons(subscription.id)
    total_limit += sum(a.quantity for a in active_add_ons)

    return usage.current_users < total_limit
```

---

## Database Schema Diagram

```
organizations (1) ←─────── (1) subscriptions
                                    │
                                    ├─→ (n) invoices
                                    │
                                    └─→ (n) subscription_add_ons

organizations (1) ←─────── (n) subscription_usage
```

---

## Constraints Summary

### Check Constraints
- subscriptions.tier IN ('starter', 'professional', 'enterprise')
- subscriptions.status IN ('trial', 'active', 'cancelled', 'past_due', 'suspended')
- subscriptions.billing_cycle IN ('monthly', 'annual') OR NULL
- invoices.status IN ('draft', 'open', 'paid', 'void', 'uncollectible')
- subscription_add_ons.add_on_type IN ('extra_users', 'extra_plants', 'extra_storage_gb')

### Unique Constraints
- subscriptions.organization_id (one subscription per org)
- subscriptions.stripe_customer_id
- subscriptions.stripe_subscription_id
- invoices.stripe_invoice_id
- invoices.invoice_number

### Foreign Keys
- All tables have CASCADE delete on organization_id
- invoices → subscriptions (CASCADE)
- subscription_add_ons → subscriptions (CASCADE)
- subscription_usage → organizations (CASCADE)

---

## Next Steps

1. **Create SQLAlchemy Models**: Mirror these tables in `/home/user/mes/backend/app/models/`
2. **Create Repository Layer**: Subscription operations in `/home/user/mes/backend/app/infrastructure/repositories/`
3. **Create Service Layer**: Business logic in `/home/user/mes/backend/app/application/services/`
4. **Implement Stripe Integration**: Webhook handlers and payment processing
5. **Create API Endpoints**: RESTful API for subscription management
6. **Add Usage Tracking Job**: pg_cron job to update subscription_usage
7. **Implement Limit Checks**: Middleware/decorators to enforce subscription limits
8. **Create Admin Dashboard**: UI for subscription management

---

**Created**: 2025-11-11
**Migration ID**: 017_add_subscription_tables
**Revises**: 007_inventory_alerts
