/**
 * Shift Schema Validation Tests
 *
 * TDD: Testing Zod validation schemas
 */
import { describe, it, expect } from 'vitest'
import {
  createShiftSchema,
  updateShiftSchema,
  createShiftHandoverSchema,
} from '../schemas/shift.schema'

describe('createShiftSchema', () => {
  it('should validate a valid shift', () => {
    const validShift = {
      shift_name: 'Morning Shift',
      shift_code: 'A',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: 1000,
      is_active: true,
    }

    const result = createShiftSchema.safeParse(validShift)
    expect(result.success).toBe(true)
  })

  it('should reject empty shift_name', () => {
    const invalidShift = {
      shift_name: '',
      shift_code: 'A',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: 1000,
    }

    const result = createShiftSchema.safeParse(invalidShift)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Shift name is required')
    }
  })

  it('should reject empty shift_code', () => {
    const invalidShift = {
      shift_name: 'Morning Shift',
      shift_code: '',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: 1000,
    }

    const result = createShiftSchema.safeParse(invalidShift)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Shift code is required')
    }
  })

  it('should reject invalid time format', () => {
    const invalidShift = {
      shift_name: 'Morning Shift',
      shift_code: 'A',
      start_time: '25:00:00', // Invalid hour
      end_time: '14:00:00',
      production_target: 1000,
    }

    const result = createShiftSchema.safeParse(invalidShift)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Invalid time format')
    }
  })

  it('should reject negative production_target', () => {
    const invalidShift = {
      shift_name: 'Morning Shift',
      shift_code: 'A',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: -100,
    }

    const result = createShiftSchema.safeParse(invalidShift)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Production target must be non-negative')
    }
  })

  it('should accept overnight shift times', () => {
    const overnightShift = {
      shift_name: 'Night Shift',
      shift_code: 'C',
      start_time: '22:00:00',
      end_time: '06:00:00', // Next day
      production_target: 800,
      is_active: true,
    }

    const result = createShiftSchema.safeParse(overnightShift)
    expect(result.success).toBe(true)
  })

  it('should default is_active to true', () => {
    const shift = {
      shift_name: 'Morning Shift',
      shift_code: 'A',
      start_time: '06:00:00',
      end_time: '14:00:00',
      production_target: 1000,
    }

    const result = createShiftSchema.safeParse(shift)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.is_active).toBe(true)
    }
  })
})

describe('updateShiftSchema', () => {
  it('should validate partial updates', () => {
    const validUpdate = {
      shift_name: 'Updated Shift',
    }

    const result = updateShiftSchema.safeParse(validUpdate)
    expect(result.success).toBe(true)
  })

  it('should validate multiple fields', () => {
    const validUpdate = {
      shift_name: 'Updated Shift',
      production_target: 1200,
      is_active: false,
    }

    const result = updateShiftSchema.safeParse(validUpdate)
    expect(result.success).toBe(true)
  })

  it('should reject invalid time format in updates', () => {
    const invalidUpdate = {
      start_time: 'invalid-time',
    }

    const result = updateShiftSchema.safeParse(invalidUpdate)
    expect(result.success).toBe(false)
  })

  it('should accept empty object for partial updates', () => {
    const emptyUpdate = {}

    const result = updateShiftSchema.safeParse(emptyUpdate)
    expect(result.success).toBe(true)
  })
})

describe('createShiftHandoverSchema', () => {
  it('should validate a valid handover', () => {
    const validHandover = {
      from_shift_id: 1,
      to_shift_id: 2,
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: 'Completed 950 units, 50 in progress',
      quality_issues: 'None',
      machine_status: 'All operational',
      material_status: 'Sufficient stock',
    }

    const result = createShiftHandoverSchema.safeParse(validHandover)
    expect(result.success).toBe(true)
  })

  it('should reject same from_shift_id and to_shift_id', () => {
    const invalidHandover = {
      from_shift_id: 1,
      to_shift_id: 1, // Same as from_shift_id
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: 'Test',
    }

    const result = createShiftHandoverSchema.safeParse(invalidHandover)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('From and To shifts must be different')
    }
  })

  it('should reject negative wip_quantity', () => {
    const invalidHandover = {
      from_shift_id: 1,
      to_shift_id: 2,
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: -10,
      production_summary: 'Test',
    }

    const result = createShiftHandoverSchema.safeParse(invalidHandover)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('WIP quantity must be non-negative')
    }
  })

  it('should require production_summary', () => {
    const invalidHandover = {
      from_shift_id: 1,
      to_shift_id: 2,
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: '',
    }

    const result = createShiftHandoverSchema.safeParse(invalidHandover)
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Production summary is required')
    }
  })

  it('should allow optional fields', () => {
    const minimalHandover = {
      from_shift_id: 1,
      to_shift_id: 2,
      handover_date: '2024-01-01T14:00:00Z',
      wip_quantity: 50,
      production_summary: 'Completed production',
    }

    const result = createShiftHandoverSchema.safeParse(minimalHandover)
    expect(result.success).toBe(true)
  })
})
