/**
 * Lane Types Tests
 *
 * TDD RED Phase: Test type definitions and constraints
 */
import { describe, it, expect } from 'vitest'
import type {
  Lane,
  LaneAssignment,
  LaneCapacity,
  LaneAssignmentStatus
} from '../types/lane.types'

describe('Lane Types', () => {
  describe('Lane', () => {
    it('should have all required properties', () => {
      const lane: Lane = {
        id: 1,
        plant_id: 100,
        lane_code: 'L001',
        lane_name: 'Assembly Line 1',
        capacity_per_day: 1000,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      }

      expect(lane.id).toBe(1)
      expect(lane.plant_id).toBe(100)
      expect(lane.lane_code).toBe('L001')
      expect(lane.capacity_per_day).toBe(1000)
      expect(lane.is_active).toBe(true)
    })

    it('should allow optional updated_at', () => {
      const lane: Lane = {
        id: 1,
        plant_id: 100,
        lane_code: 'L001',
        lane_name: 'Assembly Line 1',
        capacity_per_day: 1000,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      }

      expect(lane.updated_at).toBe('2025-01-02T00:00:00Z')
    })
  })

  describe('LaneAssignment', () => {
    it('should have all required properties', () => {
      const assignment: LaneAssignment = {
        id: 1,
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 500,
        priority: 1,
        status: 'PLANNED' as LaneAssignmentStatus,
        created_at: '2025-01-01T00:00:00Z',
      }

      expect(assignment.id).toBe(1)
      expect(assignment.work_order_id).toBe(500)
      expect(assignment.scheduled_start).toBe('2025-01-15')
      expect(assignment.allocated_capacity).toBe(500)
    })

    it('should allow optional project_id and notes', () => {
      const assignment: LaneAssignment = {
        id: 1,
        organization_id: 1,
        plant_id: 100,
        lane_id: 1,
        work_order_id: 500,
        project_id: 10,
        scheduled_start: '2025-01-15',
        scheduled_end: '2025-01-20',
        allocated_capacity: 500,
        priority: 1,
        status: 'ACTIVE' as LaneAssignmentStatus,
        notes: 'High priority order',
        created_at: '2025-01-01T00:00:00Z',
      }

      expect(assignment.project_id).toBe(10)
      expect(assignment.notes).toBe('High priority order')
    })
  })

  describe('LaneCapacity', () => {
    it('should calculate utilization correctly', () => {
      const capacity: LaneCapacity = {
        lane_id: 1,
        date: '2025-01-15',
        total_capacity: 1000,
        allocated_capacity: 800,
        available_capacity: 200,
        utilization_rate: 80,
        assignment_count: 3,
      }

      expect(capacity.utilization_rate).toBe(80)
      expect(capacity.available_capacity).toBe(200)
      expect(capacity.total_capacity - capacity.allocated_capacity).toBe(200)
    })

    it('should handle overbooked scenario', () => {
      const capacity: LaneCapacity = {
        lane_id: 1,
        date: '2025-01-15',
        total_capacity: 1000,
        allocated_capacity: 1200,
        available_capacity: -200,
        utilization_rate: 120,
        assignment_count: 5,
      }

      expect(capacity.utilization_rate).toBeGreaterThan(100)
      expect(capacity.available_capacity).toBeLessThan(0)
    })
  })
})
