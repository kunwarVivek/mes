import apiClient from '@/lib/api-client'

/**
 * Analytics Service
 *
 * API client for business intelligence and metrics:
 * - MRR/ARR tracking
 * - Trial conversion
 * - Churn analysis
 * - Cohort retention
 * - Revenue forecasting
 */

export interface MRRBreakdown {
  total_mrr: number
  mrr_by_tier: {
    starter: number
    professional: number
    enterprise: number
  }
  mrr_by_cycle: {
    monthly: number
    annual: number
  }
  customer_count: number
  arpu: number
}

export interface MRRGrowthDataPoint {
  date: string
  mrr: number
  new_customers: number
  churned_customers: number
  net_customers: number
}

export interface TrialConversionMetrics {
  total_trials: number
  converted_trials: number
  active_trials: number
  expired_trials: number
  conversion_rate: number
  avg_days_to_convert: number
}

export interface ChurnMetrics {
  period_days: number
  customers_start: number
  churned_count: number
  churn_rate: number
  mrr_churned: number
  mrr_churn_rate: number
}

export interface CohortRetention {
  cohort_month: string
  cohort_size: number
  retention: Array<{
    month: number
    retained: number
    retention_rate: number
  }>
}

export interface RevenueForecast {
  date: string
  forecasted_mrr: number
  forecasted_arr: number
  growth_rate: number
}

export interface AnalyticsDashboardSummary {
  mrr: MRRBreakdown
  trials: TrialConversionMetrics
  churn: ChurnMetrics
  growth: MRRGrowthDataPoint[]
  forecast: RevenueForecast[]
}

export const analyticsService = {
  /**
   * Get MRR breakdown by tier and billing cycle
   */
  getMRRBreakdown: async (): Promise<MRRBreakdown> => {
    const response = await apiClient.get('/api/v1/analytics/mrr/breakdown')
    return response.data
  },

  /**
   * Get MRR growth over time
   */
  getMRRGrowth: async (months: number = 12): Promise<MRRGrowthDataPoint[]> => {
    const response = await apiClient.get('/api/v1/analytics/mrr/growth', {
      params: { months },
    })
    return response.data
  },

  /**
   * Get trial conversion metrics
   */
  getTrialConversionMetrics: async (): Promise<TrialConversionMetrics> => {
    const response = await apiClient.get('/api/v1/analytics/trials/conversion')
    return response.data
  },

  /**
   * Get churn metrics
   */
  getChurnMetrics: async (periodDays: number = 30): Promise<ChurnMetrics> => {
    const response = await apiClient.get('/api/v1/analytics/churn', {
      params: { period_days: periodDays },
    })
    return response.data
  },

  /**
   * Get cohort retention analysis
   */
  getCohortRetention: async (cohortMonth?: string): Promise<CohortRetention[]> => {
    const response = await apiClient.get('/api/v1/analytics/cohorts/retention', {
      params: cohortMonth ? { cohort_month: cohortMonth } : {},
    })
    return response.data
  },

  /**
   * Get revenue forecast
   */
  getRevenueForecast: async (months: number = 6): Promise<RevenueForecast[]> => {
    const response = await apiClient.get('/api/v1/analytics/forecast', {
      params: { months },
    })
    return response.data
  },

  /**
   * Get complete analytics dashboard summary
   */
  getDashboardSummary: async (): Promise<AnalyticsDashboardSummary> => {
    const response = await apiClient.get('/api/v1/analytics/dashboard/summary')
    return response.data
  },
}
