/**
 * Scheduling Schema Tests
 *
 * TDD: Testing Zod validation schemas
 */
import { describe, it, expect } from 'vitest'
import {
  createScheduledOperationSchema,
  updateScheduledOperationSchema,
} from '../schemas/scheduling.schema'

describe('Scheduling Schemas', () => {
  describe('createScheduledOperationSchema', () => {
    it('should validate a valid scheduled operation', () => {
      const validData = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        machine_id: 1,
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
        priority: 5,
      }

      const result = createScheduledOperationSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject end time before start time', () => {
      const invalidData = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        scheduled_start: '2024-01-01T10:00:00Z',
        scheduled_end: '2024-01-01T08:00:00Z',
        priority: 5,
      }

      const result = createScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('End time must be after start time')
      }
    })

    it('should reject priority below 1', () => {
      const invalidData = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
        priority: 0,
      }

      const result = createScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at least 1')
      }
    })

    it('should reject priority above 10', () => {
      const invalidData = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
        priority: 15,
      }

      const result = createScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 10')
      }
    })

    it('should default status to SCHEDULED if not provided', () => {
      const data = {
        organization_id: 1,
        work_order_id: 1,
        operation_sequence: 10,
        operation_name: 'Cutting',
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
        priority: 5,
      }

      const result = createScheduledOperationSchema.parse(data)
      expect(result.status).toBe('SCHEDULED')
    })
  })

  describe('updateScheduledOperationSchema', () => {
    it('should validate partial update', () => {
      const validData = {
        operation_name: 'Updated Cutting',
        priority: 8,
      }

      const result = updateScheduledOperationSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should validate status change', () => {
      const validData = {
        status: 'IN_PROGRESS',
      }

      const result = updateScheduledOperationSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid status', () => {
      const invalidData = {
        status: 'INVALID_STATUS',
      }

      const result = updateScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('should validate scheduled time range', () => {
      const validData = {
        scheduled_start: '2024-01-01T08:00:00Z',
        scheduled_end: '2024-01-01T10:00:00Z',
      }

      const result = updateScheduledOperationSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid scheduled time range', () => {
      const invalidData = {
        scheduled_start: '2024-01-01T10:00:00Z',
        scheduled_end: '2024-01-01T08:00:00Z',
      }

      const result = updateScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('End time must be after start time')
      }
    })

    it('should validate actual time range', () => {
      const validData = {
        actual_start: '2024-01-01T08:05:00Z',
        actual_end: '2024-01-01T10:15:00Z',
      }

      const result = updateScheduledOperationSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid actual time range', () => {
      const invalidData = {
        actual_start: '2024-01-01T10:00:00Z',
        actual_end: '2024-01-01T08:00:00Z',
      }

      const result = updateScheduledOperationSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Actual end time must be after actual start time')
      }
    })
  })
})
