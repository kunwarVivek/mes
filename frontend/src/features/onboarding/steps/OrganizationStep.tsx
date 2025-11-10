/**
 * OrganizationStep Component
 *
 * Third step of onboarding wizard - organization setup
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useSetupOrganization, type SetupOrganizationRequest } from '@/hooks/useOnboarding'
import { useOnboardingStore } from '../store/onboardingStore'
import { cn } from '@/lib/utils'
import { Building2 } from 'lucide-react'

const organizationSchema = z.object({
  organization_name: z
    .string()
    .min(2, 'Organization name must be at least 2 characters')
    .max(100, 'Organization name must be less than 100 characters'),
})

type OrganizationFormData = z.infer<typeof organizationSchema>

export function OrganizationStep() {
  const { mutate: setupOrganization, isPending, error } = useSetupOrganization()
  const { setOrganization, setCurrentStep, markStepCompleted } = useOnboardingStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrganizationFormData>({
    resolver: zodResolver(organizationSchema),
  })

  const onSubmit = async (data: OrganizationFormData) => {
    const request: SetupOrganizationRequest = {
      organization_name: data.organization_name,
    }

    setupOrganization(request, {
      onSuccess: (response) => {
        setOrganization(response.slug, response.organization_id)
        markStepCompleted('organization')
        setCurrentStep('plant')
      },
    })
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Building2 className="w-8 h-8 text-primary" />
          </div>
        </div>
        <CardTitle className="text-center">Set Up Your Organization</CardTitle>
        <CardDescription className="text-center">
          Create your organization to get started with Unison
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Organization Name */}
          <div className="space-y-2">
            <Label htmlFor="organization_name">
              Organization Name<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="organization_name"
              type="text"
              placeholder="Acme Corporation"
              {...register('organization_name')}
              disabled={isPending}
              aria-invalid={!!errors.organization_name}
              className={cn(errors.organization_name && 'border-destructive')}
            />
            {errors.organization_name && (
              <p className="text-sm text-destructive">{errors.organization_name.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              This will be the name of your organization in Unison
            </p>
          </div>

          {/* API Error */}
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">
                {error instanceof Error
                  ? error.message
                  : 'Failed to create organization. Please try again.'}
              </p>
            </div>
          )}

          {/* Submit */}
          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? 'Creating Organization...' : 'Create Organization'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
