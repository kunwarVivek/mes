"""
SQLAlchemy models for Subscription System

Maps to database tables:
- subscriptions
- subscription_usage
- invoices
- subscription_add_ons
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Numeric,
    ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional


class SubscriptionModel(Base):
    """
    Subscription model - Core subscription management with Stripe integration

    Business Rules:
    - One subscription per organization (UNIQUE organization_id)
    - Trial: 14 days, auto-created on organization signup
    - Tiers: starter, professional, enterprise
    - NULL limits = unlimited (Enterprise tier)
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                           unique=True, nullable=False, index=True)

    # Subscription Details
    tier = Column(String(50), nullable=False, index=True)  # starter, professional, enterprise
    status = Column(String(50), nullable=False, index=True)  # trial, active, cancelled, past_due, suspended
    billing_cycle = Column(String(20), nullable=True)  # monthly, annual (NULL during trial)

    # Trial Management
    trial_starts_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    trial_converted = Column(Boolean, default=False, nullable=False)

    # Stripe Integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)

    # Billing Period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    billing_email = Column(String(255), nullable=True)

    # Resource Limits (NULL = unlimited for Enterprise)
    max_users = Column(Integer, nullable=True)
    max_plants = Column(Integer, nullable=True)
    storage_limit_gb = Column(Integer, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="subscription")
    invoices = relationship("InvoiceModel", back_populates="subscription", cascade="all, delete-orphan")
    add_ons = relationship("SubscriptionAddOnModel", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "tier IN ('starter', 'professional', 'enterprise')",
            name="check_subscription_tier"
        ),
        CheckConstraint(
            "status IN ('trial', 'active', 'cancelled', 'past_due', 'suspended')",
            name="check_subscription_status"
        ),
        CheckConstraint(
            "billing_cycle IS NULL OR billing_cycle IN ('monthly', 'annual')",
            name="check_billing_cycle"
        ),
        Index('idx_subscriptions_org_id', 'organization_id'),
        Index('idx_subscriptions_stripe_customer', 'stripe_customer_id'),
        Index('idx_subscriptions_status', 'status'),
        Index('idx_subscriptions_trial_ends', 'trial_ends_at'),
        Index('idx_subscriptions_tier', 'tier'),
    )

    def __repr__(self):
        return f"<Subscription(org_id={self.organization_id}, tier='{self.tier}', status='{self.status}')>"


class SubscriptionUsageModel(Base):
    """
    Subscription usage tracking - Monitors resource consumption

    Updated periodically (e.g., every 6 hours via pg_cron)
    Used to enforce subscription limits
    """
    __tablename__ = "subscription_usage"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                           nullable=False, index=True)

    # Current Usage Metrics
    current_users = Column(Integer, default=0, nullable=False)
    current_plants = Column(Integer, default=0, nullable=False)
    storage_used_gb = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Measurement timestamp
    measured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    organization = relationship("Organization")

    __table_args__ = (
        Index('idx_subscription_usage_org_id', 'organization_id'),
        Index('idx_subscription_usage_measured_at', 'measured_at'),
    )

    def __repr__(self):
        return f"<SubscriptionUsage(org_id={self.organization_id}, users={self.current_users}, plants={self.current_plants})>"


class InvoiceModel(Base):
    """
    Invoice model - Billing history and payment tracking

    Synced with Stripe invoices
    Amounts stored in cents (integer)
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"),
                           nullable=False, index=True)

    # Stripe Integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)

    # Invoice Details
    invoice_number = Column(String(100), unique=True, nullable=False)
    amount_due = Column(Integer, nullable=False)  # in cents
    amount_paid = Column(Integer, default=0, nullable=False)  # in cents
    currency = Column(String(3), default='USD', nullable=False)

    # Status
    status = Column(String(50), nullable=False, index=True)  # draft, open, paid, void, uncollectible

    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # PDF
    invoice_pdf_url = Column(String(500), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    subscription = relationship("SubscriptionModel", back_populates="invoices")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')",
            name="check_invoice_status"
        ),
        Index('idx_invoices_org_id', 'organization_id'),
        Index('idx_invoices_subscription_id', 'subscription_id'),
        Index('idx_invoices_stripe_id', 'stripe_invoice_id'),
        Index('idx_invoices_status', 'status'),
        Index('idx_invoices_due_date', 'due_date'),
        Index('idx_invoices_invoice_date', 'invoice_date'),
    )

    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', amount=${self.amount_due/100:.2f}, status='{self.status}')>"


class SubscriptionAddOnModel(Base):
    """
    Subscription add-ons - Additional purchased capacity

    Types: extra_users, extra_plants, extra_storage_gb
    Active add-ons have removed_at = NULL
    """
    __tablename__ = "subscription_add_ons"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"),
                           nullable=False, index=True)

    # Add-on Details
    add_on_type = Column(String(50), nullable=False, index=True)  # extra_users, extra_plants, extra_storage_gb
    quantity = Column(Integer, nullable=False)  # How many additional units
    unit_price = Column(Integer, nullable=False)  # Price per unit in cents

    # Stripe Integration
    stripe_price_id = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    removed_at = Column(DateTime(timezone=True), nullable=True)  # NULL = active

    # Relationship
    subscription = relationship("SubscriptionModel", back_populates="add_ons")

    __table_args__ = (
        CheckConstraint(
            "add_on_type IN ('extra_users', 'extra_plants', 'extra_storage_gb')",
            name="check_add_on_type"
        ),
        Index('idx_add_ons_subscription_id', 'subscription_id'),
        Index('idx_add_ons_type', 'add_on_type'),
        Index('idx_add_ons_active', 'subscription_id', 'removed_at'),  # For active add-ons
    )

    def __repr__(self):
        status = "active" if self.removed_at is None else "removed"
        return f"<AddOn(type='{self.add_on_type}', qty={self.quantity}, status='{status}')>"
