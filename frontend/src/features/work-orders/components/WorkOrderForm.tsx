/**
 * WorkOrderForm Component
 *
 * Form for creating and editing work orders with validation
 */
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import type { CreateWorkOrderDTO, UpdateWorkOrderDTO, WorkOrder } from '../types/workOrder.types'
import './WorkOrderForm.css'

export interface WorkOrderFormProps {
  mode: 'create' | 'edit'
  initialData?: WorkOrder
  onSubmit: (data: CreateWorkOrderDTO | UpdateWorkOrderDTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const WorkOrderForm = ({
  mode,
  initialData,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: WorkOrderFormProps) => {
  const [formData, setFormData] = useState({
    material_id: initialData?.material_id ?? 0,
    order_type: initialData?.order_type ?? ('PRODUCTION' as const),
    planned_quantity: initialData?.planned_quantity ?? 0,
    start_date_planned: initialData?.start_date_planned ?? '',
    end_date_planned: initialData?.end_date_planned ?? '',
    priority: initialData?.priority ?? 5,
    actual_quantity: initialData?.actual_quantity ?? 0,
    order_status: initialData?.order_status ?? ('PLANNED' as const),
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (mode === 'create') {
      if (!formData.material_id) {
        newErrors.material_id = 'Material ID is required'
      }
      if (!formData.planned_quantity || formData.planned_quantity <= 0) {
        newErrors.planned_quantity = 'Quantity must be positive'
      }
    } else {
      // Edit mode validation
      if (formData.actual_quantity && formData.actual_quantity < 0) {
        newErrors.actual_quantity = 'Actual quantity cannot be negative'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    if (mode === 'create') {
      const createData: CreateWorkOrderDTO = {
        material_id: formData.material_id,
        order_type: formData.order_type,
        planned_quantity: formData.planned_quantity,
        start_date_planned: formData.start_date_planned || undefined,
        end_date_planned: formData.end_date_planned || undefined,
        priority: formData.priority,
      }
      await onSubmit(createData)
    } else {
      // For update mode, only send changed fields
      const updateData: UpdateWorkOrderDTO = {}

      if (formData.planned_quantity !== initialData?.planned_quantity) {
        updateData.planned_quantity = formData.planned_quantity
      }
      if (formData.actual_quantity !== initialData?.actual_quantity) {
        updateData.actual_quantity = formData.actual_quantity
      }
      if (formData.priority !== initialData?.priority) {
        updateData.priority = formData.priority
      }
      if (formData.order_status !== initialData?.order_status) {
        updateData.order_status = formData.order_status
      }

      await onSubmit(updateData)
    }
  }

  const handleChange = (field: string) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    let value: string | number = e.target.value
    if (e.target.type === 'number') {
      const numValue = e.target.value === '' ? 0 : parseFloat(e.target.value)
      value = numValue
    }
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <Card variant="elevated" padding="lg">
      <div className="work-order-form">
        <form onSubmit={handleSubmit} className="work-order-form__form">
          <FormField
            label="Material ID"
            type="number"
            value={formData.material_id.toString()}
            onChange={handleChange('material_id')}
            error={errors.material_id}
            required
            disabled={isLoading || mode === 'edit'}
          />

          <div className="work-order-form__field">
            <label className="work-order-form__label">
              Order Type <span className="work-order-form__required">*</span>
            </label>
            <select
              className="work-order-form__select"
              value={formData.order_type}
              onChange={handleChange('order_type')}
              disabled={isLoading}
              required
            >
              <option value="PRODUCTION">Production</option>
              <option value="REWORK">Rework</option>
              <option value="ASSEMBLY">Assembly</option>
            </select>
          </div>

          <FormField
            label="Planned Quantity"
            type="number"
            value={formData.planned_quantity.toString()}
            onChange={handleChange('planned_quantity')}
            error={errors.planned_quantity}
            required
            disabled={isLoading}
          />

          {mode === 'edit' && (
            <FormField
              label="Actual Quantity"
              type="number"
              value={formData.actual_quantity.toString()}
              onChange={handleChange('actual_quantity')}
              disabled={isLoading}
            />
          )}

          <FormField
            label="Priority (1-10)"
            type="number"
            value={formData.priority.toString()}
            onChange={handleChange('priority')}
            disabled={isLoading}
            min={1}
            max={10}
          />

          <FormField
            label="Start Date Planned"
            type="date"
            value={formData.start_date_planned}
            onChange={handleChange('start_date_planned')}
            disabled={isLoading}
          />

          <FormField
            label="End Date Planned"
            type="date"
            value={formData.end_date_planned}
            onChange={handleChange('end_date_planned')}
            disabled={isLoading}
          />

          {error && (
            <div className="work-order-form__error-message" role="alert">
              {error}
            </div>
          )}

          <div className="work-order-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              {mode === 'create' ? 'Create Work Order' : 'Update Work Order'}
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
