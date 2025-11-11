import apiClient from '@/lib/api-client'

/**
 * Platform Admin Service
 *
 * API client for platform admin operations.
 * All endpoints require is_superuser=true.
 */

export interface Organization {
  id: number
  org_code: string
  org_name: string
  created_at: string
  is_active: boolean
  subscription?: Subscription
}

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
  id: number
  organization_id: number
  current_users: number
  current_plants: number
  storage_used_gb: number
  last_calculated_at: string
}

export interface PlatformMetrics {
  total_organizations: number
  active_subscriptions: number
  trial_subscriptions: number
  monthly_recurring_revenue: number
  total_users: number
  total_plants: number
  total_storage_gb: number
  organizations_by_tier: {
    starter: number
    professional: number
    enterprise: number
  }
  organizations_by_status: {
    trial: number
    active: number
    cancelled: number
    past_due: number
    suspended: number
  }
}

export interface OrganizationListResponse {
  organizations: Organization[]
  total_count: number
  has_more: boolean
}

export interface AdminAction {
  subscription_id?: number
  organization_id?: number
  days?: number
  reason?: string
  new_tier?: string
  immediate?: boolean
}

export interface AdminActionResponse {
  success: boolean
  message: string
  subscription?: Subscription
  organization?: Organization
}

export interface AuditLogEntry {
  id: number
  admin_user_id: number
  admin_email: string
  admin_name: string
  action: string
  target_type?: string
  target_id?: number
  details?: Record<string, any>
  created_at: string
}

export interface AuditLogListResponse {
  logs: AuditLogEntry[]
  total_count: number
  has_more: boolean
}

export interface ImpersonationResponse {
  token: string
  expires_at: string
  target_user_id: number
  target_organization_id: number
}

export const adminService = {
  /**
   * Get platform-wide metrics and KPIs
   */
  getMetrics: async (): Promise<PlatformMetrics> => {
    const response = await apiClient.get('/api/v1/platform-admin/metrics')
    return response.data
  },

  /**
   * List all organizations with optional filters
   */
  listOrganizations: async (params?: {
    search?: string
    status?: string
    tier?: string
    limit?: number
    offset?: number
  }): Promise<OrganizationListResponse> => {
    const response = await apiClient.get('/api/v1/platform-admin/organizations', {
      params,
    })
    return response.data
  },

  /**
   * Get organization details by ID
   */
  getOrganization: async (id: number): Promise<Organization> => {
    const response = await apiClient.get(`/api/v1/platform-admin/organizations/${id}`)
    return response.data
  },

  /**
   * Update organization details
   */
  updateOrganization: async (
    id: number,
    data: Partial<Organization>
  ): Promise<Organization> => {
    const response = await apiClient.patch(
      `/api/v1/platform-admin/organizations/${id}`,
      data
    )
    return response.data
  },

  /**
   * Get subscription details
   */
  getSubscription: async (subscriptionId: number): Promise<Subscription> => {
    const response = await apiClient.get(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}`
    )
    return response.data
  },

  /**
   * Get subscription usage
   */
  getSubscriptionUsage: async (organizationId: number): Promise<SubscriptionUsage> => {
    const response = await apiClient.get(
      `/api/v1/platform-admin/organizations/${organizationId}/usage`
    )
    return response.data
  },

  /**
   * Extend trial by N days (1-90)
   */
  extendTrial: async (
    subscriptionId: number,
    days: number,
    reason: string
  ): Promise<AdminActionResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}/extend-trial`,
      { days, reason }
    )
    return response.data
  },

  /**
   * Override subscription tier (admin-initiated)
   */
  overrideTier: async (
    subscriptionId: number,
    newTier: string,
    reason: string
  ): Promise<AdminActionResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}/override-tier`,
      { new_tier: newTier, reason }
    )
    return response.data
  },

  /**
   * Suspend subscription (non-payment, abuse)
   */
  suspendSubscription: async (
    subscriptionId: number,
    reason: string
  ): Promise<AdminActionResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}/suspend`,
      { reason }
    )
    return response.data
  },

  /**
   * Reactivate suspended subscription
   */
  reactivateSubscription: async (
    subscriptionId: number,
    reason: string
  ): Promise<AdminActionResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}/reactivate`,
      { reason }
    )
    return response.data
  },

  /**
   * Cancel subscription immediately
   */
  cancelSubscription: async (
    subscriptionId: number,
    reason: string,
    immediate: boolean = false
  ): Promise<AdminActionResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/subscriptions/${subscriptionId}/cancel`,
      { reason, immediate }
    )
    return response.data
  },

  /**
   * Get audit logs with filters
   */
  getAuditLogs: async (params?: {
    admin_user_id?: number
    action?: string
    target_type?: string
    target_id?: number
    limit?: number
    offset?: number
  }): Promise<AuditLogListResponse> => {
    const response = await apiClient.get('/api/v1/platform-admin/audit-logs', {
      params,
    })
    return response.data
  },

  /**
   * Create impersonation token for customer support
   */
  impersonateUser: async (
    userId: number,
    durationMinutes: number = 60
  ): Promise<ImpersonationResponse> => {
    const response = await apiClient.post(
      `/api/v1/platform-admin/impersonate/${userId}`,
      { duration_minutes: durationMinutes }
    )
    return response.data
  },
}
