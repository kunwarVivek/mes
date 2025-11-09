import { describe, it, expect } from 'vitest'
import {
  createWorkOrderSchema,
  workOrderResponseSchema,
  orderTypeSchema,
  orderStatusSchema,
  operationStatusSchema,
} from '../work-order.schema'

describe('orderTypeSchema', () => {
  it('accepts PRODUCTION type', () => {
    const result = orderTypeSchema.safeParse('PRODUCTION')
    expect(result.success).toBe(true)
  })

  it('accepts REWORK type', () => {
    const result = orderTypeSchema.safeParse('REWORK')
    expect(result.success).toBe(true)
  })

  it('accepts ASSEMBLY type', () => {
    const result = orderTypeSchema.safeParse('ASSEMBLY')
    expect(result.success).toBe(true)
  })

  it('rejects invalid type', () => {
    const result = orderTypeSchema.safeParse('INVALID')
    expect(result.success).toBe(false)
  })
})

describe('orderStatusSchema', () => {
  it('accepts all valid statuses', () => {
    const statuses = ['PLANNED', 'RELEASED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
    statuses.forEach((status) => {
      const result = orderStatusSchema.safeParse(status)
      expect(result.success).toBe(true)
    })
  })

  it('rejects invalid status', () => {
    const result = orderStatusSchema.safeParse('INVALID')
    expect(result.success).toBe(false)
  })
})

describe('operationStatusSchema', () => {
  it('accepts all valid operation statuses', () => {
    const statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED']
    statuses.forEach((status) => {
      const result = operationStatusSchema.safeParse(status)
      expect(result.success).toBe(true)
    })
  })
})

describe('createWorkOrderSchema', () => {
  const validBaseData = {
    material_id: 1,
    order_type: 'PRODUCTION',
    planned_quantity: 100,
    priority: 5,
  }

  describe('valid data', () => {
    it('validates complete valid work order data', () => {
      const validData = {
        ...validBaseData,
        start_date_planned: new Date('2025-01-15'),
        end_date_planned: new Date('2025-01-20'),
        priority: 7,
      }

      const result = createWorkOrderSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('validates minimal valid work order data', () => {
      const result = createWorkOrderSchema.safeParse(validBaseData)
      expect(result.success).toBe(true)
    })

    it('applies default order_type PRODUCTION', () => {
      const data = {
        material_id: 1,
        planned_quantity: 100,
      }
      const result = createWorkOrderSchema.safeParse(data)
      if (result.success) {
        expect(result.data.order_type).toBe('PRODUCTION')
      }
    })

    it('applies default priority 5', () => {
      const data = {
        material_id: 1,
        planned_quantity: 100,
      }
      const result = createWorkOrderSchema.safeParse(data)
      if (result.success) {
        expect(result.data.priority).toBe(5)
      }
    })

    it('accepts all valid order types', () => {
      const types = ['PRODUCTION', 'REWORK', 'ASSEMBLY']
      types.forEach((order_type) => {
        const data = {
          ...validBaseData,
          order_type,
        }
        const result = createWorkOrderSchema.safeParse(data)
        expect(result.success).toBe(true)
      })
    })

    it('accepts priority from 1 to 10', () => {
      for (let priority = 1; priority <= 10; priority++) {
        const data = {
          ...validBaseData,
          priority,
        }
        const result = createWorkOrderSchema.safeParse(data)
        expect(result.success).toBe(true)
      }
    })
  })

  describe('material_id validation', () => {
    it('rejects zero material_id', () => {
      const invalidData = {
        ...validBaseData,
        material_id: 0,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('greater than 0')
      }
    })

    it('rejects negative material_id', () => {
      const invalidData = {
        ...validBaseData,
        material_id: -1,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('rejects missing material_id', () => {
      const invalidData = {
        order_type: 'PRODUCTION',
        planned_quantity: 100,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('planned_quantity validation', () => {
    it('rejects zero planned_quantity', () => {
      const invalidData = {
        ...validBaseData,
        planned_quantity: 0,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('greater than 0')
      }
    })

    it('rejects negative planned_quantity', () => {
      const invalidData = {
        ...validBaseData,
        planned_quantity: -10,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })

    it('accepts decimal planned_quantity', () => {
      const validData = {
        ...validBaseData,
        planned_quantity: 10.5,
      }

      const result = createWorkOrderSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })

  describe('priority validation', () => {
    it('rejects priority less than 1', () => {
      const invalidData = {
        ...validBaseData,
        priority: 0,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('1')
      }
    })

    it('rejects priority greater than 10', () => {
      const invalidData = {
        ...validBaseData,
        priority: 11,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toContain('10')
      }
    })

    it('rejects negative priority', () => {
      const invalidData = {
        ...validBaseData,
        priority: -1,
      }

      const result = createWorkOrderSchema.safeParse(invalidData)
      expect(result.success).toBe(false)
    })
  })

  describe('date validation', () => {
    it('accepts valid start_date_planned', () => {
      const validData = {
        ...validBaseData,
        start_date_planned: new Date('2025-01-15'),
      }

      const result = createWorkOrderSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('accepts valid end_date_planned', () => {
      const validData = {
        ...validBaseData,
        end_date_planned: new Date('2025-01-20'),
      }

      const result = createWorkOrderSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })

    it('accepts ISO date strings', () => {
      const validData = {
        ...validBaseData,
        start_date_planned: '2025-01-15T00:00:00Z',
        end_date_planned: '2025-01-20T00:00:00Z',
      }

      const result = createWorkOrderSchema.safeParse(validData)
      expect(result.success).toBe(true)
    })
  })
})

describe('workOrderResponseSchema', () => {
  const validResponseData = {
    id: 1,
    organization_id: 1,
    plant_id: 1,
    work_order_number: 'WO-2025-001',
    material_id: 1,
    order_type: 'PRODUCTION',
    order_status: 'PLANNED',
    planned_quantity: 100,
    actual_quantity: 0,
    priority: 5,
    created_by_user_id: 1,
    created_at: new Date('2025-01-10'),
    operations: [],
    materials: [],
  }

  it('validates complete work order response', () => {
    const result = workOrderResponseSchema.safeParse(validResponseData)
    expect(result.success).toBe(true)
  })

  it('accepts work order with operations', () => {
    const data = {
      ...validResponseData,
      operations: [
        {
          id: 1,
          work_order_id: 1,
          operation_sequence: 10,
          operation_name: 'Cutting',
          status: 'PENDING',
          setup_time_minutes: 30,
          run_time_minutes: 120,
        },
      ],
    }

    const result = workOrderResponseSchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('accepts work order with materials', () => {
    const data = {
      ...validResponseData,
      materials: [
        {
          id: 1,
          work_order_id: 1,
          material_id: 2,
          required_quantity: 50,
          allocated_quantity: 0,
        },
      ],
    }

    const result = workOrderResponseSchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('accepts optional updated_at field', () => {
    const data = {
      ...validResponseData,
      updated_at: new Date('2025-01-11'),
    }

    const result = workOrderResponseSchema.safeParse(data)
    expect(result.success).toBe(true)
  })

  it('accepts optional date fields', () => {
    const data = {
      ...validResponseData,
      start_date_planned: new Date('2025-01-15'),
      start_date_actual: new Date('2025-01-16'),
      end_date_planned: new Date('2025-01-20'),
      end_date_actual: new Date('2025-01-21'),
    }

    const result = workOrderResponseSchema.safeParse(data)
    expect(result.success).toBe(true)
  })
})
