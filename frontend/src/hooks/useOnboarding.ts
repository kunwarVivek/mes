/**
 * useOnboarding Hooks
 *
 * TanStack Query hooks for self-service onboarding API
 * Provides 6 endpoints for the onboarding wizard flow
 *
 * Endpoints:
 * 1. POST /onboarding/signup - User signup (public)
 * 2. POST /onboarding/verify-email - Email verification (public)
 * 3. POST /onboarding/organization - Organization setup (authenticated)
 * 4. POST /onboarding/plant - Plant creation (authenticated)
 * 5. POST /onboarding/team/invite - Team invitations (authenticated)
 * 6. GET /onboarding/progress - Onboarding progress (authenticated)
 */
import { useMutation, useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'

// ============================================================================
// Type Definitions - Request/Response Types
// ============================================================================

// 1. Signup Types
export interface SignupRequest {
  email: string
  password: string
}

export interface SignupResponse {
  user_id: number
  email: string
  message: string
  onboarding_status: string
}

// 2. Verify Email Types
export interface VerifyEmailRequest {
  token: string
}

export interface VerifyEmailResponse {
  success: boolean
  message: string
  onboarding_status: string
}

// 3. Setup Organization Types
export interface SetupOrganizationRequest {
  organization_name: string
}

export interface SetupOrganizationResponse {
  organization_id: number
  name: string
  slug: string
  created_at: string
}

// 4. Create Plant Types
export interface CreatePlantRequest {
  plant_name: string
  address?: string
  timezone?: string
}

export interface CreatePlantResponse {
  plant_id: number
  name: string
  organization_id: number
  created_at: string
}

// 5. Invite Team Types
export type TeamRole = 'admin' | 'operator' | 'viewer' | 'custom'

export interface TeamInvitation {
  email: string
  role: TeamRole
  role_description?: string
}

export interface InviteTeamRequest {
  invitations: TeamInvitation[]
}

export interface SentInvitation {
  email: string
  role: TeamRole
  role_description?: string
  expires_at: string
}

export interface InviteTeamResponse {
  invitations_sent: SentInvitation[]
}

// 6. Onboarding Progress Types
export interface OnboardingProgress {
  current_status: string
  completed_steps: string[]
  next_step: string
}

// ============================================================================
// 1. useSignup - User Signup Mutation (Public)
// ============================================================================

/**
 * Hook for user signup with email verification
 *
 * This is a public endpoint - no authentication required
 *
 * @example
 * const { mutate, isPending, error } = useSignup()
 * mutate({ email: 'user@example.com', password: 'SecurePass123!' })
 */
export function useSignup() {
  return useMutation({
    mutationFn: async (request: SignupRequest) => {
      const response = await apiClient.post<SignupResponse>(
        '/onboarding/signup',
        request
      )
      return response.data
    },
  })
}

// ============================================================================
// 2. useVerifyEmail - Email Verification Mutation (Public)
// ============================================================================

/**
 * Hook for email verification with token
 *
 * This is a public endpoint - no authentication required
 *
 * @example
 * const { mutate, isPending, error } = useVerifyEmail()
 * mutate({ token: 'abc123def456' })
 */
export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (request: VerifyEmailRequest) => {
      const response = await apiClient.post<VerifyEmailResponse>(
        '/onboarding/verify-email',
        request
      )
      return response.data
    },
  })
}

// ============================================================================
// 3. useSetupOrganization - Organization Setup Mutation (Authenticated)
// ============================================================================

/**
 * Hook for organization setup
 *
 * Requires JWT authentication
 * Creates organization and associates user with it
 *
 * @example
 * const { mutate, isPending, error } = useSetupOrganization()
 * mutate({ organization_name: 'Acme Corporation' })
 */
export function useSetupOrganization() {
  return useMutation({
    mutationFn: async (request: SetupOrganizationRequest) => {
      const response = await apiClient.post<SetupOrganizationResponse>(
        '/onboarding/organization',
        request
      )
      return response.data
    },
  })
}

// ============================================================================
// 4. useCreatePlant - Plant Creation Mutation (Authenticated)
// ============================================================================

/**
 * Hook for plant creation
 *
 * Requires JWT authentication and existing organization
 * Creates plant and associates user with it
 *
 * @example
 * const { mutate, isPending, error } = useCreatePlant()
 * mutate({
 *   plant_name: 'Manufacturing Plant 1',
 *   address: '123 Factory St, City, State',
 *   timezone: 'America/New_York'
 * })
 */
export function useCreatePlant() {
  return useMutation({
    mutationFn: async (request: CreatePlantRequest) => {
      const response = await apiClient.post<CreatePlantResponse>(
        '/onboarding/plant',
        request
      )
      return response.data
    },
  })
}

// ============================================================================
// 5. useInviteTeam - Team Invitations Mutation (Authenticated)
// ============================================================================

/**
 * Hook for sending team member invitations
 *
 * Requires JWT authentication and existing organization
 * Creates pending invitations and queues invitation emails
 *
 * @example
 * const { mutate, isPending, error } = useInviteTeam()
 * mutate({
 *   invitations: [
 *     { email: 'user1@example.com', role: 'admin' },
 *     { email: 'user2@example.com', role: 'operator' }
 *   ]
 * })
 */
export function useInviteTeam() {
  return useMutation({
    mutationFn: async (request: InviteTeamRequest) => {
      const response = await apiClient.post<InviteTeamResponse>(
        '/onboarding/team/invite',
        request
      )
      return response.data
    },
  })
}

// ============================================================================
// 6. useOnboardingProgress - Onboarding Progress Query (Authenticated)
// ============================================================================

/**
 * Hook for fetching onboarding progress
 *
 * Requires JWT authentication
 * Returns current status, completed steps, and next step
 *
 * @example
 * const { data, isLoading, error } = useOnboardingProgress()
 * // data: OnboardingProgress | undefined
 */
export function useOnboardingProgress() {
  return useQuery({
    queryKey: ['onboarding-progress'],
    queryFn: async () => {
      const response = await apiClient.get<OnboardingProgress>(
        '/onboarding/progress'
      )
      return response.data
    },
  })
}

// ============================================================================
// Convenience Hooks with Transformed Data (Optional)
// ============================================================================

/**
 * Hook that returns onboarding progress with type-safe result
 *
 * Provides consistent return type matching useDashboardMetrics pattern
 *
 * @example
 * const { isLoading, error, progress } = useOnboardingProgressResult()
 */
export interface UseOnboardingProgressResult {
  isLoading: boolean
  error?: Error | null
  progress?: OnboardingProgress
}

export function useOnboardingProgressResult(): UseOnboardingProgressResult {
  const { data, isLoading, error } = useOnboardingProgress()

  return {
    isLoading,
    error: error as Error | null | undefined,
    progress: data,
  }
}
