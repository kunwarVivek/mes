import apiClient from '@/lib/api-client'

/**
 * Billing Service
 *
 * API client for customer-facing billing operations:
 * - View current subscription
 * - Create checkout sessions
 * - View usage
 * - View invoices
 * - Upgrade/downgrade tiers
 */

export interface Subscription {
  id: number
  organization_id: number
  tier: 'starter' | 'professional' | 'enterprise'
  status: 'trial' | 'active' | 'cancelled' | 'past_due' | 'suspended'
  billing_cycle: 'monthly' | 'annual'
  trial_starts_at?: string
  trial_ends_at?: string
  trial_converted: boolean
  stripe_customer_id?: string
  stripe_subscription_id?: string
  max_users?: number
  max_plants?: number
  storage_limit_gb?: number
  created_at: string
  updated_at?: string
}

export interface SubscriptionUsage {
  current_users: number
  current_plants: number
  storage_used_gb: number
  last_calculated_at: string
}

export interface Invoice {
  id: number
  organization_id: number
  invoice_number: string
  amount_cents: number
  amount_due_cents: number
  amount_paid_cents: number
  status: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible'
  invoice_date: string
  due_date: string
  paid_at?: string
  stripe_invoice_id?: string
  description?: string
}

export interface CheckoutSessionRequest {
  tier: string
  billing_cycle: string
  success_url: string
  cancel_url: string
}

export interface CheckoutSessionResponse {
  checkout_url: string
  session_id: string
  expires_at: string
}

export interface InvoiceListResponse {
  invoices: Invoice[]
  total_count: number
  has_more: boolean
}

export interface PricingTier {
  tier: string
  monthly_price: number
  annual_price: number
  features: string[]
  limits: {
    max_users?: number
    max_plants?: number
    storage_limit_gb?: number
  }
}

export const billingService = {
  /**
   * Get current subscription for organization
   */
  getCurrentSubscription: async (): Promise<Subscription> => {
    const response = await apiClient.get('/api/v1/subscription')
    return response.data
  },

  /**
   * Get subscription usage
   */
  getUsage: async (): Promise<SubscriptionUsage> => {
    const response = await apiClient.get('/api/v1/subscription/usage')
    return response.data
  },

  /**
   * Create Stripe checkout session
   */
  createCheckoutSession: async (
    request: CheckoutSessionRequest
  ): Promise<CheckoutSessionResponse> => {
    const response = await apiClient.post('/api/v1/billing/checkout', request)
    return response.data
  },

  /**
   * Get pricing information for all tiers
   */
  getPricing: async (): Promise<PricingTier[]> => {
    const response = await apiClient.get('/api/v1/billing/pricing')
    return response.data
  },

  /**
   * List invoices for current organization
   */
  listInvoices: async (params?: {
    limit?: number
    offset?: number
  }): Promise<InvoiceListResponse> => {
    const response = await apiClient.get('/api/v1/billing/invoices', { params })
    return response.data
  },

  /**
   * Download invoice PDF
   */
  downloadInvoice: async (invoiceId: number): Promise<Blob> => {
    const response = await apiClient.get(`/api/v1/billing/invoices/${invoiceId}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Get Stripe billing portal URL
   */
  getBillingPortalUrl: async (): Promise<{ url: string }> => {
    const response = await apiClient.post('/api/v1/billing/portal')
    return response.data
  },

  /**
   * Upgrade to higher tier
   */
  upgradeTier: async (newTier: string, billingCycle: string): Promise<Subscription> => {
    const response = await apiClient.post('/api/v1/subscription/upgrade', {
      new_tier: newTier,
      billing_cycle: billingCycle,
    })
    return response.data
  },

  /**
   * Downgrade to lower tier (effective at end of billing period)
   */
  downgradeTier: async (newTier: string): Promise<Subscription> => {
    const response = await apiClient.post('/api/v1/subscription/downgrade', {
      new_tier: newTier,
    })
    return response.data
  },

  /**
   * Cancel subscription (effective at end of billing period)
   */
  cancelSubscription: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/api/v1/subscription/cancel')
    return response.data
  },

  /**
   * Reactivate cancelled subscription
   */
  reactivateSubscription: async (): Promise<Subscription> => {
    const response = await apiClient.post('/api/v1/subscription/reactivate')
    return response.data
  },
}
