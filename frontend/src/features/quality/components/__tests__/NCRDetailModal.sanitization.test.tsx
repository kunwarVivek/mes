/**
 * NCRDetailModal Sanitization Tests
 *
 * Tests to verify XSS prevention in NCRDetailModal component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NCRDetailModal } from '../NCRDetailModal'
import type { NCR } from '../types/ncr.types'

describe('NCRDetailModal - XSS Prevention', () => {
  const mockOnUpdate = vi.fn()
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should sanitize script tags in description field', () => {
    const ncrWithXSS: NCR = {
      id: 1,
      ncr_number: 'NCR-2025-001',
      work_order_id: 100,
      material_id: 200,
      defect_type: 'DIMENSIONAL',
      description: '<script>alert("XSS")</script>Critical manufacturing defect',
      quantity_affected: 5,
      status: 'OPEN',
      reported_at: '2025-01-01T00:00:00Z',
      reported_by_user_id: 1,
      root_cause: null,
      corrective_action: null,
      preventive_action: null,
    }

    render(<NCRDetailModal ncr={ncrWithXSS} onUpdate={mockOnUpdate} onClose={mockOnClose} />)

    const modal = screen.getByTestId('ncr-detail-modal')
    expect(modal.innerHTML).not.toContain('<script>')
    expect(modal.innerHTML).not.toContain('alert("XSS")')
    expect(modal.innerHTML).toContain('Critical manufacturing defect')
  })

  it('should sanitize event handlers in root_cause field', () => {
    const ncrWithXSS: NCR = {
      id: 2,
      ncr_number: 'NCR-2025-002',
      work_order_id: 101,
      material_id: 201,
      defect_type: 'VISUAL',
      description: 'Visual defect',
      quantity_affected: 10,
      status: 'INVESTIGATING',
      reported_at: '2025-01-02T00:00:00Z',
      reported_by_user_id: 2,
      root_cause: '<div onclick="alert(\'XSS\')">Machine calibration issue</div>',
      corrective_action: null,
      preventive_action: null,
    }

    render(<NCRDetailModal ncr={ncrWithXSS} onUpdate={mockOnUpdate} onClose={mockOnClose} />)

    const modal = screen.getByTestId('ncr-detail-modal')
    expect(modal.innerHTML).not.toContain('onclick')
    expect(modal.innerHTML).not.toContain('alert(\'XSS\')')
    expect(modal.innerHTML).toContain('Machine calibration issue')
  })

  it('should sanitize javascript: protocol in corrective_action field', () => {
    const ncrWithXSS: NCR = {
      id: 3,
      ncr_number: 'NCR-2025-003',
      work_order_id: 102,
      material_id: 202,
      defect_type: 'FUNCTIONAL',
      description: 'Functional failure',
      quantity_affected: 3,
      status: 'CORRECTIVE_ACTION',
      reported_at: '2025-01-03T00:00:00Z',
      reported_by_user_id: 3,
      root_cause: 'Component failure',
      corrective_action:
        '<a href="javascript:alert(\'XSS\')">Click for action plan</a>',
      preventive_action: null,
    }

    render(<NCRDetailModal ncr={ncrWithXSS} onUpdate={mockOnUpdate} onClose={mockOnClose} />)

    const modal = screen.getByTestId('ncr-detail-modal')
    expect(modal.innerHTML).not.toContain('javascript:')
    expect(modal.innerHTML).not.toContain('alert(\'XSS\')')
  })

  it('should sanitize iframe tags in preventive_action field', () => {
    const ncrWithXSS: NCR = {
      id: 4,
      ncr_number: 'NCR-2025-004',
      work_order_id: 103,
      material_id: 203,
      defect_type: 'MATERIAL',
      description: 'Material defect',
      quantity_affected: 15,
      status: 'CLOSED',
      reported_at: '2025-01-04T00:00:00Z',
      reported_by_user_id: 4,
      root_cause: 'Supplier issue',
      corrective_action: 'Changed supplier',
      preventive_action:
        '<iframe src="http://evil.com"></iframe>Implement incoming inspection',
    }

    render(<NCRDetailModal ncr={ncrWithXSS} onUpdate={mockOnUpdate} onClose={mockOnClose} />)

    const modal = screen.getByTestId('ncr-detail-modal')
    expect(modal.innerHTML).not.toContain('<iframe')
    expect(modal.innerHTML).toContain('Implement incoming inspection')
  })

  it('should preserve safe HTML formatting in description', () => {
    const ncrWithSafeHTML: NCR = {
      id: 5,
      ncr_number: 'NCR-2025-005',
      work_order_id: 104,
      material_id: 204,
      defect_type: 'DIMENSIONAL',
      description: '<p>Defect found in <strong>critical</strong> dimension</p>',
      quantity_affected: 2,
      status: 'OPEN',
      reported_at: '2025-01-05T00:00:00Z',
      reported_by_user_id: 5,
      root_cause: null,
      corrective_action: null,
      preventive_action: null,
    }

    render(
      <NCRDetailModal ncr={ncrWithSafeHTML} onUpdate={mockOnUpdate} onClose={mockOnClose} />
    )

    const modal = screen.getByTestId('ncr-detail-modal')
    expect(modal.innerHTML).toContain('<p>')
    expect(modal.innerHTML).toContain('<strong>')
    expect(modal.innerHTML).toContain('Defect found in')
    expect(modal.innerHTML).toContain('critical')
  })

  it('should not execute any JavaScript from user content', () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    const ncrWithMultipleXSS: NCR = {
      id: 6,
      ncr_number: 'NCR-2025-006',
      work_order_id: 105,
      material_id: 205,
      defect_type: 'OTHER',
      description: '<script>alert("XSS1")</script>Description',
      quantity_affected: 8,
      status: 'INVESTIGATING',
      reported_at: '2025-01-06T00:00:00Z',
      reported_by_user_id: 6,
      root_cause: '<img src="x" onerror="alert(\'XSS2\')">Root cause',
      corrective_action: '<body onload="alert(\'XSS3\')">Action',
      preventive_action: '<svg onload="alert(\'XSS4\')">Prevention',
    }

    render(
      <NCRDetailModal ncr={ncrWithMultipleXSS} onUpdate={mockOnUpdate} onClose={mockOnClose} />
    )

    // No alerts should be triggered from any field
    expect(alertSpy).not.toHaveBeenCalled()

    alertSpy.mockRestore()
  })

  it('should handle null values in optional fields gracefully', () => {
    const ncrWithNulls: NCR = {
      id: 7,
      ncr_number: 'NCR-2025-007',
      work_order_id: 106,
      material_id: 206,
      defect_type: 'VISUAL',
      description: 'Simple description',
      quantity_affected: 1,
      status: 'OPEN',
      reported_at: '2025-01-07T00:00:00Z',
      reported_by_user_id: 7,
      root_cause: null,
      corrective_action: null,
      preventive_action: null,
    }

    render(<NCRDetailModal ncr={ncrWithNulls} onUpdate={mockOnUpdate} onClose={mockOnClose} />)

    expect(screen.getByTestId('ncr-detail-modal')).toBeInTheDocument()
    expect(screen.getByText('Simple description')).toBeInTheDocument()
  })
})
