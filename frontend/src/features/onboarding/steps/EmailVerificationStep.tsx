/**
 * EmailVerificationStep Component
 *
 * Second step of onboarding wizard - email verification
 */
import { useEffect, useState } from 'react'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useVerifyEmail } from '@/hooks/useOnboarding'
import { useOnboardingStore } from '../store/onboardingStore'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

export function EmailVerificationStep() {
  const navigate = useNavigate()
  const searchParams = useSearch({ strict: false })
  const token = (searchParams as any)?.token as string | undefined

  const { mutate: verifyEmail, isPending, error } = useVerifyEmail()
  const { setCurrentStep, markStepCompleted } = useOnboardingStore()
  const [isSuccess, setIsSuccess] = useState(false)

  useEffect(() => {
    // If token exists in URL, automatically verify
    if (token) {
      verifyEmail(
        { token },
        {
          onSuccess: () => {
            markStepCompleted('email-verification')
            setIsSuccess(true)
            // Auto-redirect after 2 seconds
            setTimeout(() => {
              setCurrentStep('organization')
            }, 2000)
          },
        }
      )
    }
  }, [token, verifyEmail, markStepCompleted, setCurrentStep])

  // Manual verification (for testing)
  const handleManualVerify = () => {
    verifyEmail(
      { token: 'test-token-123' },
      {
        onSuccess: () => {
          markStepCompleted('email-verification')
          setIsSuccess(true)
          setTimeout(() => {
            setCurrentStep('organization')
          }, 2000)
        },
      }
    )
  }

  // Success state
  if (isSuccess) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <CardTitle className="text-center">Email Verified!</CardTitle>
          <CardDescription className="text-center">
            Your email has been successfully verified
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center">
            Redirecting to organization setup...
          </p>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
              <XCircle className="w-8 h-8 text-destructive" />
            </div>
          </div>
          <CardTitle className="text-center">Verification Failed</CardTitle>
          <CardDescription className="text-center">
            {error instanceof Error ? error.message : 'Unable to verify your email'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={() => setCurrentStep('signup')}
            className="w-full"
          >
            Back to Signup
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Loading state
  if (isPending) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          </div>
          <CardTitle className="text-center">Verifying Email</CardTitle>
          <CardDescription className="text-center">
            Please wait while we verify your email address
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  // Waiting for verification
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-center">Email Verification</CardTitle>
        <CardDescription className="text-center">
          Click the link in your email to verify your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground text-center">
            We've sent a verification link to your email address. Please check your inbox and
            click the link to continue.
          </p>

          {/* For testing */}
          <div className="p-4 rounded-lg bg-muted">
            <p className="text-xs font-semibold text-muted-foreground mb-2">For Testing:</p>
            <Button variant="outline" onClick={handleManualVerify} className="w-full">
              Verify Email (Test)
            </Button>
          </div>

          <div className="text-center">
            <Button
              variant="link"
              size="sm"
              onClick={() => setCurrentStep('signup')}
              className="text-primary"
            >
              Back to Signup
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
