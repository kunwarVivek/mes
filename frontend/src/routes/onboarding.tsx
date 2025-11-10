import { createRoute } from '@tanstack/react-router'
import { rootRoute } from './__root'
import { OnboardingWizard } from '../features/onboarding/OnboardingWizard'

/**
 * Onboarding Route (/onboarding)
 *
 * Public onboarding wizard route:
 * - Single Responsibility: Onboarding wizard route config
 * - Public: No authentication required for signup/verification steps
 * - Component: OnboardingWizard
 * - Multi-step wizard flow
 */

export const onboardingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/onboarding',
  component: OnboardingWizard,
})
