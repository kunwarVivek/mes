/**
 * NCRForm Component
 *
 * Form for creating NCRs with Zod validation
 */
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import { createNCRSchema } from '../schemas/ncr.schema'
import type { CreateNCRDTO } from '../types/quality.types'
import { ZodError } from 'zod'
import './NCRForm.css'

export interface NCRFormProps {
  defaultWorkOrderId?: number
  defaultMaterialId?: number
  defaultReporterId?: number
  onSubmit: (data: CreateNCRDTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const NCRForm = ({
  defaultWorkOrderId,
  defaultMaterialId,
  defaultReporterId = 1,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: NCRFormProps) => {
  const [formData, setFormData] = useState<Partial<CreateNCRDTO>>({
    ncr_number: '',
    work_order_id: defaultWorkOrderId ?? 0,
    material_id: defaultMaterialId ?? 0,
    defect_type: 'DIMENSIONAL',
    defect_description: '',
    quantity_defective: 0,
    reported_by_user_id: defaultReporterId,
    attachment_urls: [],
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      createNCRSchema.parse(formData)
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

    await onSubmit(formData as CreateNCRDTO)
  }

  const handleChange = (field: keyof CreateNCRDTO) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <Card variant="elevated" padding="lg">
      <div className="ncr-form">
        <form onSubmit={handleSubmit} className="ncr-form__form">
          <div className="ncr-form__section">
            <h3 className="ncr-form__section-title">NCR Information</h3>

            <FormField
              label="NCR Number"
              type="text"
              value={formData.ncr_number}
              onChange={handleChange('ncr_number')}
              error={errors.ncr_number}
              helperText="Unique NCR identifier, max 50 characters"
              required
              disabled={isLoading}
            />

            <FormField
              label="Work Order ID"
              type="number"
              value={formData.work_order_id?.toString() ?? ''}
              onChange={handleChange('work_order_id')}
              error={errors.work_order_id}
              required
              disabled={isLoading}
            />

            <FormField
              label="Material ID"
              type="number"
              value={formData.material_id?.toString() ?? ''}
              onChange={handleChange('material_id')}
              error={errors.material_id}
              required
              disabled={isLoading}
            />
          </div>

          <div className="ncr-form__section">
            <h3 className="ncr-form__section-title">Defect Details</h3>

            <div className="ncr-form__field">
              <label className="ncr-form__label" htmlFor="defect-type">
                Defect Type <span className="ncr-form__required">*</span>
              </label>
              <select
                id="defect-type"
                className="ncr-form__select"
                value={formData.defect_type}
                onChange={handleChange('defect_type')}
                disabled={isLoading}
                required
              >
                <option value="DIMENSIONAL">Dimensional</option>
                <option value="VISUAL">Visual</option>
                <option value="FUNCTIONAL">Functional</option>
                <option value="MATERIAL">Material</option>
                <option value="OTHER">Other</option>
              </select>
              {errors.defect_type && (
                <span className="ncr-form__error">{errors.defect_type}</span>
              )}
            </div>

            <div className="ncr-form__field">
              <label className="ncr-form__label" htmlFor="defect-description">
                Defect Description <span className="ncr-form__required">*</span>
              </label>
              <textarea
                id="defect-description"
                className="ncr-form__textarea"
                value={formData.defect_description}
                onChange={handleChange('defect_description')}
                disabled={isLoading}
                rows={4}
                maxLength={500}
                placeholder="Describe the defect in detail (min 10 characters)"
                required
              />
              <div className="ncr-form__helper">
                {formData.defect_description?.length || 0} / 500 characters (min 10)
              </div>
              {errors.defect_description && (
                <span className="ncr-form__error">{errors.defect_description}</span>
              )}
            </div>

            <FormField
              label="Quantity Defective"
              type="number"
              value={formData.quantity_defective?.toString() ?? ''}
              onChange={handleChange('quantity_defective')}
              error={errors.quantity_defective}
              helperText="Number of defective units"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="ncr-form__error-message" role="alert">
              {error}
            </div>
          )}

          <div className="ncr-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              Create NCR
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
