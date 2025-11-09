/**
 * ProductionEntryForm Component Tests
 *
 * TDD: Testing form validation and submission
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React, { type PropsWithChildren } from 'react'
import { ProductionEntryForm } from '../components/ProductionEntryForm'
import type { ProductionLog } from '../types/productionLog.types'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: PropsWithChildren) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('ProductionEntryForm', () => {
  const mockOnSuccess = vi.fn()

  it('should render form fields', () => {
    render(<ProductionEntryForm onSuccess={mockOnSuccess} workOrderId={10} />, {
      wrapper: createWrapper(),
    })

    expect(screen.getByLabelText(/quantity produced/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/quantity scrapped/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/quantity reworked/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
  })

  it('should show validation error for negative quantity produced', async () => {
    const user = userEvent.setup()
    render(<ProductionEntryForm onSuccess={mockOnSuccess} workOrderId={10} />, {
      wrapper: createWrapper(),
    })

    const input = screen.getByLabelText(/quantity produced/i)
    await user.clear(input)
    await user.type(input, '-10')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText(/must be greater than or equal to 0/i)).toBeInTheDocument()
    })
  })

  it('should calculate and display yield rate in real-time', async () => {
    const user = userEvent.setup()
    render(<ProductionEntryForm onSuccess={mockOnSuccess} workOrderId={10} />, {
      wrapper: createWrapper(),
    })

    const produced = screen.getByLabelText(/quantity produced/i)
    const scrapped = screen.getByLabelText(/quantity scrapped/i)
    const reworked = screen.getByLabelText(/quantity reworked/i)

    await user.clear(produced)
    await user.type(produced, '100')
    await user.clear(scrapped)
    await user.type(scrapped, '5')
    await user.clear(reworked)
    await user.type(reworked, '2')

    // Yield = 100 / (100 + 5 + 2) = 93.5%
    await waitFor(() => {
      expect(screen.getByText(/93\.5%/i)).toBeInTheDocument()
    })
  })

  it('should disable submit button when form is invalid', () => {
    render(<ProductionEntryForm onSuccess={mockOnSuccess} workOrderId={10} />, {
      wrapper: createWrapper(),
    })

    const submitButton = screen.getByRole('button', { name: /submit/i })
    // Form starts empty, should be disabled
    expect(submitButton).toBeDisabled()
  })

  it('should show warning when no work order selected', () => {
    render(<ProductionEntryForm onSuccess={mockOnSuccess} />, {
      wrapper: createWrapper(),
    })

    expect(screen.getByText(/please select a work order first/i)).toBeInTheDocument()
  })
})
