/**
 * ProductionPlanForm Component
 *
 * Form for creating and editing production plans with Zod validation
 */
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import { createProductionPlanSchema, updateProductionPlanSchema } from '../schemas/production.schema'
import type { CreateProductionPlanDTO, UpdateProductionPlanDTO, ProductionPlan } from '../types/production.types'
import { ZodError } from 'zod'
import './ProductionPlanForm.css'

export interface ProductionPlanFormProps {
  mode: 'create' | 'edit'
  initialData?: ProductionPlan
  onSubmit: (data: CreateProductionPlanDTO | UpdateProductionPlanDTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const ProductionPlanForm = ({
  mode,
  initialData,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: ProductionPlanFormProps) => {
  const [formData, setFormData] = useState<Partial<CreateProductionPlanDTO>>({
    plan_code: initialData?.plan_code ?? '',
    plan_name: initialData?.plan_name ?? '',
    start_date: initialData?.start_date ?? '',
    end_date: initialData?.end_date ?? '',
    status: initialData?.status ?? 'DRAFT',
    notes: initialData?.notes ?? '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      const schema = mode === 'create' ? createProductionPlanSchema : updateProductionPlanSchema
      schema.parse(formData)
      setErrors({})
      return true
    } catch (e) {
      if (e instanceof ZodError) {
        const newErrors: Record<string, string> = {}
        e.errors.forEach((err) => {
          const path = err.path.join('.')
          newErrors[path] = err.message
        })
        setErrors(newErrors)
      }
      return false
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    if (mode === 'create') {
      await onSubmit(formData as CreateProductionPlanDTO)
    } else {
      // For update mode, only send changed fields
      const updateData: UpdateProductionPlanDTO = {}
      if (formData.plan_name !== initialData?.plan_name) {
        updateData.plan_name = formData.plan_name
      }
      if (formData.start_date !== initialData?.start_date) {
        updateData.start_date = formData.start_date
      }
      if (formData.end_date !== initialData?.end_date) {
        updateData.end_date = formData.end_date
      }
      if (formData.status !== initialData?.status) {
        updateData.status = formData.status
      }
      if (formData.notes !== initialData?.notes) {
        updateData.notes = formData.notes
      }

      await onSubmit(updateData)
    }
  }

  const handleChange = (field: keyof CreateProductionPlanDTO) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const value = e.target.value
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <Card variant="elevated" padding="lg">
      <div className="production-plan-form">
        <form onSubmit={handleSubmit} className="production-plan-form__form">
          <div className="production-plan-form__section">
            <h3 className="production-plan-form__section-title">Basic Information</h3>

            <FormField
              label="Plan Code"
              type="text"
              value={formData.plan_code}
              onChange={handleChange('plan_code')}
              error={errors.plan_code}
              helperText="Unique plan identifier, max 20 characters"
              required
              disabled={isLoading || mode === 'edit'}
            />

            <FormField
              label="Plan Name"
              type="text"
              value={formData.plan_name}
              onChange={handleChange('plan_name')}
              error={errors.plan_name}
              required
              disabled={isLoading}
            />
          </div>

          <div className="production-plan-form__section">
            <h3 className="production-plan-form__section-title">Planning Period</h3>

            <FormField
              label="Start Date"
              type="date"
              value={formData.start_date}
              onChange={handleChange('start_date')}
              error={errors.start_date}
              required
              disabled={isLoading}
            />

            <FormField
              label="End Date"
              type="date"
              value={formData.end_date}
              onChange={handleChange('end_date')}
              error={errors.end_date}
              required
              disabled={isLoading}
            />
          </div>

          <div className="production-plan-form__section">
            <h3 className="production-plan-form__section-title">Status & Notes</h3>

            <div className="production-plan-form__field">
              <label className="production-plan-form__label" htmlFor="status">
                Status <span className="production-plan-form__required">*</span>
              </label>
              <select
                id="status"
                className="production-plan-form__select"
                value={formData.status}
                onChange={handleChange('status')}
                disabled={isLoading}
                required
              >
                <option value="DRAFT">DRAFT</option>
                <option value="APPROVED">APPROVED</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
              {errors.status && (
                <span className="production-plan-form__error">{errors.status}</span>
              )}
            </div>

            <div className="production-plan-form__field">
              <label className="production-plan-form__label" htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                className="production-plan-form__textarea"
                value={formData.notes}
                onChange={handleChange('notes')}
                disabled={isLoading}
                rows={4}
                maxLength={1000}
              />
              {errors.notes && (
                <span className="production-plan-form__error">{errors.notes}</span>
              )}
            </div>
          </div>

          {error && (
            <div className="production-plan-form__error-message" role="alert">
              {error}
            </div>
          )}

          <div className="production-plan-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              {mode === 'create' ? 'Create Production Plan' : 'Update Production Plan'}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="ghost"
                onClick={onCancel}
                disabled={isLoading}
                fullWidth
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </div>
    </Card>
  )
}
