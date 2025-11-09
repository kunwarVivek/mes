/**
 * MRP Schema Tests
 *
 * TDD: Testing Zod validation schemas
 */
import { describe, it, expect } from 'vitest'
import { createMRPRunSchema, updateMRPRunSchema } from '../schemas/mrp.schema'

describe('MRP Schemas', () => {
  describe('createMRPRunSchema', () => {
    it('should validate a valid MRP run', () => {
      const validData = {
        organization_id: 1,
        run_code: 'MRP001',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: 30,
        created_by_user_id: 1,
      }

      const result = createMRPRunSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject negative planning horizon', () => {
      const invalidData = {
        organization_id: 1,
        run_code: 'MRP001',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: -5,
        created_by_user_id: 1,
      }

      const result = createMRPRunSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('should reject planning horizon over 365 days', () => {
      const invalidData = {
        organization_id: 1,
        run_code: 'MRP001',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: 400,
        created_by_user_id: 1,
      }

      const result = createMRPRunSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('365')
      }
    })

    it('should reject empty run code', () => {
      const invalidData = {
        organization_id: 1,
        run_code: '',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: 30,
        created_by_user_id: 1,
      }

      const result = createMRPRunSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('should default status to DRAFT if not provided', () => {
      const data = {
        organization_id: 1,
        run_code: 'MRP001',
        run_name: 'Test MRP Run',
        run_date: '2024-01-01',
        planning_horizon_days: 30,
        created_by_user_id: 1,
      }

      const result = createMRPRunSchema.parse(data)
      expect(result.status).toBe('DRAFT')
    })
  })

  describe('updateMRPRunSchema', () => {
    it('should validate partial update', () => {
      const validData = {
        run_name: 'Updated MRP Run',
      }

      const result = updateMRPRunSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should validate status change', () => {
      const validData = {
        status: 'RUNNING',
      }

      const result = updateMRPRunSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('should reject invalid status', () => {
      const invalidData = {
        status: 'INVALID_STATUS',
      }

      const result = updateMRPRunSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })
})
