/**
 * TeamInvitationsStep Component
 *
 * Fifth and final step of onboarding wizard - team member invitations
 */
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useInviteTeam, type InviteTeamRequest, type TeamRole } from '@/hooks/useOnboarding'
import { useOnboardingStore } from '../store/onboardingStore'
import { cn } from '@/lib/utils'
import { Users, Plus, X } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'

const invitationSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  role: z.enum(['admin', 'operator', 'viewer', 'custom']),
  role_description: z.string().optional(),
})

const teamInvitationsSchema = z.object({
  invitations: z
    .array(invitationSchema)
    .min(1, 'Add at least one team member or skip this step'),
})

type TeamInvitationsFormData = z.infer<typeof teamInvitationsSchema>

const ROLE_OPTIONS: { value: TeamRole; label: string; description: string }[] = [
  {
    value: 'admin',
    label: 'Admin',
    description: 'Full access to all features and settings',
  },
  {
    value: 'operator',
    label: 'Operator',
    description: 'Can manage production and operations',
  },
  {
    value: 'viewer',
    label: 'Viewer',
    description: 'Read-only access to data',
  },
  {
    value: 'custom',
    label: 'Custom',
    description: 'Define custom role permissions',
  },
]

export function TeamInvitationsStep() {
  const navigate = useNavigate()
  const { mutate: inviteTeam, isPending, error } = useInviteTeam()
  const { markStepCompleted } = useOnboardingStore()

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<TeamInvitationsFormData>({
    resolver: zodResolver(teamInvitationsSchema),
    defaultValues: {
      invitations: [{ email: '', role: 'operator' }],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'invitations',
  })

  const onSubmit = async (data: TeamInvitationsFormData) => {
    const request: InviteTeamRequest = {
      invitations: data.invitations.map((inv) => ({
        email: inv.email,
        role: inv.role,
        role_description: inv.role_description || undefined,
      })),
    }

    inviteTeam(request, {
      onSuccess: () => {
        markStepCompleted('team-invitations')
        navigate({ to: '/' })
      },
    })
  }

  const handleSkip = () => {
    markStepCompleted('team-invitations')
    navigate({ to: '/' })
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Users className="w-8 h-8 text-primary" />
          </div>
        </div>
        <CardTitle className="text-center">Invite Your Team</CardTitle>
        <CardDescription className="text-center">
          Add team members to collaborate on your projects
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Invitations List */}
          <div className="space-y-4">
            {fields.map((field, index) => (
              <div
                key={field.id}
                className="flex gap-4 items-start p-4 rounded-lg border bg-card"
              >
                <div className="flex-1 space-y-4">
                  {/* Email */}
                  <div className="space-y-2">
                    <Label htmlFor={`invitations.${index}.email`}>
                      Email<span className="text-destructive ml-1">*</span>
                    </Label>
                    <Input
                      id={`invitations.${index}.email`}
                      type="email"
                      placeholder="teammate@example.com"
                      {...register(`invitations.${index}.email`)}
                      disabled={isPending}
                      aria-invalid={!!errors.invitations?.[index]?.email}
                      className={cn(
                        errors.invitations?.[index]?.email && 'border-destructive'
                      )}
                    />
                    {errors.invitations?.[index]?.email && (
                      <p className="text-sm text-destructive">
                        {errors.invitations[index]?.email?.message}
                      </p>
                    )}
                  </div>

                  {/* Role */}
                  <div className="space-y-2">
                    <Label htmlFor={`invitations.${index}.role`}>
                      Role<span className="text-destructive ml-1">*</span>
                    </Label>
                    <Select
                      value={watch(`invitations.${index}.role`)}
                      onValueChange={(value) =>
                        setValue(`invitations.${index}.role`, value as TeamRole)
                      }
                      disabled={isPending}
                    >
                      <SelectTrigger id={`invitations.${index}.role`}>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLE_OPTIONS.map((role) => (
                          <SelectItem key={role.value} value={role.value}>
                            <div className="flex flex-col">
                              <span className="font-medium">{role.label}</span>
                              <span className="text-xs text-muted-foreground">
                                {role.description}
                              </span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Custom Role Description */}
                  {watch(`invitations.${index}.role`) === 'custom' && (
                    <div className="space-y-2">
                      <Label htmlFor={`invitations.${index}.role_description`}>
                        Role Description
                      </Label>
                      <Input
                        id={`invitations.${index}.role_description`}
                        type="text"
                        placeholder="Describe the custom role"
                        {...register(`invitations.${index}.role_description`)}
                        disabled={isPending}
                      />
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                {fields.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(index)}
                    disabled={isPending}
                    className="mt-8"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>

          {/* Add Another Button */}
          <Button
            type="button"
            variant="outline"
            onClick={() => append({ email: '', role: 'operator' })}
            disabled={isPending}
            className="w-full"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Another Team Member
          </Button>

          {/* API Error */}
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">
                {error instanceof Error
                  ? error.message
                  : 'Failed to send invitations. Please try again.'}
              </p>
            </div>
          )}

          {/* Form Errors */}
          {errors.invitations && !Array.isArray(errors.invitations) && (
            <p className="text-sm text-destructive">{errors.invitations.message}</p>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleSkip}
              disabled={isPending}
              className="flex-1"
            >
              Skip for Now
            </Button>
            <Button type="submit" disabled={isPending} className="flex-1">
              {isPending ? 'Sending Invitations...' : 'Send Invitations'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
