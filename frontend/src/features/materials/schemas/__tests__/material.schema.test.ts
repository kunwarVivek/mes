import { describe, it, expect } from 'vitest'
import { createMaterialSchema, updateMaterialSchema } from '../material.schema'

describe('createMaterialSchema', () => {
  const validBaseData = {
    organization_id: 1,
    plant_id: 1,
    material_number: 'MAT001',
    material_name: 'Steel Plate',
    material_category_id: 1,
    base_uom_id: 1,
    procurement_type: 'PURCHASE',
    mrp_type: 'MRP',
  }

  describe('valid data', () => {
    it('validates complete valid material data', () => {
      const validData = {
        ...validBaseData,
        description: 'High-grade steel plate',
        safety_stock: 100,
        reorder_point: 200,
        lot_size: 50,
        lead_time_days: 7,
      }

      const result = createMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates minimal valid material data', () => {
      const result = createMaterialSchema.safeParse(validBaseData)
      expect(result.success).toBe(true)
    })

    it('accepts uppercase alphanumeric material number', () => {
      const validData = {
        ...validBaseData,
        material_number: 'ABC123XYZ',
      }

      const result = createMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('accepts all valid procurement types', () => {
      const types = ['PURCHASE', 'MANUFACTURE', 'BOTH']

      types.forEach(procurement_type => {
        const data = {
          ...validBaseData,
          procurement_type,
        }

        const result = createMaterialSchema.safeParse(data)
        expect(result.success).toBe(true)
      })
    })

    it('accepts all valid MRP types', () => {
      const types = ['MRP', 'REORDER']

      types.forEach(mrp_type => {
        const data = {
          ...validBaseData,
          mrp_type,
        }

        const result = createMaterialSchema.safeParse(data)
        expect(result.success).toBe(true)
      })
    })

    it('applies default values for optional fields', () => {
      const result = createMaterialSchema.safeParse(validBaseData)
      if (result.success) {
        expect(result.data.safety_stock).toBe(0)
        expect(result.data.reorder_point).toBe(0)
        expect(result.data.lot_size).toBe(1)
        expect(result.data.lead_time_days).toBe(0)
      }
    })
  })

  describe('material_number validation', () => {
    it('rejects empty material number', () => {
      const invalidData = {
        ...validBaseData,
        material_number: '',
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Material number is required')
      }
    })

    it('rejects lowercase material number', () => {
      const invalidData = {
        ...validBaseData,
        material_number: 'mat001',
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues.some(i => i.message.includes('uppercase alphanumeric'))).toBe(true)
      }
    })

    it('rejects material number with special characters', () => {
      const invalidData = {
        ...validBaseData,
        material_number: 'MAT@001',
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects material number with hyphens', () => {
      const invalidData = {
        ...validBaseData,
        material_number: 'MAT-001',
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects material number exceeding 10 characters', () => {
      const invalidData = {
        ...validBaseData,
        material_number: 'A'.repeat(11),
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 10 characters')
      }
    })
  })

  describe('material_name validation', () => {
    it('rejects empty name', () => {
      const invalidData = {
        ...validBaseData,
        material_name: '',
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Material name is required')
      }
    })

    it('rejects name exceeding 200 characters', () => {
      const invalidData = {
        ...validBaseData,
        material_name: 'A'.repeat(201),
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 200 characters')
      }
    })
  })

  describe('description validation', () => {
    it('rejects description exceeding 500 characters', () => {
      const invalidData = {
        ...validBaseData,
        description: 'A'.repeat(501),
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 500 characters')
      }
    })

    it('accepts empty optional description', () => {
      const validData = {
        ...validBaseData,
        description: undefined,
      }

      const result = createMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('organization_id validation', () => {
    it('rejects zero organization_id', () => {
      const invalidData = {
        ...validBaseData,
        organization_id: 0,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects negative organization_id', () => {
      const invalidData = {
        ...validBaseData,
        organization_id: -1,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('plant_id validation', () => {
    it('rejects zero plant_id', () => {
      const invalidData = {
        ...validBaseData,
        plant_id: 0,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('stock level validation', () => {
    it('rejects negative safety_stock', () => {
      const invalidData = {
        ...validBaseData,
        safety_stock: -10,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('non-negative')
      }
    })

    it('rejects negative reorder_point', () => {
      const invalidData = {
        ...validBaseData,
        reorder_point: -50,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects zero lot_size', () => {
      const invalidData = {
        ...validBaseData,
        lot_size: 0,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('rejects negative lot_size', () => {
      const invalidData = {
        ...validBaseData,
        lot_size: -10,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('lead_time_days validation', () => {
    it('rejects negative lead time', () => {
      const invalidData = {
        ...validBaseData,
        lead_time_days: -5,
      }

      const result = createMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('non-negative')
      }
    })

    it('accepts zero lead time', () => {
      const validData = {
        ...validBaseData,
        lead_time_days: 0,
      }

      const result = createMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })
})

describe('updateMaterialSchema', () => {
  describe('valid data', () => {
    it('validates partial update with single field', () => {
      const validData = {
        material_name: 'Updated Material Name',
      }

      const result = updateMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates partial update with multiple fields', () => {
      const validData = {
        material_name: 'Updated Name',
        description: 'Updated description',
        safety_stock: 150,
        reorder_point: 250,
        is_active: false,
      }

      const result = updateMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates empty update object', () => {
      const validData = {}

      const result = updateMaterialSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('field validation', () => {
    it('rejects empty material_name if provided', () => {
      const invalidData = {
        material_name: '',
      }

      const result = updateMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects material_name exceeding 200 characters', () => {
      const invalidData = {
        material_name: 'A'.repeat(201),
      }

      const result = updateMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects negative safety_stock', () => {
      const invalidData = {
        safety_stock: -10,
      }

      const result = updateMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects zero lot_size', () => {
      const invalidData = {
        lot_size: 0,
      }

      const result = updateMaterialSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })
})
