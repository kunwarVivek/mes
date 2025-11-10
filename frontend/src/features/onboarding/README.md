# Onboarding Wizard

Multi-step onboarding wizard for self-service user registration and organization setup.

## Overview

The onboarding wizard guides new users through a 5-step process:

1. **Signup** - User creates account with email/password
2. **Email Verification** - User verifies email address
3. **Organization Setup** - User creates their organization
4. **Plant Creation** - User sets up their first manufacturing plant
5. **Team Invitations** - User invites team members (optional)

## Architecture

### File Structure

```
/features/onboarding/
├── OnboardingWizard.tsx           # Main wizard component
├── types.ts                       # Shared TypeScript types
├── store/
│   └── onboardingStore.ts        # Zustand state management
├── components/
│   └── ProgressStepper.tsx       # Visual progress indicator
└── steps/
    ├── SignupStep.tsx            # Step 1: Account creation
    ├── EmailVerificationStep.tsx # Step 2: Email verification
    ├── OrganizationStep.tsx      # Step 3: Organization setup
    ├── PlantStep.tsx             # Step 4: Plant creation
    └── TeamInvitationsStep.tsx   # Step 5: Team invitations
```

### Tech Stack

- **React 18** with TypeScript
- **TanStack Router** for navigation
- **React Hook Form** + **Zod** for form validation
- **Zustand** for state management
- **TanStack Query** for API calls
- **Radix UI** for accessible components
- **Tailwind CSS** for styling

## Components

### OnboardingWizard

Main orchestration component that:
- Manages step routing
- Renders progress indicator
- Displays current step component

**Props:** None (uses Zustand store for state)

### ProgressStepper

Visual stepper showing onboarding progress:
- Shows all 5 steps
- Highlights current step
- Marks completed steps with checkmarks
- Responsive design (hides descriptions on mobile)

**Props:**
```typescript
interface ProgressStepperProps {
  currentStep: OnboardingStep
  completedSteps: OnboardingStep[]
}
```

### SignupStep

User account creation form:
- Email validation
- Password complexity requirements (min 8 chars, uppercase, lowercase, number, special char)
- Confirm password matching
- Success state showing verification instructions
- Test button for email verification simulation

**API Hook:** `useSignup()`

### EmailVerificationStep

Email verification handler:
- Auto-verifies if `token` URL parameter present
- Shows loading/success/error states
- Test button for manual verification
- Auto-redirects to next step on success

**API Hook:** `useVerifyEmail()`

### OrganizationStep

Organization creation form:
- Organization name input (2-100 characters)
- Auto-generates slug on backend
- Simple single-field form

**API Hook:** `useSetupOrganization()`

### PlantStep

Manufacturing plant setup form:
- Plant name (required)
- Address (optional)
- Timezone selection (optional, IANA timezones)
- 13 common timezone options

**API Hook:** `useCreatePlant()`

### TeamInvitationsStep

Team member invitation form:
- Dynamic form with add/remove rows
- Email + role selection per invitation
- 4 role options: admin, operator, viewer, custom
- Custom role description field
- "Skip" option to bypass invitations
- Redirects to dashboard on completion

**API Hook:** `useInviteTeam()`

## State Management

### Zustand Store (onboardingStore)

```typescript
interface OnboardingStore {
  // State
  currentStep: OnboardingStep
  completedSteps: OnboardingStep[]
  email?: string
  organizationSlug?: string
  organizationId?: number
  plantId?: number

  // Actions
  setCurrentStep: (step: OnboardingStep) => void
  markStepCompleted: (step: OnboardingStep) => void
  setEmail: (email: string) => void
  setOrganization: (slug: string, id: number) => void
  setPlant: (id: number) => void
  reset: () => void
}
```

## User Flow

```
┌─────────────┐
│   Signup    │ → Email/password → API call → Success message
└─────────────┘                                     ↓
                                            "Check your email"
                                         (Test verification link)
                                                    ↓
┌─────────────┐
│  Verify     │ → Token from URL → API call → Auto-redirect
└─────────────┘                                     ↓
┌─────────────┐
│ Organization│ → Org name → API call → Show slug → Next step
└─────────────┘                                     ↓
┌─────────────┐
│   Plant     │ → Plant details → API call → Next step
└─────────────┘                                     ↓
┌─────────────┐
│    Team     │ → Invitations/Skip → API call → Dashboard
└─────────────┘
```

## API Integration

All API calls use TanStack Query hooks from `/hooks/useOnboarding.ts`:

1. **POST /api/v1/onboarding/signup** (public)
2. **POST /api/v1/onboarding/verify-email** (public)
3. **POST /api/v1/onboarding/organization** (authenticated)
4. **POST /api/v1/onboarding/plant** (authenticated)
5. **POST /api/v1/onboarding/team/invite** (authenticated)

## Form Validation

All forms use Zod schemas for validation:

- **Signup:** Email format, password complexity, password matching
- **Email Verification:** Token presence
- **Organization:** Name length (2-100 chars)
- **Plant:** Name length (2-100 chars), optional fields
- **Team:** Email format, role selection, min 1 invitation

## Error Handling

Each step handles errors:
- **Validation errors:** Inline field-level errors
- **API errors:** Error message display below form
- **Loading states:** Disabled inputs, loading button text
- **Success states:** Visual feedback, auto-redirect

## Testing Features

For development/testing, several components include test helpers:

- **SignupStep:** "Simulate Email Verification" button
- **EmailVerificationStep:** "Verify Email (Test)" button

These bypass email sending for rapid testing.

## Routing

Route registered at `/onboarding`:

```typescript
// /routes/onboarding.tsx
export const onboardingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/onboarding',
  component: OnboardingWizard,
})
```

Route added to router configuration in `/router.tsx`.

## Styling

- **Tailwind CSS:** Utility-first styling
- **Responsive:** Mobile-friendly design
- **Consistent:** Follows existing component patterns
- **Accessible:** Radix UI primitives with proper ARIA attributes

## Usage

Navigate to `/onboarding` to start the wizard:

```typescript
// From login page
navigate({ to: '/onboarding' })

// Or direct URL
http://localhost:5173/onboarding
```

## Future Enhancements

Potential improvements:
- [ ] Email resend functionality
- [ ] Back navigation between steps
- [ ] Save progress and resume later
- [ ] Onboarding progress API integration
- [ ] Email verification token expiration handling
- [ ] Multi-plant creation option
- [ ] Role permission customization UI
- [ ] Invitation link preview
- [ ] Organization logo upload
- [ ] Plant photo upload
