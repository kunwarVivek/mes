/**
 * SignupStep Component
 *
 * First step of onboarding wizard - user signup with email verification
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSignup, type SignupRequest } from '@/hooks/useOnboarding'
import { useOnboardingStore } from '../store/onboardingStore'
import { cn } from '@/lib/utils'
import { Mail } from 'lucide-react'

const signupSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})

type SignupFormData = z.infer<typeof signupSchema>

export function SignupStep() {
  const { mutate: signup, isPending, error } = useSignup()
  const { setEmail, setCurrentStep, markStepCompleted } = useOnboardingStore()
  const [isSuccess, setIsSuccess] = useState(false)
  const [verificationEmail, setVerificationEmail] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  })

  const onSubmit = async (data: SignupFormData) => {
    const request: SignupRequest = {
      email: data.email,
      password: data.password,
    }

    signup(request, {
      onSuccess: (response) => {
        setEmail(data.email)
        setVerificationEmail(data.email)
        markStepCompleted('signup')
        setIsSuccess(true)
      },
    })
  }

  if (isSuccess) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Mail className="w-8 h-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-center">Check Your Email</CardTitle>
          <CardDescription className="text-center">
            We've sent a verification link to <strong>{verificationEmail}</strong>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground text-center">
              Click the verification link in your email to continue setting up your account.
            </p>

            {/* For testing - show verification link */}
            <div className="p-4 rounded-lg bg-muted">
              <p className="text-xs font-semibold text-muted-foreground mb-2">
                For Testing:
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setCurrentStep('email-verification')
                }}
                className="w-full"
              >
                Simulate Email Verification
              </Button>
            </div>

            <div className="text-center text-sm text-muted-foreground">
              <p>Didn't receive the email?</p>
              <Button
                variant="link"
                size="sm"
                onClick={() => setIsSuccess(false)}
                className="text-primary"
              >
                Try again
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Create Your Account</CardTitle>
        <CardDescription>
          Enter your email and password to get started
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email">
              Email<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              {...register('email')}
              disabled={isPending}
              aria-invalid={!!errors.email}
              className={cn(errors.email && 'border-destructive')}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          {/* Password */}
          <div className="space-y-2">
            <Label htmlFor="password">
              Password<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="Create a strong password"
              {...register('password')}
              disabled={isPending}
              aria-invalid={!!errors.password}
              className={cn(errors.password && 'border-destructive')}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              At least 8 characters with uppercase, lowercase, number, and special character
            </p>
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">
              Confirm Password<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              {...register('confirmPassword')}
              disabled={isPending}
              aria-invalid={!!errors.confirmPassword}
              className={cn(errors.confirmPassword && 'border-destructive')}
            />
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          {/* API Error */}
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">
                {error instanceof Error ? error.message : 'Signup failed. Please try again.'}
              </p>
            </div>
          )}

          {/* Submit */}
          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
