-- ============================================================================
-- SUBSCRIPTION SYSTEM - COMMON QUERIES & USAGE PATTERNS
-- ============================================================================
-- Reference queries for working with the subscription system
-- File: /home/user/mes/backend/database/schema/SUBSCRIPTION_QUERIES.sql
-- ============================================================================

-- ============================================================================
-- 1. SUBSCRIPTION STATUS & LIMITS
-- ============================================================================

-- Check subscription status and limits for an organization
SELECT
    s.tier,
    s.status,
    s.billing_cycle,
    s.trial_starts_at,
    s.trial_ends_at,
    s.trial_converted,
    s.max_users,
    s.max_plants,
    s.storage_limit_gb,
    s.current_period_start,
    s.current_period_end,
    CASE
        WHEN s.status = 'trial' THEN s.trial_ends_at - NOW()
        WHEN s.status = 'active' THEN s.current_period_end - NOW()
        ELSE NULL
    END AS time_remaining
FROM subscriptions s
WHERE s.organization_id = :org_id;


-- ============================================================================
-- 2. USAGE TRACKING & LIMIT ENFORCEMENT
-- ============================================================================

-- Get current usage vs limits
SELECT
    s.tier,
    s.status,
    -- Users
    s.max_users AS user_limit,
    u.current_users AS users_used,
    CASE
        WHEN s.max_users IS NULL THEN 'unlimited'
        ELSE ((u.current_users::FLOAT / s.max_users) * 100)::INTEGER || '%'
    END AS user_usage_pct,
    CASE
        WHEN s.max_users IS NULL THEN TRUE
        ELSE u.current_users < s.max_users
    END AS can_add_user,
    -- Plants
    s.max_plants AS plant_limit,
    u.current_plants AS plants_used,
    CASE
        WHEN s.max_plants IS NULL THEN 'unlimited'
        ELSE ((u.current_plants::FLOAT / s.max_plants) * 100)::INTEGER || '%'
    END AS plant_usage_pct,
    CASE
        WHEN s.max_plants IS NULL THEN TRUE
        ELSE u.current_plants < s.max_plants
    END AS can_add_plant,
    -- Storage
    s.storage_limit_gb AS storage_limit,
    u.storage_used_gb AS storage_used,
    CASE
        WHEN s.storage_limit_gb IS NULL THEN 'unlimited'
        ELSE ((u.storage_used_gb / s.storage_limit_gb) * 100)::INTEGER || '%'
    END AS storage_usage_pct,
    CASE
        WHEN s.storage_limit_gb IS NULL THEN TRUE
        ELSE u.storage_used_gb < s.storage_limit_gb
    END AS has_storage_available
FROM subscriptions s
LEFT JOIN LATERAL (
    SELECT *
    FROM subscription_usage
    WHERE organization_id = s.organization_id
    ORDER BY measured_at DESC
    LIMIT 1
) u ON TRUE
WHERE s.organization_id = :org_id;


-- ============================================================================
-- 3. ADD-ONS & TOTAL LIMITS
-- ============================================================================

-- Calculate total limits including active add-ons
SELECT
    s.tier,
    -- Base limits
    s.max_users AS base_user_limit,
    s.max_plants AS base_plant_limit,
    s.storage_limit_gb AS base_storage_limit,
    -- Add-ons
    COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_users' AND a.removed_at IS NULL
                      THEN a.quantity ELSE 0 END), 0) AS extra_users,
    COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_plants' AND a.removed_at IS NULL
                      THEN a.quantity ELSE 0 END), 0) AS extra_plants,
    COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_storage_gb' AND a.removed_at IS NULL
                      THEN a.quantity ELSE 0 END), 0) AS extra_storage,
    -- Total limits
    CASE
        WHEN s.max_users IS NULL THEN NULL
        ELSE s.max_users + COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_users' AND a.removed_at IS NULL
                                             THEN a.quantity ELSE 0 END), 0)
    END AS total_user_limit,
    CASE
        WHEN s.max_plants IS NULL THEN NULL
        ELSE s.max_plants + COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_plants' AND a.removed_at IS NULL
                                              THEN a.quantity ELSE 0 END), 0)
    END AS total_plant_limit,
    CASE
        WHEN s.storage_limit_gb IS NULL THEN NULL
        ELSE s.storage_limit_gb + COALESCE(SUM(CASE WHEN a.add_on_type = 'extra_storage_gb' AND a.removed_at IS NULL
                                                    THEN a.quantity ELSE 0 END), 0)
    END AS total_storage_limit
FROM subscriptions s
LEFT JOIN subscription_add_ons a ON a.subscription_id = s.id
WHERE s.organization_id = :org_id
GROUP BY s.id;


-- Active add-ons for a subscription
SELECT
    a.add_on_type,
    a.quantity,
    a.unit_price,
    (a.quantity * a.unit_price) AS total_monthly_cost,
    a.created_at,
    a.stripe_price_id
FROM subscription_add_ons a
INNER JOIN subscriptions s ON s.id = a.subscription_id
WHERE s.organization_id = :org_id
  AND a.removed_at IS NULL
ORDER BY a.add_on_type;


-- ============================================================================
-- 4. TRIAL MANAGEMENT
-- ============================================================================

-- Check if organization is in trial
SELECT
    s.trial_starts_at,
    s.trial_ends_at,
    s.trial_ends_at - NOW() AS time_remaining,
    s.trial_converted,
    CASE
        WHEN s.status = 'trial' AND s.trial_ends_at > NOW() THEN 'active_trial'
        WHEN s.status = 'trial' AND s.trial_ends_at <= NOW() THEN 'trial_expired'
        WHEN s.trial_converted THEN 'converted'
        ELSE 'no_trial'
    END AS trial_status
FROM subscriptions s
WHERE s.organization_id = :org_id;


-- Get all trials ending soon (next 7 days)
SELECT
    o.org_name,
    o.org_code,
    s.billing_email,
    s.trial_ends_at,
    s.trial_ends_at - NOW() AS time_remaining,
    DATE_PART('day', s.trial_ends_at - NOW()) AS days_remaining
FROM subscriptions s
INNER JOIN organizations o ON o.id = s.organization_id
WHERE s.status = 'trial'
  AND s.trial_ends_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
ORDER BY s.trial_ends_at ASC;


-- Convert trial to paid subscription
UPDATE subscriptions
SET
    status = 'active',
    trial_converted = TRUE,
    billing_cycle = :billing_cycle,  -- 'monthly' or 'annual'
    tier = :new_tier,                -- may upgrade during conversion
    stripe_customer_id = :stripe_customer_id,
    stripe_subscription_id = :stripe_subscription_id,
    current_period_start = NOW(),
    current_period_end = NOW() + INTERVAL '1 month',  -- or '1 year'
    updated_at = NOW()
WHERE organization_id = :org_id
  AND status = 'trial'
RETURNING *;


-- ============================================================================
-- 5. BILLING & INVOICES
-- ============================================================================

-- Get all invoices for an organization
SELECT
    i.invoice_number,
    i.invoice_date,
    i.due_date,
    i.amount_due / 100.0 AS amount_due_dollars,
    i.amount_paid / 100.0 AS amount_paid_dollars,
    (i.amount_due - i.amount_paid) / 100.0 AS balance_dollars,
    i.currency,
    i.status,
    i.paid_at,
    i.stripe_invoice_id,
    i.invoice_pdf_url
FROM invoices i
WHERE i.organization_id = :org_id
ORDER BY i.invoice_date DESC;


-- Outstanding (unpaid) invoices
SELECT
    i.invoice_number,
    i.due_date,
    (i.amount_due - i.amount_paid) / 100.0 AS balance_dollars,
    i.status,
    CASE
        WHEN i.due_date < NOW() THEN 'overdue'
        WHEN i.due_date BETWEEN NOW() AND NOW() + INTERVAL '7 days' THEN 'due_soon'
        ELSE 'current'
    END AS payment_urgency
FROM invoices i
WHERE i.organization_id = :org_id
  AND i.status IN ('open', 'past_due')
  AND (i.amount_due - i.amount_paid) > 0
ORDER BY i.due_date ASC;


-- Total revenue by organization (paid invoices)
SELECT
    o.org_name,
    o.org_code,
    COUNT(i.id) AS invoice_count,
    SUM(i.amount_paid) / 100.0 AS total_revenue_dollars,
    MIN(i.paid_at) AS first_payment_date,
    MAX(i.paid_at) AS last_payment_date
FROM organizations o
INNER JOIN invoices i ON i.organization_id = o.id
WHERE i.status = 'paid'
GROUP BY o.id
ORDER BY total_revenue_dollars DESC;


-- ============================================================================
-- 6. SUBSCRIPTION HEALTH CHECKS
-- ============================================================================

-- Find organizations at/over limits
SELECT
    o.org_name,
    o.org_code,
    s.tier,
    s.max_users,
    u.current_users,
    CASE
        WHEN s.max_users IS NOT NULL AND u.current_users >= s.max_users THEN 'AT_USER_LIMIT'
        WHEN s.max_plants IS NOT NULL AND u.current_plants >= s.max_plants THEN 'AT_PLANT_LIMIT'
        WHEN s.storage_limit_gb IS NOT NULL AND u.storage_used_gb >= s.storage_limit_gb THEN 'AT_STORAGE_LIMIT'
        ELSE 'OK'
    END AS limit_status
FROM organizations o
INNER JOIN subscriptions s ON s.organization_id = o.id
LEFT JOIN LATERAL (
    SELECT *
    FROM subscription_usage
    WHERE organization_id = o.id
    ORDER BY measured_at DESC
    LIMIT 1
) u ON TRUE
WHERE s.status = 'active'
  AND (
    (s.max_users IS NOT NULL AND u.current_users >= s.max_users) OR
    (s.max_plants IS NOT NULL AND u.current_plants >= s.max_plants) OR
    (s.storage_limit_gb IS NOT NULL AND u.storage_used_gb >= s.storage_limit_gb)
  );


-- Subscriptions with payment issues
SELECT
    o.org_name,
    o.org_code,
    s.status,
    s.billing_email,
    s.current_period_end,
    COUNT(i.id) AS unpaid_invoice_count,
    SUM(i.amount_due - i.amount_paid) / 100.0 AS total_outstanding_dollars
FROM organizations o
INNER JOIN subscriptions s ON s.organization_id = o.id
LEFT JOIN invoices i ON i.organization_id = o.id
    AND i.status IN ('open', 'past_due', 'uncollectible')
WHERE s.status IN ('past_due', 'suspended')
GROUP BY o.id, s.id
ORDER BY total_outstanding_dollars DESC;


-- ============================================================================
-- 7. ANALYTICS & REPORTING
-- ============================================================================

-- Subscription distribution by tier
SELECT
    s.tier,
    COUNT(*) AS subscriber_count,
    COUNT(*) FILTER (WHERE s.status = 'active') AS active_count,
    COUNT(*) FILTER (WHERE s.status = 'trial') AS trial_count,
    AVG(CASE
        WHEN s.status = 'trial' THEN
            EXTRACT(EPOCH FROM (NOW() - s.trial_starts_at)) / 86400
        ELSE NULL
    END)::INTEGER AS avg_trial_days_elapsed
FROM subscriptions s
GROUP BY s.tier
ORDER BY
    CASE s.tier
        WHEN 'starter' THEN 1
        WHEN 'professional' THEN 2
        WHEN 'enterprise' THEN 3
    END;


-- Trial conversion rate
SELECT
    COUNT(*) FILTER (WHERE trial_converted = TRUE) AS converted_count,
    COUNT(*) FILTER (WHERE trial_converted = FALSE AND status != 'trial') AS not_converted_count,
    COUNT(*) FILTER (WHERE status = 'trial') AS active_trial_count,
    ROUND(
        (COUNT(*) FILTER (WHERE trial_converted = TRUE)::FLOAT /
         NULLIF(COUNT(*) FILTER (WHERE status != 'trial'), 0)) * 100,
        2
    ) AS conversion_rate_pct
FROM subscriptions;


-- Monthly Recurring Revenue (MRR) estimate
-- Note: This is a simplified calculation. Actual MRR should come from Stripe
SELECT
    SUM(
        CASE s.tier
            WHEN 'starter' THEN 49.00       -- Example pricing
            WHEN 'professional' THEN 199.00
            WHEN 'enterprise' THEN 999.00
        END +
        COALESCE((
            SELECT SUM(a.quantity * a.unit_price) / 100.0
            FROM subscription_add_ons a
            WHERE a.subscription_id = s.id
              AND a.removed_at IS NULL
        ), 0)
    ) AS estimated_mrr
FROM subscriptions s
WHERE s.status = 'active'
  AND s.billing_cycle = 'monthly';


-- Usage trends over time (last 30 days)
SELECT
    DATE(u.measured_at) AS date,
    AVG(u.current_users) AS avg_users,
    AVG(u.current_plants) AS avg_plants,
    AVG(u.storage_used_gb) AS avg_storage_gb
FROM subscription_usage u
WHERE u.measured_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(u.measured_at)
ORDER BY date;


-- ============================================================================
-- 8. ONBOARDING TRACKING
-- ============================================================================

-- Organizations that completed onboarding
SELECT
    o.org_name,
    o.org_code,
    o.created_at AS organization_created,
    o.onboarding_completed_at,
    o.onboarding_completed_at - o.created_at AS time_to_complete_onboarding,
    s.status AS subscription_status,
    s.tier
FROM organizations o
INNER JOIN subscriptions s ON s.organization_id = o.id
WHERE o.onboarding_completed = TRUE
ORDER BY o.onboarding_completed_at DESC;


-- Organizations stuck in onboarding (created > 7 days ago, not completed)
SELECT
    o.org_name,
    o.org_code,
    o.created_at,
    NOW() - o.created_at AS days_since_signup,
    s.trial_ends_at,
    s.trial_ends_at - NOW() AS trial_time_remaining
FROM organizations o
INNER JOIN subscriptions s ON s.organization_id = o.id
WHERE o.onboarding_completed = FALSE
  AND o.created_at < NOW() - INTERVAL '7 days'
ORDER BY o.created_at ASC;


-- ============================================================================
-- 9. STRIPE SYNCHRONIZATION
-- ============================================================================

-- Find subscriptions missing Stripe IDs (need to sync)
SELECT
    o.org_name,
    o.org_code,
    s.status,
    s.tier,
    s.billing_email,
    s.stripe_customer_id IS NULL AS missing_customer_id,
    s.stripe_subscription_id IS NULL AS missing_subscription_id
FROM subscriptions s
INNER JOIN organizations o ON o.id = s.organization_id
WHERE s.status = 'active'
  AND (s.stripe_customer_id IS NULL OR s.stripe_subscription_id IS NULL);


-- ============================================================================
-- 10. ADMINISTRATIVE FUNCTIONS
-- ============================================================================

-- Suspend subscription (for payment issues)
UPDATE subscriptions
SET
    status = 'suspended',
    updated_at = NOW()
WHERE organization_id = :org_id
  AND status = 'active'
RETURNING *;


-- Cancel subscription
UPDATE subscriptions
SET
    status = 'cancelled',
    cancelled_at = NOW(),
    updated_at = NOW()
WHERE organization_id = :org_id
  AND status IN ('active', 'trial', 'past_due')
RETURNING *;


-- Upgrade/downgrade subscription tier
UPDATE subscriptions
SET
    tier = :new_tier,
    max_users = :new_max_users,
    max_plants = :new_max_plants,
    storage_limit_gb = :new_storage_limit_gb,
    updated_at = NOW()
WHERE organization_id = :org_id
RETURNING *;


-- Add a subscription add-on
INSERT INTO subscription_add_ons (
    subscription_id,
    add_on_type,
    quantity,
    unit_price,
    stripe_price_id
)
SELECT
    s.id,
    :add_on_type,        -- 'extra_users', 'extra_plants', 'extra_storage_gb'
    :quantity,
    :unit_price,         -- in cents
    :stripe_price_id
FROM subscriptions s
WHERE s.organization_id = :org_id
RETURNING *;


-- Remove a subscription add-on (soft delete)
UPDATE subscription_add_ons
SET removed_at = NOW()
WHERE id = :add_on_id
  AND removed_at IS NULL
RETURNING *;


-- Mark onboarding as completed
UPDATE organizations
SET
    onboarding_completed = TRUE,
    onboarding_completed_at = NOW()
WHERE id = :org_id
  AND onboarding_completed = FALSE
RETURNING *;


-- ============================================================================
-- 11. BULK OPERATIONS (Admin/Support)
-- ============================================================================

-- Extend trial for specific organizations (e.g., additional 7 days)
UPDATE subscriptions
SET
    trial_ends_at = trial_ends_at + INTERVAL '7 days',
    updated_at = NOW()
WHERE organization_id = :org_id
  AND status = 'trial'
RETURNING org_name, trial_ends_at;


-- Find all organizations that need usage calculation
SELECT DISTINCT s.organization_id
FROM subscriptions s
WHERE s.status IN ('active', 'trial')
  AND NOT EXISTS (
    SELECT 1
    FROM subscription_usage u
    WHERE u.organization_id = s.organization_id
      AND u.measured_at > NOW() - INTERVAL '6 hours'
  );
