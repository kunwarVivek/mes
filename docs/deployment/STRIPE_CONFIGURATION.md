# Stripe Configuration & Deployment Guide

**Version**: 1.0
**Last Updated**: 2025-11-11
**Purpose**: Step-by-step guide to configure Stripe for production billing

---

## Prerequisites

- ✅ Subscription system backend complete (database, API, services)
- ✅ Stripe account created (test + live modes)
- ✅ Domain configured with HTTPS
- ✅ Backend deployed and accessible

---

## Step 1: Create Stripe Account

### 1.1 Sign Up

1. Go to https://dashboard.stripe.com/register
2. Fill in business details:
   - Business name: Unison Manufacturing ERP
   - Country: [Your country]
   - Business type: Software as a Service (SaaS)
3. Verify email address
4. Complete identity verification (required for payouts)

### 1.2 Activate Account

Complete Stripe's onboarding checklist:
- ✅ Verify business information
- ✅ Add bank account (for payouts)
- ✅ Set up tax information
- ✅ Configure branding (logo, colors)

---

## Step 2: Create Products & Prices

### 2.1 Create Products

**In Stripe Dashboard**: Products → Create Product

#### Product 1: Starter Plan
```
Name: Starter Plan
Description: For small manufacturers (1 plant, 3 users, 10GB storage)
Statement descriptor: UNISON STARTER
```

#### Product 2: Professional Plan
```
Name: Professional Plan
Description: For growing manufacturers (5 plants, 25 users, 100GB storage)
Statement descriptor: UNISON PRO
```

#### Product 3: Enterprise Plan
```
Name: Enterprise Plan
Description: For large manufacturers (unlimited resources, white-labeling, SSO)
Statement descriptor: UNISON ENT
```

### 2.2 Create Prices

For **each product**, create 2 recurring prices:

#### Starter - Monthly
```
Amount: $49
Billing period: Monthly
Recurring: Yes
Price ID: (copy this - example: price_1AbCdEfGhIjKlMnO)
```

#### Starter - Annual
```
Amount: $529 ($49 × 12 × 0.9 = 10% discount)
Billing period: Yearly
Recurring: Yes
Price ID: (copy this - example: price_2AbCdEfGhIjKlMnO)
```

**Repeat for Professional ($199/mo, $2,149/yr) and Enterprise ($999/mo, $10,789/yr)**

### 2.3 Create Add-On Products

#### Extra Users
```
Name: Extra Users
Description: Additional users beyond plan limit
Price: $5/user/month
Billing period: Monthly
Price ID: (copy this)
```

#### Extra Plants
```
Name: Extra Plants
Description: Additional plants beyond plan limit
Price: $25/plant/month
Billing period: Monthly
Price ID: (copy this)
```

#### Extra Storage
```
Name: Extra Storage
Description: Additional storage per GB
Price: $0.50/GB/month
Billing period: Monthly
Price ID: (copy this)
```

---

## Step 3: Configure Webhooks

### 3.1 Create Webhook Endpoint

**In Stripe Dashboard**: Developers → Webhooks → Add endpoint

```
Endpoint URL: https://api.unison-mes.com/api/v1/webhooks/stripe
Description: Unison MES Production Webhook
```

### 3.2 Select Events

Enable these events:

**Checkout**:
- ✅ `checkout.session.completed`
- ✅ `checkout.session.expired`

**Customer**:
- ✅ `customer.created`
- ✅ `customer.updated`
- ✅ `customer.deleted`

**Subscription**:
- ✅ `customer.subscription.created`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`
- ✅ `customer.subscription.trial_will_end` (3 days before)

**Invoice**:
- ✅ `invoice.created`
- ✅ `invoice.finalized`
- ✅ `invoice.paid`
- ✅ `invoice.payment_failed`

**Payment**:
- ✅ `payment_intent.succeeded`
- ✅ `payment_intent.payment_failed`

### 3.3 Copy Webhook Secret

After creating, copy the **Signing secret** (starts with `whsec_`):
```
whsec_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

---

## Step 4: Update Backend Configuration

### 4.1 Environment Variables

Add to `.env` or environment configuration:

```bash
# Stripe API Keys (replace with your actual keys from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_live_YOUR_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Product Price IDs
STRIPE_PRICE_STARTER_MONTHLY=price_1AbCdEfGhIjKlMnO
STRIPE_PRICE_STARTER_ANNUAL=price_2AbCdEfGhIjKlMnO
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_3AbCdEfGhIjKlMnO
STRIPE_PRICE_PROFESSIONAL_ANNUAL=price_4AbCdEfGhIjKlMnO
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_5AbCdEfGhIjKlMnO
STRIPE_PRICE_ENTERPRISE_ANNUAL=price_6AbCdEfGhIjKlMnO

# Add-on Price IDs
STRIPE_PRICE_EXTRA_USERS=price_7AbCdEfGhIjKlMnO
STRIPE_PRICE_EXTRA_PLANTS=price_8AbCdEfGhIjKlMnO
STRIPE_PRICE_EXTRA_STORAGE=price_9AbCdEfGhIjKlMnO
```

### 4.2 Update `pricing.py`

Update `/backend/app/config/pricing.py` with actual Stripe Price IDs:

```python
import os

STRIPE_PRICES = {
    SubscriptionTier.STARTER: {
        BillingCycle.MONTHLY: os.getenv("STRIPE_PRICE_STARTER_MONTHLY"),
        BillingCycle.ANNUAL: os.getenv("STRIPE_PRICE_STARTER_ANNUAL"),
    },
    SubscriptionTier.PROFESSIONAL: {
        BillingCycle.MONTHLY: os.getenv("STRIPE_PRICE_PROFESSIONAL_MONTHLY"),
        BillingCycle.ANNUAL: os.getenv("STRIPE_PRICE_PROFESSIONAL_ANNUAL"),
    },
    SubscriptionTier.ENTERPRISE: {
        BillingCycle.MONTHLY: os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY"),
        BillingCycle.ANNUAL: os.getenv("STRIPE_PRICE_ENTERPRISE_ANNUAL"),
    },
}
```

### 4.3 Deploy Configuration

```bash
# Restart backend to load new environment variables
docker-compose restart backend

# Or if using Kubernetes
kubectl rollout restart deployment/backend
```

---

## Step 5: Test Integration

### 5.1 Test Mode First

**Before going live**, test with Stripe Test Mode:

1. Use test API keys (start with `sk_test_` and `pk_test_`)
2. Use test webhook endpoint: `https://staging.unison-mes.com/api/v1/webhooks/stripe`
3. Test with [Stripe test cards](https://stripe.com/docs/testing):
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Requires auth: `4000 0027 6000 3184`

### 5.2 Test Checkout Flow

```bash
# 1. Create checkout session
curl -X POST https://staging.unison-mes.com/api/v1/billing/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "professional",
    "billing_cycle": "monthly",
    "success_url": "https://app.unison-mes.com/billing/success",
    "cancel_url": "https://app.unison-mes.com/billing"
  }'

# 2. Visit checkout_url from response
# 3. Complete payment with test card
# 4. Verify webhook received
```

### 5.3 Verify Webhooks

```bash
# Check webhook logs in Stripe Dashboard
# Developers → Webhooks → [Your endpoint] → Logs

# Check backend logs
docker logs backend | grep "stripe_webhook"
```

### 5.4 Test Subscription Lifecycle

1. **Create trial** → Verify 14-day trial created
2. **Convert to paid** → Complete checkout, verify status = `active`
3. **Payment fails** → Use decline card, verify status = `past_due`
4. **Cancel subscription** → Verify status = `cancelled` at period end
5. **Reactivate** → Verify can reactivate before period end

---

## Step 6: Go Live

### 6.1 Switch to Live Mode

1. In Stripe Dashboard, toggle to **Live mode**
2. Copy **live API keys** (start with `sk_live_` and `pk_live_`)
3. Update webhook endpoint to production URL
4. Update environment variables with live keys

### 6.2 Production Checklist

Before going live:

- [ ] Test mode fully tested (all flows working)
- [ ] Webhook signature verification enabled
- [ ] HTTPS configured on all endpoints
- [ ] Error monitoring configured (Sentry/DataDog)
- [ ] Payment failure alerts set up
- [ ] Customer support contact added to Stripe
- [ ] Tax configuration completed (if applicable)
- [ ] Terms of Service and Privacy Policy published
- [ ] Refund policy documented
- [ ] Data retention policy configured

### 6.3 Monitor First Transactions

**Watch closely for first 24-48 hours**:

```sql
-- Check subscription creations
SELECT * FROM subscriptions
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Check webhook events
SELECT * FROM stripe_webhook_events
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Check for errors
SELECT * FROM scheduled_job_logs
WHERE status = 'failure'
  AND executed_at > NOW() - INTERVAL '24 hours';
```

---

## Step 7: Monitoring & Alerts

### 7.1 Stripe Dashboard Alerts

Configure alerts in Stripe Dashboard → Settings → Email notifications:

- ✅ Failed payments (immediate)
- ✅ Disputed charges
- ✅ Unusual activity
- ✅ Large charges (>$1000)

### 7.2 Application Monitoring

Set up alerts for:

1. **Webhook failures**: >5% failure rate
2. **Checkout abandonment**: >70% abandonment
3. **Payment decline rate**: >10% decline rate
4. **Trial conversion rate**: <20% conversion (investigate)

### 7.3 Financial Metrics

Track daily:

```sql
-- Daily MRR
SELECT
  DATE(created_at) as date,
  SUM(CASE
    WHEN billing_cycle = 'monthly' THEN
      CASE tier
        WHEN 'starter' THEN 4900
        WHEN 'professional' THEN 19900
        WHEN 'enterprise' THEN 99900
      END
    ELSE 0
  END) / 100.0 as daily_mrr
FROM subscriptions
WHERE status = 'active'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;

-- Churn rate
SELECT
  COUNT(*) FILTER (WHERE status = 'cancelled') * 100.0 /
  COUNT(*) as churn_rate
FROM subscriptions
WHERE created_at > NOW() - INTERVAL '30 days';
```

---

## Step 8: Customer Billing Portal

### 8.1 Enable Customer Portal

In Stripe Dashboard → Settings → Billing:

**Customer portal settings**:
- ✅ Allow customers to update payment method
- ✅ Allow customers to update billing email
- ✅ Allow customers to view invoices
- ✅ Allow customers to view billing history
- ❌ Disable subscription cancellation (use app UI)
- ❌ Disable subscription upgrades/downgrades (use app UI)

### 8.2 Configure Portal Link

```python
# Backend generates portal link
from app.infrastructure.adapters.stripe import stripe_client

portal_session = stripe_client.create_billing_portal_session(
    customer_id=subscription.stripe_customer_id,
    return_url="https://app.unison-mes.com/billing"
)

return {"url": portal_session.url}
```

---

## Troubleshooting

### Webhook Not Receiving Events

**Check**:
1. Endpoint URL is publicly accessible (test with curl)
2. HTTPS certificate valid
3. Webhook secret matches environment variable
4. Backend logs for errors: `docker logs backend | grep webhook`

**Test webhook manually**:
```bash
# In Stripe Dashboard → Webhooks → Send test webhook
```

### Payments Failing

**Common causes**:
1. Invalid Price ID (check STRIPE_PRICE_* environment variables)
2. Stripe account not activated
3. Payment method declined (customer issue)
4. 3D Secure required but not handled

### Subscription Not Activating

**Check**:
1. Webhook `checkout.session.completed` received
2. Database subscription status updated
3. Trial converted flag set to `true`
4. Stripe subscription ID stored

---

## Security Best Practices

### API Key Management

**DO**:
- ✅ Store keys in environment variables (never commit to git)
- ✅ Use different keys for staging and production
- ✅ Rotate keys quarterly
- ✅ Restrict key permissions (use restricted keys where possible)

**DON'T**:
- ❌ Hardcode keys in source code
- ❌ Share keys via email or Slack
- ❌ Use production keys in development
- ❌ Commit `.env` files to version control

### Webhook Security

**Always**:
- ✅ Verify webhook signature before processing
- ✅ Use HTTPS for webhook endpoint
- ✅ Implement idempotency (same event received multiple times)
- ✅ Return 200 OK quickly (process async if needed)

### PCI Compliance

Stripe handles PCI compliance, but you must:
- ✅ Never store raw card numbers
- ✅ Use Stripe.js for card collection (frontend)
- ✅ Use Stripe tokens for server-side processing
- ✅ Log payment attempts (not card details)

---

## Cost Optimization

### Transaction Fees

Stripe fees (US):
- **2.9% + $0.30** per successful card charge
- **0.5%** additional for international cards
- **$15** per chargeback (if you lose)

**Estimated costs for 100 customers** ($199/mo Professional):
- Revenue: $19,900/month
- Stripe fees: ~$618/month (2.9% + $30)
- Net revenue: ~$19,282/month

### Reduce Fees

1. **Annual billing**: Fewer transactions = lower fixed fees ($0.30)
2. **ACH/bank transfers**: 0.8% (max $5) instead of 2.9% + $0.30
3. **Volume pricing**: Contact Stripe for discounts at >$1M/year

---

## Next Steps After Setup

1. **Create runbook** for common payment issues
2. **Train support team** on refund process
3. **Set up revenue recognition** (accounting)
4. **Configure tax collection** (Stripe Tax or TaxJar)
5. **Implement dunning** (retry failed payments automatically)
6. **Add usage-based billing** (metered pricing)

---

## Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Webhook Guide](https://stripe.com/docs/webhooks)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Security](https://stripe.com/docs/security)
- [PCI Compliance](https://stripe.com/docs/security/guide)

---

## Support Contacts

**Stripe Support**: support@stripe.com
**Emergency**: +1 (888) 926-2289
**Status Page**: https://status.stripe.com

**Unison MES Support**: support@unison-mes.com
