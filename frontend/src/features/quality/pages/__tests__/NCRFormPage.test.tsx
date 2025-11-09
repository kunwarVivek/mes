/**
 * NCRFormPage Component Tests
 *
 * Tests for NCRFormPage (create mode only) with NCRForm and navigation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NCRFormPage } from '../NCRFormPage'

// Mock dependencies
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}))

vi.mock('../../hooks/useNCRMutations', () => ({
  useNCRMutations: vi.fn(),
}))

vi.mock('../../components/NCRForm', () => ({
  NCRForm: vi.fn(({ onSuccess }) => (
    <div data-testid="ncr-form">
      <button onClick={() => onSuccess?.()}>Submit Form</button>
    </div>
  )),
}))

import { useNavigate } from 'react-router-dom'
import { useNCRMutations } from '../../hooks/useNCRMutations'
import { NCRForm } from '../../components/NCRForm'

describe('NCRFormPage', () => {
  const mockNavigate = vi.fn()
  const mockUseNCRMutations = vi.mocked(useNCRMutations)
  const mockNCRForm = vi.mocked(NCRForm)

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)

    mockUseNCRMutations.mockReturnValue({
      createNCR: {
        mutate: vi.fn(),
        mutateAsync: vi.fn(),
        isPending: false,
      },
      updateNCRStatus: {
        mutate: vi.fn(),
        isPending: false,
      },
    } as any)
  })

  describe('Page Layout', () => {
    it('renders page title', () => {
      render(<NCRFormPage />)

      expect(screen.getByText('Create Non-Conformance Report')).toBeInTheDocument()
    })

    it('renders NCRForm component', () => {
      render(<NCRFormPage />)

      expect(screen.getByTestId('ncr-form')).toBeInTheDocument()
    })

    it('passes onSuccess handler to NCRForm', () => {
      render(<NCRFormPage />)

      expect(mockNCRForm).toHaveBeenCalledWith(
        expect.objectContaining({
          onSuccess: expect.any(Function),
        }),
        expect.anything()
      )
    })
  })

  describe('Breadcrumb Navigation', () => {
    it('renders Home breadcrumb link', () => {
      render(<NCRFormPage />)

      const homeBreadcrumb = screen.getByText('Home')
      expect(homeBreadcrumb).toBeInTheDocument()
    })

    it('renders Quality breadcrumb link', () => {
      render(<NCRFormPage />)

      const qualityBreadcrumb = screen.getByText('Quality')
      expect(qualityBreadcrumb).toBeInTheDocument()
    })

    it('renders Create NCR breadcrumb (current page)', () => {
      render(<NCRFormPage />)

      const createNCRBreadcrumb = screen.getByText('Create NCR')
      expect(createNCRBreadcrumb).toBeInTheDocument()
    })

    it('navigates to home when Home breadcrumb is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRFormPage />)

      const homeBreadcrumb = screen.getByText('Home')
      await user.click(homeBreadcrumb)

      expect(mockNavigate).toHaveBeenCalledWith('/')
    })

    it('navigates to quality NCRs list when Quality breadcrumb is clicked', async () => {
      const user = userEvent.setup()
      render(<NCRFormPage />)

      const qualityBreadcrumb = screen.getByText('Quality')
      await user.click(qualityBreadcrumb)

      expect(mockNavigate).toHaveBeenCalledWith('/quality/ncrs')
    })
  })

  describe('Form Success Navigation', () => {
    it('navigates to NCR list page on successful form submission', async () => {
      const user = userEvent.setup()
      render(<NCRFormPage />)

      const submitButton = screen.getByText('Submit Form')
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/quality/ncrs')
      })
    })
  })

  describe('Accessibility', () => {
    it('has semantic page structure', () => {
      render(<NCRFormPage />)

      const mainHeading = screen.getByRole('heading', {
        name: /Create Non-Conformance Report/i,
      })
      expect(mainHeading).toBeInTheDocument()
    })
  })
})
