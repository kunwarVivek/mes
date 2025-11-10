/**
 * Onboarding Wizard Store
 *
 * Zustand store for managing onboarding wizard state
 */
import { create } from 'zustand'
import type { OnboardingStep, OnboardingState } from '../types'

interface OnboardingStore extends OnboardingState {
  setCurrentStep: (step: OnboardingStep) => void
  markStepCompleted: (step: OnboardingStep) => void
  setEmail: (email: string) => void
  setOrganization: (slug: string, id: number) => void
  setPlant: (id: number) => void
  reset: () => void
}

const initialState: OnboardingState = {
  currentStep: 'signup',
  completedSteps: [],
}

export const useOnboardingStore = create<OnboardingStore>((set) => ({
  ...initialState,

  setCurrentStep: (step) =>
    set((state) => ({
      currentStep: step,
    })),

  markStepCompleted: (step) =>
    set((state) => ({
      completedSteps: state.completedSteps.includes(step)
        ? state.completedSteps
        : [...state.completedSteps, step],
    })),

  setEmail: (email) =>
    set(() => ({
      email,
    })),

  setOrganization: (slug, id) =>
    set(() => ({
      organizationSlug: slug,
      organizationId: id,
    })),

  setPlant: (id) =>
    set(() => ({
      plantId: id,
    })),

  reset: () => set(initialState),
}))
