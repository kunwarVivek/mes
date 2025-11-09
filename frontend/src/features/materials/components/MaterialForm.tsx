/**
 * MaterialForm Component
 *
 * Form for creating and editing materials with Zod validation
 */
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import { createMaterialSchema, updateMaterialSchema } from '../schemas/material.schema'
import type { CreateMaterialDTO, UpdateMaterialDTO, Material } from '../types/material.types'
import { ZodError } from 'zod'
import './MaterialForm.css'

export interface MaterialFormProps {
  mode: 'create' | 'edit'
  initialData?: Material
  defaultOrgId?: number
  defaultPlantId?: number
  onSubmit: (data: CreateMaterialDTO | UpdateMaterialDTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const MaterialForm = ({
  mode,
  initialData,
  defaultOrgId = 1,
  defaultPlantId = 1,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: MaterialFormProps) => {
  const [formData, setFormData] = useState<Partial<CreateMaterialDTO>>({
    organization_id: initialData?.organization_id ?? defaultOrgId,
    plant_id: initialData?.plant_id ?? defaultPlantId,
    material_number: initialData?.material_number ?? '',
    material_name: initialData?.material_name ?? '',
    description: initialData?.description ?? '',
    material_category_id: initialData?.material_category_id ?? 0,
    base_uom_id: initialData?.base_uom_id ?? 0,
    procurement_type: initialData?.procurement_type ?? 'PURCHASE',
    mrp_type: initialData?.mrp_type ?? 'MRP',
    safety_stock: initialData?.safety_stock ?? 0,
    reorder_point: initialData?.reorder_point ?? 0,
    lot_size: initialData?.lot_size ?? 1,
    lead_time_days: initialData?.lead_time_days ?? 0,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      const schema = mode === 'create' ? createMaterialSchema : updateMaterialSchema
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
      await onSubmit(formData as CreateMaterialDTO)
    } else {
      // For update mode, only send changed fields
      const updateData: UpdateMaterialDTO = {}
      if (formData.material_name !== initialData?.material_name) {
        updateData.material_name = formData.material_name
      }
      if (formData.description !== initialData?.description) {
        updateData.description = formData.description
      }
      if (formData.material_category_id !== initialData?.material_category_id) {
        updateData.material_category_id = formData.material_category_id
      }
      if (formData.procurement_type !== initialData?.procurement_type) {
        updateData.procurement_type = formData.procurement_type
      }
      if (formData.mrp_type !== initialData?.mrp_type) {
        updateData.mrp_type = formData.mrp_type
      }
      if (formData.safety_stock !== initialData?.safety_stock) {
        updateData.safety_stock = formData.safety_stock
      }
      if (formData.reorder_point !== initialData?.reorder_point) {
        updateData.reorder_point = formData.reorder_point
      }
      if (formData.lot_size !== initialData?.lot_size) {
        updateData.lot_size = formData.lot_size
      }
      if (formData.lead_time_days !== initialData?.lead_time_days) {
        updateData.lead_time_days = formData.lead_time_days
      }

      await onSubmit(updateData)
    }
  }

  const handleChange = (field: keyof CreateMaterialDTO) => (
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
      <div className="material-form">
        <form onSubmit={handleSubmit} className="material-form__form">
          <div className="material-form__section">
            <h3 className="material-form__section-title">Basic Information</h3>

            <FormField
              label="Material Number"
              type="text"
              value={formData.material_number}
              onChange={handleChange('material_number')}
              error={errors.material_number}
              helperText="Uppercase alphanumeric only, max 10 characters"
              required
              disabled={isLoading || mode === 'edit'}
            />

            <FormField
              label="Material Name"
              type="text"
              value={formData.material_name}
              onChange={handleChange('material_name')}
              error={errors.material_name}
              required
              disabled={isLoading}
            />

            <div className="material-form__field">
              <label className="material-form__label">Description</label>
              <textarea
                className="material-form__textarea"
                value={formData.description}
                onChange={handleChange('description')}
                disabled={isLoading}
                rows={3}
                maxLength={500}
              />
              {errors.description && (
                <span className="material-form__error">{errors.description}</span>
              )}
            </div>
          </div>

          <div className="material-form__section">
            <h3 className="material-form__section-title">Classification</h3>

            <FormField
              label="Material Category ID"
              type="number"
              value={formData.material_category_id?.toString() ?? ''}
              onChange={handleChange('material_category_id')}
              error={errors.material_category_id}
              required
              disabled={isLoading}
            />

            <FormField
              label="Base UOM ID"
              type="number"
              value={formData.base_uom_id?.toString() ?? ''}
              onChange={handleChange('base_uom_id')}
              error={errors.base_uom_id}
              required
              disabled={isLoading}
            />

            <div className="material-form__field">
              <label className="material-form__label">
                Procurement Type <span className="material-form__required">*</span>
              </label>
              <select
                className="material-form__select"
                value={formData.procurement_type}
                onChange={handleChange('procurement_type')}
                disabled={isLoading}
                required
              >
                <option value="PURCHASE">Purchase</option>
                <option value="MANUFACTURE">Manufacture</option>
                <option value="BOTH">Both</option>
              </select>
              {errors.procurement_type && (
                <span className="material-form__error">{errors.procurement_type}</span>
              )}
            </div>

            <div className="material-form__field">
              <label className="material-form__label">
                MRP Type <span className="material-form__required">*</span>
              </label>
              <select
                className="material-form__select"
                value={formData.mrp_type}
                onChange={handleChange('mrp_type')}
                disabled={isLoading}
                required
              >
                <option value="MRP">MRP</option>
                <option value="REORDER">Reorder Point</option>
              </select>
              {errors.mrp_type && (
                <span className="material-form__error">{errors.mrp_type}</span>
              )}
            </div>
          </div>

          <div className="material-form__section">
            <h3 className="material-form__section-title">Planning Parameters</h3>

            <FormField
              label="Safety Stock"
              type="number"
              value={formData.safety_stock?.toString() ?? '0'}
              onChange={handleChange('safety_stock')}
              error={errors.safety_stock}
              disabled={isLoading}
            />

            <FormField
              label="Reorder Point"
              type="number"
              value={formData.reorder_point?.toString() ?? '0'}
              onChange={handleChange('reorder_point')}
              error={errors.reorder_point}
              disabled={isLoading}
            />

            <FormField
              label="Lot Size"
              type="number"
              value={formData.lot_size?.toString() ?? '1'}
              onChange={handleChange('lot_size')}
              error={errors.lot_size}
              disabled={isLoading}
            />

            <FormField
              label="Lead Time (Days)"
              type="number"
              value={formData.lead_time_days?.toString() ?? '0'}
              onChange={handleChange('lead_time_days')}
              error={errors.lead_time_days}
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="material-form__error-message" role="alert">
              {error}
            </div>
          )}

          <div className="material-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              {mode === 'create' ? 'Create Material' : 'Update Material'}
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
