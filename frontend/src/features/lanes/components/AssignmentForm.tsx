/**
 * AssignmentForm Component
 *
 * Create/Edit form for lane assignments with validation
 */
import React, { useState } from 'react'
import { Button, Input, Label, Textarea, Body } from '@/design-system/atoms'
import { useAuthStore } from '@/stores/auth.store'
import type {
  LaneAssignment,
  LaneAssignmentCreateRequest,
  LaneAssignmentUpdateRequest,
} from '../types/lane.types'

export interface AssignmentFormProps {
  assignment?: LaneAssignment | null
  preSelectedLane?: number
  preSelectedDate?: string
  onSubmit: (
    data: LaneAssignmentCreateRequest | LaneAssignmentUpdateRequest
  ) => Promise<void>
  onCancel: () => void
  isLoading: boolean
}

export const AssignmentForm: React.FC<AssignmentFormProps> = ({
  assignment,
  preSelectedLane,
  preSelectedDate,
  onSubmit,
  onCancel,
  isLoading,
}) => {
  const { currentOrg, currentPlant } = useAuthStore()

  const [formData, setFormData] = useState({
    lane_id: assignment?.lane_id || preSelectedLane || 0,
    work_order_id: assignment?.work_order_id || 0,
    project_id: assignment?.project_id || undefined,
    scheduled_start: assignment?.scheduled_start || preSelectedDate || '',
    scheduled_end: assignment?.scheduled_end || preSelectedDate || '',
    allocated_capacity: assignment?.allocated_capacity || '0',
    priority: assignment?.priority || 0,
    status: assignment?.status || 'PLANNED',
    notes: assignment?.notes || '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.lane_id) newErrors.lane_id = 'Lane is required'
    if (!formData.work_order_id) newErrors.work_order_id = 'Work Order is required'
    if (!formData.scheduled_start) newErrors.scheduled_start = 'Start date is required'
    if (!formData.scheduled_end) newErrors.scheduled_end = 'End date is required'

    const capacityNum = parseFloat(formData.allocated_capacity)
    if (isNaN(capacityNum) || capacityNum <= 0)
      newErrors.allocated_capacity = 'Capacity must be greater than 0'

    if (formData.scheduled_end < formData.scheduled_start) {
      newErrors.scheduled_end = 'End date must be on or after start date'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    try {
      if (assignment) {
        // Update mode
        const updateData: LaneAssignmentUpdateRequest = {
          scheduled_start: formData.scheduled_start,
          scheduled_end: formData.scheduled_end,
          allocated_capacity: formData.allocated_capacity,
          priority: formData.priority,
          status: formData.status as any,
          notes: formData.notes || undefined,
        }
        await onSubmit(updateData)
      } else {
        // Create mode
        const createData: LaneAssignmentCreateRequest = {
          organization_id: currentOrg?.id || 0,
          plant_id: currentPlant?.id || 0,
          lane_id: formData.lane_id,
          work_order_id: formData.work_order_id,
          project_id: formData.project_id,
          scheduled_start: formData.scheduled_start,
          scheduled_end: formData.scheduled_end,
          allocated_capacity: formData.allocated_capacity,
          priority: formData.priority,
          notes: formData.notes || undefined,
        }
        await onSubmit(createData)
      }
    } catch (error) {
      console.error('Form submission error:', error)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: name.includes('_id') || name === 'priority'
        ? Number(value)
        : value,
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      <div>
        <Label htmlFor="lane_id">Lane ID</Label>
        <Input
          id="lane_id"
          name="lane_id"
          type="number"
          value={formData.lane_id}
          onChange={handleChange}
          disabled={!!assignment || isLoading}
          aria-invalid={!!errors.lane_id}
        />
        {errors.lane_id && <Body className="text-red-500 text-sm">{errors.lane_id}</Body>}
      </div>

      <div>
        <Label htmlFor="work_order_id">Work Order ID</Label>
        <Input
          id="work_order_id"
          name="work_order_id"
          type="number"
          value={formData.work_order_id}
          onChange={handleChange}
          disabled={!!assignment || isLoading}
          aria-invalid={!!errors.work_order_id}
        />
        {errors.work_order_id && (
          <Body className="text-red-500 text-sm">{errors.work_order_id}</Body>
        )}
      </div>

      <div>
        <Label htmlFor="scheduled_start">Start Date</Label>
        <Input
          id="scheduled_start"
          name="scheduled_start"
          type="date"
          value={formData.scheduled_start}
          onChange={handleChange}
          disabled={isLoading}
          aria-invalid={!!errors.scheduled_start}
        />
        {errors.scheduled_start && (
          <Body className="text-red-500 text-sm">{errors.scheduled_start}</Body>
        )}
      </div>

      <div>
        <Label htmlFor="scheduled_end">End Date</Label>
        <Input
          id="scheduled_end"
          name="scheduled_end"
          type="date"
          value={formData.scheduled_end}
          onChange={handleChange}
          disabled={isLoading}
          aria-invalid={!!errors.scheduled_end}
        />
        {errors.scheduled_end && (
          <Body className="text-red-500 text-sm">{errors.scheduled_end}</Body>
        )}
      </div>

      <div>
        <Label htmlFor="allocated_capacity">Allocated Capacity</Label>
        <Input
          id="allocated_capacity"
          name="allocated_capacity"
          type="number"
          value={formData.allocated_capacity}
          onChange={handleChange}
          disabled={isLoading}
          aria-invalid={!!errors.allocated_capacity}
        />
        {errors.allocated_capacity && (
          <Body className="text-red-500 text-sm">{errors.allocated_capacity}</Body>
        )}
      </div>

      <div>
        <Label htmlFor="priority">Priority</Label>
        <Input
          id="priority"
          name="priority"
          type="number"
          value={formData.priority}
          onChange={handleChange}
          disabled={isLoading}
        />
      </div>

      {assignment && (
        <div>
          <Label htmlFor="status">Status</Label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
            disabled={isLoading}
            className="w-full border border-gray-300 rounded p-2"
          >
            <option value="PLANNED">Planned</option>
            <option value="ACTIVE">Active</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      )}

      <div>
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onValueChange={(value) => setFormData((prev) => ({ ...prev, notes: value }))}
          disabled={isLoading}
          rows={3}
        />
      </div>

      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={isLoading}>
          {isLoading ? 'Saving...' : assignment ? 'Update' : 'Create'}
        </Button>
      </div>
    </form>
  )
}
