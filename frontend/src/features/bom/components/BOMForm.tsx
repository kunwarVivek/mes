/**
 * BOMForm Component
 *
 * Form for creating and editing BOMs with Zod validation
 */
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import { createBOMSchema, updateBOMSchema } from '../schemas/bom.schema'
import type { CreateBOMDTO, UpdateBOMDTO, BOM } from '../types/bom.types'
import { ZodError } from 'zod'
import './BOMForm.css'

export interface BOMFormProps {
  mode: 'create' | 'edit'
  initialData?: BOM
  defaultOrgId?: number
  defaultPlantId?: number
  onSubmit: (data: CreateBOMDTO | UpdateBOMDTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const BOMForm = ({
  mode,
  initialData,
  defaultOrgId = 1,
  defaultPlantId = 1,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: BOMFormProps) => {
  const [formData, setFormData] = useState<Partial<CreateBOMDTO>>({
    bom_number: initialData?.bom_number ?? '',
    material_id: initialData?.material_id ?? 0,
    bom_name: initialData?.bom_name ?? '',
    bom_type: initialData?.bom_type ?? 'PRODUCTION',
    base_quantity: initialData?.base_quantity ?? 1,
    unit_of_measure_id: initialData?.unit_of_measure_id ?? 0,
    effective_start_date: initialData?.effective_start_date ?? '',
    effective_end_date: initialData?.effective_end_date ?? '',
    bom_version: initialData?.bom_version ?? 1,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      if (mode === 'create') {
        createBOMSchema.parse(formData)
      } else {
        // In edit mode, only validate the fields that are in the update schema
        const updateData: Partial<UpdateBOMDTO> = {}
        if (formData.bom_name !== undefined) updateData.bom_name = formData.bom_name
        if (formData.bom_type !== undefined) updateData.bom_type = formData.bom_type
        if (formData.base_quantity !== undefined) updateData.base_quantity = formData.base_quantity
        if (formData.effective_start_date !== undefined)
          updateData.effective_start_date = formData.effective_start_date
        if (formData.effective_end_date !== undefined)
          updateData.effective_end_date = formData.effective_end_date
        updateBOMSchema.parse(updateData)
      }
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
      await onSubmit(formData as CreateBOMDTO)
    } else {
      // For update mode, only send changed fields
      const updateData: UpdateBOMDTO = {}
      if (formData.bom_name !== initialData?.bom_name) {
        updateData.bom_name = formData.bom_name
      }
      if (formData.bom_type !== initialData?.bom_type) {
        updateData.bom_type = formData.bom_type
      }
      if (formData.base_quantity !== initialData?.base_quantity) {
        updateData.base_quantity = formData.base_quantity
      }
      // Only include dates if they are not empty and different from initial
      if (
        formData.effective_start_date &&
        formData.effective_start_date !== (initialData?.effective_start_date ?? '')
      ) {
        updateData.effective_start_date = formData.effective_start_date
      }
      if (
        formData.effective_end_date &&
        formData.effective_end_date !== (initialData?.effective_end_date ?? '')
      ) {
        updateData.effective_end_date = formData.effective_end_date
      }

      await onSubmit(updateData)
    }
  }

  const handleChange = (field: keyof CreateBOMDTO) => (
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
      <div className="bom-form">
        <form onSubmit={handleSubmit} className="bom-form__form">
          <div className="bom-form__section">
            <h3 className="bom-form__section-title">Basic Information</h3>

            <FormField
              label="BOM Number"
              type="text"
              value={formData.bom_number}
              onChange={handleChange('bom_number')}
              error={errors.bom_number}
              helperText="Max 50 characters"
              required
              disabled={isLoading || mode === 'edit'}
            />

            <FormField
              label="BOM Name"
              type="text"
              value={formData.bom_name}
              onChange={handleChange('bom_name')}
              error={errors.bom_name}
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

            <div className="bom-form__field">
              <label className="bom-form__label">
                BOM Type <span className="bom-form__required">*</span>
              </label>
              <select
                className="bom-form__select"
                value={formData.bom_type}
                onChange={handleChange('bom_type')}
                disabled={isLoading}
                required
              >
                <option value="PRODUCTION">Production</option>
                <option value="ENGINEERING">Engineering</option>
                <option value="PLANNING">Planning</option>
              </select>
              {errors.bom_type && <span className="bom-form__error">{errors.bom_type}</span>}
            </div>
          </div>

          <div className="bom-form__section">
            <h3 className="bom-form__section-title">Quantity & UOM</h3>

            <FormField
              label="Base Quantity"
              type="number"
              value={formData.base_quantity?.toString() ?? '1'}
              onChange={handleChange('base_quantity')}
              error={errors.base_quantity}
              required
              disabled={isLoading}
            />

            <FormField
              label="Unit of Measure ID"
              type="number"
              value={formData.unit_of_measure_id?.toString() ?? ''}
              onChange={handleChange('unit_of_measure_id')}
              error={errors.unit_of_measure_id}
              required
              disabled={isLoading}
            />
          </div>

          <div className="bom-form__section">
            <h3 className="bom-form__section-title">Effectivity</h3>

            <FormField
              label="Effective Start Date"
              type="date"
              value={formData.effective_start_date ?? ''}
              onChange={handleChange('effective_start_date')}
              error={errors.effective_start_date}
              disabled={isLoading}
            />

            <FormField
              label="Effective End Date"
              type="date"
              value={formData.effective_end_date ?? ''}
              onChange={handleChange('effective_end_date')}
              error={errors.effective_end_date}
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="bom-form__error-message" role="alert">
              {error}
            </div>
          )}

          <div className="bom-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              {mode === 'create' ? 'Create BOM' : 'Update BOM'}
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
