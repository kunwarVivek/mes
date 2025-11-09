import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DateRangeFilter } from '../DateRangeFilter'

describe('DateRangeFilter', () => {
  it('renders two date inputs', () => {
    const { container } = render(
      <DateRangeFilter
        from={null}
        to={null}
        onChange={() => {}}
      />
    )
    const inputs = container.querySelectorAll('input[type="date"]')
    expect(inputs).toHaveLength(2)
  })

  it('calls onChange with correct dates', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    const { container } = render(
      <DateRangeFilter
        from={null}
        to={null}
        onChange={onChange}
      />
    )

    const inputs = container.querySelectorAll('input[type="date"]')
    await user.type(inputs[0], '2024-01-01')

    expect(onChange).toHaveBeenCalled()
    const callArgs = onChange.mock.calls[onChange.mock.calls.length - 1]
    expect(callArgs[0]).toBeInstanceOf(Date)
  })

  it('shows label when provided', () => {
    render(
      <DateRangeFilter
        from={null}
        to={null}
        onChange={() => {}}
        label="Date Range"
      />
    )
    expect(screen.getByText('Date Range:')).toBeInTheDocument()
  })

  it('handles null values', () => {
    const { container } = render(
      <DateRangeFilter
        from={null}
        to={null}
        onChange={() => {}}
      />
    )
    const inputs = container.querySelectorAll('input[type="date"]')
    expect(inputs[0]).toHaveValue('')
    expect(inputs[1]).toHaveValue('')
  })
})
