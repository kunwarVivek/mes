import { describe, it, expect } from 'vitest'
import {
  createNCRSchema,
  updateNCRStatusSchema,
  ncrStatusSchema,
  defectTypeSchema,
} from '../ncr.schema'

describe('ncrStatusSchema', () => {
  it('accepts all valid NCR statuses', () => {
    const validStatuses = ['OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED']

    validStatuses.forEach(status => {
      const result = ncrStatusSchema.safeParse(status)
      expect(result.success).toBe(true)
    })
  })

  it('rejects invalid status', () => {
    const result = ncrStatusSchema.safeParse('INVALID_STATUS')
    expect(result.success).toBe(false)
  })
})

describe('defectTypeSchema', () => {
  it('accepts all valid defect types', () => {
    const validTypes = ['DIMENSIONAL', 'VISUAL', 'FUNCTIONAL', 'MATERIAL', 'OTHER']

    validTypes.forEach(type => {
      const result = defectTypeSchema.safeParse(type)
      expect(result.success).toBe(true)
    })
  })

  it('rejects invalid defect type', () => {
    const result = defectTypeSchema.safeParse('INVALID_TYPE')
    expect(result.success).toBe(false)
  })
})

describe('createNCRSchema', () => {
  const validBaseData = {
    ncr_number: 'NCR-2024-001',
    work_order_id: 1,
    material_id: 1,
    defect_type: 'DIMENSIONAL' as const,
    defect_description: 'Part dimensions out of tolerance',
    quantity_defective: 5,
    reported_by_user_id: 1,
  }

  describe('valid data', () => {
    it('validates complete valid NCR data', () => {
      const validData = {
        ...validBaseData,
        attachment_urls: ['https://example.com/photo1.jpg', 'https://example.com/photo2.jpg'],
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates minimal valid NCR data without attachments', () => {
      const result = createNCRSchema.safeParse(validBaseData)
      expect(result.success).toBe(true)
    })

    it('accepts all valid defect types', () => {
      const types = ['DIMENSIONAL', 'VISUAL', 'FUNCTIONAL', 'MATERIAL', 'OTHER']

      types.forEach(defect_type => {
        const data = {
          ...validBaseData,
          defect_type,
        }

        const result = createNCRSchema.safeParse(data)
        expect(result.success).toBe(true)
      })
    })

    it('accepts empty attachment_urls array', () => {
      const validData = {
        ...validBaseData,
        attachment_urls: [],
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('ncr_number validation', () => {
    it('rejects empty ncr_number', () => {
      const invalidData = {
        ...validBaseData,
        ncr_number: '',
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('NCR number is required')
      }
    })

    it('rejects ncr_number exceeding 50 characters', () => {
      const invalidData = {
        ...validBaseData,
        ncr_number: 'A'.repeat(51),
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 50 characters')
      }
    })

    it('accepts ncr_number at max length (50 characters)', () => {
      const validData = {
        ...validBaseData,
        ncr_number: 'A'.repeat(50),
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('work_order_id validation', () => {
    it('rejects zero work_order_id', () => {
      const invalidData = {
        ...validBaseData,
        work_order_id: 0,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('rejects negative work_order_id', () => {
      const invalidData = {
        ...validBaseData,
        work_order_id: -1,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('material_id validation', () => {
    it('rejects zero material_id', () => {
      const invalidData = {
        ...validBaseData,
        material_id: 0,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('rejects negative material_id', () => {
      const invalidData = {
        ...validBaseData,
        material_id: -1,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('defect_description validation', () => {
    it('rejects empty defect_description', () => {
      const invalidData = {
        ...validBaseData,
        defect_description: '',
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Defect description is required')
      }
    })

    it('rejects defect_description exceeding 500 characters', () => {
      const invalidData = {
        ...validBaseData,
        defect_description: 'A'.repeat(501),
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('at most 500 characters')
      }
    })

    it('accepts defect_description at max length (500 characters)', () => {
      const validData = {
        ...validBaseData,
        defect_description: 'A'.repeat(500),
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('quantity_defective validation', () => {
    it('rejects zero quantity_defective', () => {
      const invalidData = {
        ...validBaseData,
        quantity_defective: 0,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('rejects negative quantity_defective', () => {
      const invalidData = {
        ...validBaseData,
        quantity_defective: -5,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('accepts positive quantity_defective', () => {
      const validData = {
        ...validBaseData,
        quantity_defective: 100,
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('reported_by_user_id validation', () => {
    it('rejects zero reported_by_user_id', () => {
      const invalidData = {
        ...validBaseData,
        reported_by_user_id: 0,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('positive')
      }
    })

    it('rejects negative reported_by_user_id', () => {
      const invalidData = {
        ...validBaseData,
        reported_by_user_id: -1,
      }

      const result = createNCRSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('attachment_urls validation', () => {
    it('accepts valid array of URLs', () => {
      const validData = {
        ...validBaseData,
        attachment_urls: [
          'https://example.com/photo1.jpg',
          'https://example.com/photo2.jpg',
          'https://example.com/photo3.jpg',
        ],
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('accepts undefined attachment_urls', () => {
      const validData = {
        ...validBaseData,
        attachment_urls: undefined,
      }

      const result = createNCRSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })
})

describe('updateNCRStatusSchema', () => {
  describe('valid data', () => {
    it('validates status update to IN_REVIEW', () => {
      const validData = {
        status: 'IN_REVIEW' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates status update to RESOLVED with resolution_notes', () => {
      const validData = {
        status: 'RESOLVED' as const,
        resolution_notes: 'Parts have been reworked and reinspected',
        resolved_by_user_id: 2,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates status update to CLOSED', () => {
      const validData = {
        status: 'CLOSED' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('conditional validation for RESOLVED status', () => {
    it('requires resolution_notes when status is RESOLVED', () => {
      const invalidData = {
        status: 'RESOLVED' as const,
        // Missing resolution_notes
      }

      const result = updateNCRStatusSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Resolution notes are required')
      }
    })

    it('rejects empty resolution_notes when status is RESOLVED', () => {
      const invalidData = {
        status: 'RESOLVED' as const,
        resolution_notes: '',
      }

      const result = updateNCRStatusSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('Resolution notes are required')
      }
    })

    it('allows missing resolution_notes when status is not RESOLVED', () => {
      const validData = {
        status: 'IN_REVIEW' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('allows missing resolution_notes for OPEN status', () => {
      const validData = {
        status: 'OPEN' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('allows missing resolution_notes for CLOSED status', () => {
      const validData = {
        status: 'CLOSED' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('resolved_by_user_id validation', () => {
    it('accepts valid resolved_by_user_id', () => {
      const validData = {
        status: 'RESOLVED' as const,
        resolution_notes: 'Issue resolved',
        resolved_by_user_id: 5,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('accepts undefined resolved_by_user_id', () => {
      const validData = {
        status: 'IN_REVIEW' as const,
      }

      const result = updateNCRStatusSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('status validation', () => {
    it('rejects invalid status value', () => {
      const invalidData = {
        status: 'INVALID_STATUS',
      }

      const result = updateNCRStatusSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })
})
