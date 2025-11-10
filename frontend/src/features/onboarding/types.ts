/**
 * Onboarding Wizard Types
 *
 * Shared types for the onboarding wizard flow
 */

export type OnboardingStep =
  | 'signup'
  | 'email-verification'
  | 'organization'
  | 'plant'
  | 'team-invitations'

export interface OnboardingState {
  currentStep: OnboardingStep
  completedSteps: OnboardingStep[]
  email?: string
  organizationSlug?: string
  organizationId?: number
  plantId?: number
}

export interface StepperStep {
  id: OnboardingStep
  label: string
  description: string
}

export const ONBOARDING_STEPS: StepperStep[] = [
  {
    id: 'signup',
    label: 'Sign Up',
    description: 'Create your account',
  },
  {
    id: 'email-verification',
    label: 'Verify Email',
    description: 'Confirm your email',
  },
  {
    id: 'organization',
    label: 'Organization',
    description: 'Set up your organization',
  },
  {
    id: 'plant',
    label: 'Plant',
    description: 'Create your first plant',
  },
  {
    id: 'team-invitations',
    label: 'Team',
    description: 'Invite team members',
  },
]
