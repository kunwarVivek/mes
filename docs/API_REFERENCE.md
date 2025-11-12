# Unison Manufacturing ERP - API Reference

**Complete REST API Documentation**

*Version 1.0 | Last Updated: 2025-11-11*

**Base URL**: `https://api.yourdomain.com` (Production) or `http://localhost:8000` (Development)

**API Docs**: `/docs` (Swagger UI) or `/redoc` (ReDoc)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Subscriptions & Billing](#subscriptions--billing)
3. [Platform Admin](#platform-admin)
4. [Analytics](#analytics)
5. [Materials](#materials)
6. [Work Orders](#work-orders)
7. [Quality (NCR)](#quality-ncr)
8. [Inventory](#inventory)
9. [Webhooks](#webhooks)
10. [Internal Jobs API](#internal-jobs-api)
11. [Health Checks](#health-checks)

---

## Authentication

All API requests (except public endpoints) require authentication using **JWT Bearer tokens**.

### POST /api/v1/auth/register

Register a new user and organization.

**Request Body**:
```json
{
  "email": "user@company.com",
  "password": "SecurePassword123",
  "full_name": "John Doe",
  "organization_name": "Acme Manufacturing",
  "organization_code": "ACME"
}
```

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "admin",
    "is_platform_admin": false
  },
  "organization": {
    "id": 1,
    "name": "Acme Manufacturing",
    "code": "ACME"
  },
  "subscription": {
    "id": 1,
    "tier": "starter",
    "status": "trial",
    "trial_ends_at": "2025-11-25T00:00:00Z"
  }
}
```

**What Happens**:
- New organization created
- User created as organization admin
- 14-day trial subscription auto-created
- Default plant created
- Welcome email sent

---

### POST /api/v1/auth/login

Authenticate user and get access token.

**Request Body**:
```json
{
  "email": "user@company.com",
  "password": "SecurePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Access Token**: Valid for 30 minutes
**Refresh Token**: Valid for 7 days

---

### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### GET /api/v1/auth/me

Get current user information.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@company.com",
  "full_name": "John Doe",
  "role": "admin",
  "organization": {
    "id": 1,
    "name": "Acme Manufacturing",
    "code": "ACME"
  },
  "subscription": {
    "id": 1,
    "tier": "professional",
    "status": "active",
    "max_users": 25,
    "max_plants": 5,
    "storage_limit_gb": 100
  }
}
```

---

## Subscriptions & Billing

### GET /api/v1/subscriptions/current

Get current organization's subscription.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Response** (200 OK):
```json
{
  "id": 1,
  "organization_id": 1,
  "tier": "professional",
  "status": "active",
  "billing_cycle": "monthly",
  "trial_starts_at": "2025-11-01T00:00:00Z",
  "trial_ends_at": "2025-11-15T00:00:00Z",
  "current_period_start": "2025-11-15T00:00:00Z",
  "current_period_end": "2025-12-15T00:00:00Z",
  "stripe_customer_id": "cus_ABC123",
  "stripe_subscription_id": "sub_DEF456",
  "max_users": 25,
  "max_plants": 5,
  "storage_limit_gb": 100,
  "created_at": "2025-11-01T10:00:00Z"
}
```

---

### GET /api/v1/subscriptions/usage

Get current usage vs. limits.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Response** (200 OK):
```json
{
  "subscription_id": 1,
  "tier": "professional",
  "limits": {
    "max_users": 25,
    "max_plants": 5,
    "storage_limit_gb": 100
  },
  "usage": {
    "users_count": 12,
    "plants_count": 2,
    "storage_used_gb": 34.5
  },
  "percentage": {
    "users": 48,
    "plants": 40,
    "storage": 34.5
  },
  "warnings": []
}
```

**Warnings** (when usage > 90%):
```json
{
  "warnings": [
    {
      "resource": "users",
      "usage": 23,
      "limit": 25,
      "percentage": 92,
      "message": "Approaching user limit. Consider upgrading."
    }
  ]
}
```

---

### POST /api/v1/subscriptions/checkout

Create Stripe checkout session for upgrade/new subscription.

**Request Body**:
```json
{
  "tier": "professional",
  "billing_cycle": "monthly",
  "success_url": "https://app.yourdomain.com/billing/success",
  "cancel_url": "https://app.yourdomain.com/billing"
}
```

**Response** (200 OK):
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_ABC123..."
}
```

**Flow**:
1. Frontend redirects user to `checkout_url`
2. User completes payment in Stripe
3. Stripe redirects to `success_url`
4. Stripe sends webhook `checkout.session.completed`
5. Backend activates subscription

---

### GET /api/v1/billing/portal

Get Stripe Customer Portal URL (for payment method updates, invoices).

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Response** (200 OK):
```json
{
  "url": "https://billing.stripe.com/session/ABC123..."
}
```

**Use Case**: Customer clicks "Manage Payment Methods" → Redirected to Stripe portal → Can update card, view invoices, cancel subscription.

---

### GET /api/v1/billing/invoices

List customer invoices.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Query Parameters**:
- `limit` (optional): Number of invoices (default: 10)
- `starting_after` (optional): Pagination cursor

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "in_ABC123",
      "number": "INV-001",
      "amount_due": 19900,
      "amount_paid": 19900,
      "currency": "usd",
      "status": "paid",
      "created": 1699564800,
      "period_start": 1699564800,
      "period_end": 1702243200,
      "invoice_pdf": "https://pay.stripe.com/invoice/ABC123/pdf"
    }
  ],
  "has_more": false
}
```

---

## Platform Admin

**Note**: All admin endpoints require `is_platform_admin = true` and are decorated with `@require_platform_admin`.

### GET /api/v1/admin/metrics

Get platform-wide KPIs.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "total_organizations": 42,
  "active_subscriptions": 38,
  "trial_subscriptions": 8,
  "total_mrr": 12450,
  "total_arr": 149400,
  "subscriptions_by_tier": {
    "starter": 15,
    "professional": 20,
    "enterprise": 3
  },
  "subscriptions_by_status": {
    "trial": 8,
    "active": 30,
    "cancelled": 3,
    "past_due": 1,
    "suspended": 0
  },
  "total_users": 287,
  "total_plants": 65,
  "total_storage_gb": 1245.6
}
```

---

### GET /api/v1/admin/organizations

List all organizations with filters.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `search` (optional): Search by name or code
- `tier` (optional): Filter by tier (`starter`, `professional`, `enterprise`)
- `status` (optional): Filter by status (`trial`, `active`, `cancelled`, `past_due`, `suspended`)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Page size (default: 20)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "name": "Acme Manufacturing",
      "code": "ACME",
      "created_at": "2025-11-01T10:00:00Z",
      "subscription": {
        "id": 1,
        "tier": "professional",
        "status": "active",
        "mrr": 19900
      },
      "usage": {
        "users_count": 12,
        "plants_count": 2,
        "storage_gb": 34.5
      }
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

### GET /api/v1/admin/organizations/{organization_id}

Get detailed organization information.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Acme Manufacturing",
  "code": "ACME",
  "created_at": "2025-11-01T10:00:00Z",
  "subscription": {
    "id": 1,
    "tier": "professional",
    "status": "active",
    "billing_cycle": "monthly",
    "trial_ends_at": null,
    "current_period_start": "2025-11-15T00:00:00Z",
    "current_period_end": "2025-12-15T00:00:00Z",
    "mrr": 19900,
    "stripe_customer_id": "cus_ABC123"
  },
  "usage": {
    "users_count": 12,
    "plants_count": 2,
    "storage_gb": 34.5,
    "work_orders_count": 145,
    "materials_count": 567
  },
  "users": [
    {
      "id": 1,
      "email": "admin@acme.com",
      "full_name": "John Doe",
      "role": "admin",
      "last_login_at": "2025-11-11T08:30:00Z"
    }
  ]
}
```

---

### POST /api/v1/admin/organizations/{organization_id}/extend-trial

Extend trial period (admin action).

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "additional_days": 7,
  "reason": "Customer requested extension to evaluate advanced features"
}
```

**Response** (200 OK):
```json
{
  "subscription_id": 1,
  "old_trial_ends_at": "2025-11-15T00:00:00Z",
  "new_trial_ends_at": "2025-11-22T00:00:00Z",
  "extended_by_days": 7
}
```

**Audit Log Created**:
- Action: `trial_extended`
- Admin user ID
- Reason
- Timestamp

---

### POST /api/v1/admin/organizations/{organization_id}/suspend

Suspend organization (stop all access).

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "reason": "Payment failed after 3 retries"
}
```

**Response** (200 OK):
```json
{
  "subscription_id": 1,
  "old_status": "active",
  "new_status": "suspended",
  "suspended_at": "2025-11-11T10:00:00Z"
}
```

**Effect**:
- Users can log in but see "Account Suspended" message
- All API calls blocked (except billing endpoints)
- Email sent to organization admin

---

### POST /api/v1/admin/organizations/{organization_id}/reactivate

Reactivate suspended organization.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "reason": "Payment received, reactivating account"
}
```

**Response** (200 OK):
```json
{
  "subscription_id": 1,
  "old_status": "suspended",
  "new_status": "active",
  "reactivated_at": "2025-11-11T10:30:00Z"
}
```

---

## Analytics

**Note**: All analytics endpoints require Professional or Enterprise tier (`@require_tier("professional")`).

### GET /api/v1/analytics/mrr/breakdown

Get MRR breakdown by tier and billing cycle.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "total_mrr": 12450,
  "mrr_by_tier": {
    "starter": 2940,
    "professional": 7960,
    "enterprise": 1550
  },
  "mrr_by_cycle": {
    "monthly": 8500,
    "annual": 3950
  },
  "customer_count": 38,
  "arpu": 328
}
```

---

### GET /api/v1/analytics/mrr/growth

Get MRR growth over time.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `months` (optional): Number of months (default: 12)

**Response** (200 OK):
```json
{
  "data": [
    {
      "month": "2025-01",
      "mrr": 8500,
      "new_customers": 5,
      "churned_customers": 1,
      "net_new_mrr": 1200,
      "churn_mrr": -200
    },
    {
      "month": "2025-02",
      "mrr": 9500,
      "new_customers": 4,
      "churned_customers": 0,
      "net_new_mrr": 1000,
      "churn_mrr": 0
    }
  ]
}
```

---

### GET /api/v1/analytics/trials/conversion

Get trial conversion metrics.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "total_trials": 50,
  "converted_trials": 38,
  "active_trials": 8,
  "expired_trials": 4,
  "conversion_rate": 76.0,
  "funnel": {
    "trial_started": 50,
    "trial_active": 8,
    "trial_expired": 4,
    "converted_to_paid": 38
  },
  "avg_days_to_conversion": 9.5
}
```

---

### GET /api/v1/analytics/churn

Get churn analysis.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `period_days` (optional): Analysis period in days (default: 30)

**Response** (200 OK):
```json
{
  "period_days": 30,
  "customer_churn": {
    "churned_customers": 3,
    "total_customers_start": 42,
    "churn_rate": 7.14
  },
  "mrr_churn": {
    "churned_mrr": 385,
    "total_mrr_start": 12450,
    "churn_rate": 3.09
  },
  "churn_by_tier": {
    "starter": 2,
    "professional": 1,
    "enterprise": 0
  },
  "churn_reasons": [
    {
      "reason": "price",
      "count": 2
    },
    {
      "reason": "switching_competitor",
      "count": 1
    }
  ]
}
```

---

### GET /api/v1/analytics/cohorts/retention

Get cohort retention analysis.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `cohort_month` (optional): Specific cohort (format: YYYY-MM), or all cohorts if omitted

**Response** (200 OK):
```json
{
  "cohorts": [
    {
      "cohort_month": "2025-01",
      "initial_customers": 10,
      "retention": {
        "month_0": 100,
        "month_1": 90,
        "month_2": 85,
        "month_3": 80,
        "month_4": 75,
        "month_5": 70,
        "month_6": 65
      }
    },
    {
      "cohort_month": "2025-02",
      "initial_customers": 12,
      "retention": {
        "month_0": 100,
        "month_1": 92,
        "month_2": 88,
        "month_3": 83,
        "month_4": 75,
        "month_5": 75
      }
    }
  ]
}
```

---

### GET /api/v1/analytics/forecast

Get revenue forecast.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `months` (optional): Forecast period in months (default: 6)

**Response** (200 OK):
```json
{
  "current_mrr": 12450,
  "forecast": [
    {
      "month": "2025-12",
      "projected_mrr": 13200,
      "confidence_interval": {
        "low": 12800,
        "high": 13600
      }
    },
    {
      "month": "2026-01",
      "projected_mrr": 14000,
      "confidence_interval": {
        "low": 13400,
        "high": 14600
      }
    }
  ],
  "growth_rate": 6.0,
  "assumptions": {
    "monthly_growth_rate": 6.0,
    "churn_rate": 3.0,
    "trial_conversion_rate": 76.0
  }
}
```

---

## Materials

### GET /api/v1/materials

List all materials.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Query Parameters**:
- `search` (optional): Search by code or name
- `type` (optional): Filter by type (`raw_material`, `finished_good`, `wip`, `consumable`)
- `category` (optional): Filter by category
- `skip` (optional): Pagination offset
- `limit` (optional): Page size (default: 50)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "code": "RM-001",
      "name": "Steel Plate 5mm",
      "type": "raw_material",
      "category": "Steel",
      "base_uom": "kg",
      "cost": 3.50,
      "stock_quantity": 1500.0,
      "created_at": "2025-11-01T10:00:00Z"
    }
  ],
  "total": 567,
  "skip": 0,
  "limit": 50
}
```

---

### POST /api/v1/materials

Create new material.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
```

**Request Body**:
```json
{
  "code": "RM-002",
  "name": "Aluminum Sheet 3mm",
  "type": "raw_material",
  "category": "Aluminum",
  "base_uom": "kg",
  "cost": 4.25,
  "description": "3mm aluminum sheet for panel manufacturing"
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "code": "RM-002",
  "name": "Aluminum Sheet 3mm",
  "type": "raw_material",
  "category": "Aluminum",
  "base_uom": "kg",
  "cost": 4.25,
  "stock_quantity": 0.0,
  "created_at": "2025-11-11T10:00:00Z"
}
```

---

### GET /api/v1/materials/{material_id}

Get material details.

**Response** (200 OK):
```json
{
  "id": 1,
  "code": "RM-001",
  "name": "Steel Plate 5mm",
  "type": "raw_material",
  "category": "Steel",
  "base_uom": "kg",
  "cost": 3.50,
  "stock_quantity": 1500.0,
  "alternative_uoms": [
    {
      "uom": "sheet",
      "conversion_factor": 50.0
    },
    {
      "uom": "pallet",
      "conversion_factor": 1000.0
    }
  ],
  "bom_count": 12,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-05T14:30:00Z"
}
```

---

## Work Orders

### GET /api/v1/work-orders

List work orders.

**Headers**:
```
Authorization: Bearer {access_token}
X-Organization-ID: 1
X-Plant-ID: 1
```

**Query Parameters**:
- `status` (optional): Filter by status (`draft`, `released`, `in_progress`, `completed`, `closed`)
- `material_id` (optional): Filter by material
- `priority` (optional): Filter by priority (`normal`, `high`, `urgent`)
- `skip`, `limit`: Pagination

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "wo_number": "WO-2025-001",
      "material": {
        "id": 10,
        "code": "FG-001",
        "name": "Bicycle Frame"
      },
      "quantity": 100,
      "status": "in_progress",
      "priority": "high",
      "start_date": "2025-11-10",
      "due_date": "2025-11-20",
      "quantity_produced": 45,
      "quantity_rejected": 2,
      "created_at": "2025-11-08T10:00:00Z"
    }
  ],
  "total": 145
}
```

---

### POST /api/v1/work-orders

Create work order.

**Request Body**:
```json
{
  "material_id": 10,
  "quantity": 100,
  "bom_id": 5,
  "start_date": "2025-11-10",
  "due_date": "2025-11-20",
  "priority": "high",
  "notes": "Rush order for customer XYZ"
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "wo_number": "WO-2025-002",
  "material_id": 10,
  "quantity": 100,
  "status": "draft",
  "priority": "high",
  "start_date": "2025-11-10",
  "due_date": "2025-11-20",
  "created_at": "2025-11-11T10:00:00Z"
}
```

---

### POST /api/v1/work-orders/{work_order_id}/release

Release work order for production.

**Response** (200 OK):
```json
{
  "id": 2,
  "wo_number": "WO-2025-002",
  "status": "released",
  "released_at": "2025-11-11T10:30:00Z",
  "material_availability": {
    "all_available": true,
    "shortages": []
  }
}
```

**Material Shortages** (if any):
```json
{
  "material_availability": {
    "all_available": false,
    "shortages": [
      {
        "material_id": 1,
        "material_code": "RM-001",
        "required": 500.0,
        "available": 350.0,
        "shortage": 150.0,
        "uom": "kg"
      }
    ]
  }
}
```

---

### POST /api/v1/work-orders/{work_order_id}/log-production

Log production activity.

**Request Body**:
```json
{
  "operation_id": 10,
  "quantity_produced": 10,
  "quantity_rejected": 1,
  "operator_id": 5,
  "notes": "Minor weld defect on 1 unit"
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "work_order_id": 2,
  "operation_id": 10,
  "quantity_produced": 10,
  "quantity_rejected": 1,
  "logged_at": "2025-11-11T14:30:00Z"
}
```

---

## Quality (NCR)

### GET /api/v1/ncrs

List Non-Conformance Reports.

**Query Parameters**:
- `status` (optional): Filter by status (`open`, `in_progress`, `closed`)
- `severity` (optional): Filter by severity (`critical`, `major`, `minor`)
- `type` (optional): Filter by type (`internal`, `customer`, `supplier`)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "ncr_number": "NCR-2025-001",
      "title": "Weld crack on Frame #123",
      "type": "internal",
      "severity": "major",
      "status": "in_progress",
      "material_id": 10,
      "quantity_affected": 5,
      "created_at": "2025-11-10T08:00:00Z",
      "days_open": 2
    }
  ],
  "total": 23
}
```

---

### POST /api/v1/ncrs

Create NCR.

**Request Body**:
```json
{
  "title": "Paint defect on Panel #456",
  "type": "internal",
  "severity": "minor",
  "material_id": 15,
  "quantity_affected": 10,
  "location": "Paint booth",
  "description": "Paint bubbling observed on 10 panels. Possible contamination in paint mix.",
  "images": [
    "https://storage.example.com/ncr-images/img1.jpg"
  ]
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "ncr_number": "NCR-2025-002",
  "title": "Paint defect on Panel #456",
  "status": "open",
  "created_at": "2025-11-11T10:00:00Z"
}
```

---

## Inventory

### GET /api/v1/inventory/stock

Get stock overview.

**Query Parameters**:
- `material_id` (optional): Filter by material
- `location_id` (optional): Filter by location

**Response** (200 OK):
```json
{
  "items": [
    {
      "material_id": 1,
      "material_code": "RM-001",
      "material_name": "Steel Plate 5mm",
      "total_quantity": 1500.0,
      "reserved_quantity": 200.0,
      "available_quantity": 1300.0,
      "uom": "kg",
      "locations": [
        {
          "location_id": 1,
          "location_code": "RM-A1",
          "quantity": 800.0
        },
        {
          "location_id": 2,
          "location_code": "RM-A2",
          "quantity": 700.0
        }
      ]
    }
  ]
}
```

---

### POST /api/v1/inventory/transactions

Create inventory transaction.

**Request Body** (Goods Receipt):
```json
{
  "type": "goods_receipt",
  "material_id": 1,
  "quantity": 500.0,
  "uom": "kg",
  "location_id": 1,
  "reference": "PO-2025-123",
  "lot_number": "LOT-2025-11-001",
  "cost_per_unit": 3.50
}
```

**Request Body** (Goods Issue):
```json
{
  "type": "goods_issue",
  "material_id": 1,
  "quantity": 100.0,
  "uom": "kg",
  "location_id": 1,
  "reason": "production",
  "work_order_id": 5
}
```

**Response** (201 Created):
```json
{
  "id": 456,
  "type": "goods_receipt",
  "material_id": 1,
  "quantity": 500.0,
  "uom": "kg",
  "location_id": 1,
  "new_stock_quantity": 2000.0,
  "posted_at": "2025-11-11T10:00:00Z"
}
```

---

## Webhooks

### POST /api/v1/webhooks/stripe

Stripe webhook endpoint (called by Stripe, not by clients).

**Headers** (from Stripe):
```
Stripe-Signature: t=1699564800,v1=abcdef...
```

**Payload** (example: checkout.session.completed):
```json
{
  "id": "evt_ABC123",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_ABC123",
      "customer": "cus_ABC123",
      "subscription": "sub_DEF456",
      "metadata": {
        "organization_id": "1",
        "tier": "professional",
        "billing_cycle": "monthly"
      }
    }
  }
}
```

**Response** (200 OK):
```json
{
  "status": "success"
}
```

**Supported Events**:
- `checkout.session.completed`: New subscription created
- `invoice.payment_succeeded`: Payment successful → extend subscription
- `invoice.payment_failed`: Payment failed → send notification, retry
- `customer.subscription.updated`: Subscription changed (upgrade/downgrade)
- `customer.subscription.deleted`: Subscription cancelled

**Security**: Webhook signature verified using `STRIPE_WEBHOOK_SECRET`.

---

## Internal Jobs API

**Note**: These endpoints are for internal use by pg_cron scheduled jobs. Require `X-API-Key` header.

### POST /api/v1/jobs/track-usage

Track usage for all organizations (runs every 6 hours via pg_cron).

**Headers**:
```
X-API-Key: your-internal-api-key
```

**Response** (200 OK):
```json
{
  "job_name": "track-usage",
  "status": "completed",
  "organizations_processed": 42,
  "errors": 0,
  "duration_seconds": 12.5,
  "executed_at": "2025-11-11T12:00:00Z"
}
```

**What It Does**:
- Queries all active subscriptions
- For each organization:
  - Count users
  - Count plants
  - Calculate storage used
- Update usage records in database

---

### POST /api/v1/jobs/check-trial-expirations

Check and handle expired trials (runs daily at 2 AM UTC).

**Headers**:
```
X-API-Key: your-internal-api-key
```

**Response** (200 OK):
```json
{
  "job_name": "check-trial-expirations",
  "status": "completed",
  "trials_checked": 8,
  "trials_expiring_soon": 3,
  "trials_expired": 1,
  "emails_sent": 4,
  "errors": 0,
  "executed_at": "2025-11-11T02:00:00Z"
}
```

**What It Does**:
- Find trials expiring in 7, 3, 1 days → Send reminder emails
- Find trials that expired today → Suspend access, send notification

---

## Health Checks

### GET /health

Basic health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-11T10:00:00Z",
  "version": "1.0.0"
}
```

---

### GET /ready

Readiness probe (checks database connection).

**Response** (200 OK):
```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2025-11-11T10:00:00Z"
}
```

**Response** (503 Service Unavailable) if database is down:
```json
{
  "status": "not_ready",
  "database": "disconnected",
  "error": "Connection refused"
}
```

---

### GET /live

Liveness probe (checks if application is alive).

**Response** (200 OK):
```json
{
  "status": "alive"
}
```

---

### GET /startup

Startup probe (checks if application has finished starting).

**Response** (200 OK):
```json
{
  "status": "started",
  "database_migrations": "up_to_date",
  "extensions_loaded": true
}
```

---

## Error Responses

All endpoints return errors in standard format:

**400 Bad Request**:
```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**401 Unauthorized**:
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden** (Feature Gating):
```json
{
  "detail": "Feature requires Professional tier or higher"
}
```

**404 Not Found**:
```json
{
  "detail": "Material with ID 999 not found"
}
```

**422 Unprocessable Entity** (Validation):
```json
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error. Please contact support."
}
```

---

## Rate Limiting

**Limits**:
- **Authenticated**: 1000 requests / hour per user
- **Unauthenticated**: 100 requests / hour per IP
- **Webhooks**: No limit (verified by signature)

**Headers** (included in all responses):
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1699568400
```

**429 Too Many Requests**:
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

---

## Pagination

All list endpoints support pagination with standard parameters:

**Query Parameters**:
- `skip` (default: 0): Number of records to skip
- `limit` (default: 50, max: 100): Page size

**Response Format**:
```json
{
  "items": [...],
  "total": 567,
  "skip": 0,
  "limit": 50,
  "has_more": true
}
```

**Example**: Get page 2 (records 51-100):
```
GET /api/v1/materials?skip=50&limit=50
```

---

## Filtering & Searching

Most list endpoints support filtering and search:

**Search** (text search):
```
GET /api/v1/materials?search=steel
```

**Filter** (exact match):
```
GET /api/v1/materials?type=raw_material&category=Steel
```

**Combined**:
```
GET /api/v1/materials?search=plate&type=raw_material&category=Steel
```

---

## Sorting

List endpoints support sorting:

**Query Parameter**:
- `sort_by` (default: varies by endpoint): Field to sort by
- `sort_order` (`asc` or `desc`, default: `asc`): Sort direction

**Example**:
```
GET /api/v1/materials?sort_by=created_at&sort_order=desc
```

---

## WebSocket Endpoints (Future)

**Coming Soon**: Real-time updates via WebSocket for:
- Production status updates
- Machine status changes
- NCR notifications
- Trial expiry warnings

**Endpoint** (planned): `wss://api.yourdomain.com/ws`

---

## Postman Collection

Import our Postman collection for easy API testing:

**Download**: [Unison API Postman Collection](https://api.yourdomain.com/docs/postman-collection.json)

**Import Steps**:
1. Open Postman
2. Click "Import" → "Link"
3. Paste URL
4. Collection imported with all endpoints

**Environment Variables** (set these):
- `base_url`: http://localhost:8000
- `access_token`: (get from /auth/login)
- `organization_id`: 1
- `plant_id`: 1

---

## SDK / Client Libraries (Future)

**Coming Soon**: Official client libraries for:
- Python
- JavaScript/TypeScript
- C# / .NET

**Example** (Python SDK - planned):
```python
from unison import UnisonClient

client = UnisonClient(api_key="your_api_key")

# Create material
material = client.materials.create(
    code="RM-001",
    name="Steel Plate",
    type="raw_material"
)

# Create work order
wo = client.work_orders.create(
    material_id=material.id,
    quantity=100
)
```

---

## Support

**API Issues**:
- Email: api-support@unison.com
- Slack: #api-help (for Enterprise customers)

**Documentation**:
- Interactive API Docs: https://api.yourdomain.com/docs
- Developer Portal: https://developers.unison.com

---

**Last Updated**: 2025-11-11 | **Version**: 1.0

**Changelog**:
- 2025-11-11: Initial API documentation with commercial infrastructure endpoints
