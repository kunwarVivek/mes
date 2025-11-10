/**
 * ProgressStepper Component
 *
 * Visual progress indicator for onboarding wizard
 */
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { OnboardingStep, StepperStep } from '../types'
import { ONBOARDING_STEPS } from '../types'

interface ProgressStepperProps {
  currentStep: OnboardingStep
  completedSteps: OnboardingStep[]
}

export function ProgressStepper({ currentStep, completedSteps }: ProgressStepperProps) {
  const currentIndex = ONBOARDING_STEPS.findIndex((step) => step.id === currentStep)

  return (
    <div className="w-full py-8">
      <div className="flex items-center justify-between">
        {ONBOARDING_STEPS.map((step, index) => {
          const isCompleted = completedSteps.includes(step.id)
          const isCurrent = step.id === currentStep
          const isLast = index === ONBOARDING_STEPS.length - 1

          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                {/* Step Circle */}
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors',
                    {
                      'bg-primary border-primary text-primary-foreground':
                        isCompleted || isCurrent,
                      'bg-background border-muted-foreground/30 text-muted-foreground':
                        !isCompleted && !isCurrent,
                    }
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-semibold">{index + 1}</span>
                  )}
                </div>

                {/* Step Label */}
                <div className="mt-2 text-center">
                  <p
                    className={cn('text-sm font-medium', {
                      'text-foreground': isCurrent,
                      'text-muted-foreground': !isCurrent,
                    })}
                  >
                    {step.label}
                  </p>
                  <p className="text-xs text-muted-foreground hidden sm:block">
                    {step.description}
                  </p>
                </div>
              </div>

              {/* Connector Line */}
              {!isLast && (
                <div
                  className={cn('h-0.5 flex-1 -mt-8', {
                    'bg-primary': index < currentIndex,
                    'bg-muted-foreground/30': index >= currentIndex,
                  })}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
