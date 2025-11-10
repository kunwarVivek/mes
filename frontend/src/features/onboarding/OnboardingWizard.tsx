/**
 * OnboardingWizard Component
 *
 * Main wizard component that orchestrates the onboarding flow
 * - Manages step routing
 * - Shows progress indicator
 * - Renders current step component
 */
import { useOnboardingStore } from './store/onboardingStore'
import { ProgressStepper } from './components/ProgressStepper'
import { SignupStep } from './steps/SignupStep'
import { EmailVerificationStep } from './steps/EmailVerificationStep'
import { OrganizationStep } from './steps/OrganizationStep'
import { PlantStep } from './steps/PlantStep'
import { TeamInvitationsStep } from './steps/TeamInvitationsStep'

export function OnboardingWizard() {
  const { currentStep, completedSteps } = useOnboardingStore()

  // Render current step
  const renderStep = () => {
    switch (currentStep) {
      case 'signup':
        return <SignupStep />
      case 'email-verification':
        return <EmailVerificationStep />
      case 'organization':
        return <OrganizationStep />
      case 'plant':
        return <PlantStep />
      case 'team-invitations':
        return <TeamInvitationsStep />
      default:
        return <SignupStep />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Welcome to Unison</h1>
          <p className="text-muted-foreground mt-2">
            Let's get you set up in just a few steps
          </p>
        </div>

        {/* Progress Stepper */}
        <ProgressStepper currentStep={currentStep} completedSteps={completedSteps} />

        {/* Current Step */}
        <div className="mt-8">{renderStep()}</div>
      </div>
    </div>
  )
}
