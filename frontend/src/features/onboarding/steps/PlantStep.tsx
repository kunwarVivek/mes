/**
 * PlantStep Component
 *
 * Fourth step of onboarding wizard - plant creation
 */
import { useForm } from 'react-hook-form'
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
import { useCreatePlant, type CreatePlantRequest } from '@/hooks/useOnboarding'
import { useOnboardingStore } from '../store/onboardingStore'
import { cn } from '@/lib/utils'
import { Factory } from 'lucide-react'

// Common IANA timezones
const TIMEZONES = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Phoenix', label: 'Arizona Time (MST)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HST)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEDT/AEST)' },
]

const plantSchema = z.object({
  plant_name: z
    .string()
    .min(2, 'Plant name must be at least 2 characters')
    .max(100, 'Plant name must be less than 100 characters'),
  address: z.string().max(255, 'Address must be less than 255 characters').optional(),
  timezone: z.string().optional(),
})

type PlantFormData = z.infer<typeof plantSchema>

export function PlantStep() {
  const { mutate: createPlant, isPending, error } = useCreatePlant()
  const { setPlant, setCurrentStep, markStepCompleted } = useOnboardingStore()

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<PlantFormData>({
    resolver: zodResolver(plantSchema),
  })

  const selectedTimezone = watch('timezone')

  const onSubmit = async (data: PlantFormData) => {
    const request: CreatePlantRequest = {
      plant_name: data.plant_name,
      address: data.address || undefined,
      timezone: data.timezone || undefined,
    }

    createPlant(request, {
      onSuccess: (response) => {
        setPlant(response.plant_id)
        markStepCompleted('plant')
        setCurrentStep('team-invitations')
      },
    })
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Factory className="w-8 h-8 text-primary" />
          </div>
        </div>
        <CardTitle className="text-center">Create Your First Plant</CardTitle>
        <CardDescription className="text-center">
          Set up your manufacturing plant or facility
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Plant Name */}
          <div className="space-y-2">
            <Label htmlFor="plant_name">
              Plant Name<span className="text-destructive ml-1">*</span>
            </Label>
            <Input
              id="plant_name"
              type="text"
              placeholder="Manufacturing Plant 1"
              {...register('plant_name')}
              disabled={isPending}
              aria-invalid={!!errors.plant_name}
              className={cn(errors.plant_name && 'border-destructive')}
            />
            {errors.plant_name && (
              <p className="text-sm text-destructive">{errors.plant_name.message}</p>
            )}
          </div>

          {/* Address */}
          <div className="space-y-2">
            <Label htmlFor="address">Address (Optional)</Label>
            <Input
              id="address"
              type="text"
              placeholder="123 Factory St, City, State, ZIP"
              {...register('address')}
              disabled={isPending}
              aria-invalid={!!errors.address}
              className={cn(errors.address && 'border-destructive')}
            />
            {errors.address && (
              <p className="text-sm text-destructive">{errors.address.message}</p>
            )}
          </div>

          {/* Timezone */}
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone (Optional)</Label>
            <Select
              value={selectedTimezone}
              onValueChange={(value) => setValue('timezone', value)}
              disabled={isPending}
            >
              <SelectTrigger id="timezone">
                <SelectValue placeholder="Select timezone" />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Set the timezone for your plant's operations
            </p>
          </div>

          {/* API Error */}
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive">
                {error instanceof Error
                  ? error.message
                  : 'Failed to create plant. Please try again.'}
              </p>
            </div>
          )}

          {/* Submit */}
          <Button type="submit" disabled={isPending} className="w-full">
            {isPending ? 'Creating Plant...' : 'Create Plant'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
