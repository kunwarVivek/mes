import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FilterGroup } from '../FilterGroup'

describe('FilterGroup', () => {
  const mockOptions = [
    { value: 'running', label: 'Running' },
    { value: 'idle', label: 'Idle' },
    { value: 'down', label: 'Down' },
  ]

  it('renders trigger button with label', () => {
    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={[]}
        onChange={() => {}}
      />
    )
    expect(screen.getByRole('button', { name: /status/i })).toBeInTheDocument()
  })

  it('shows selected count badge', () => {
    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={['running', 'idle']}
        onChange={() => {}}
      />
    )
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('toggles selection on click', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={[]}
        onChange={onChange}
      />
    )

    const trigger = screen.getByRole('button', { name: /status/i })
    await user.click(trigger)

    const runningOption = screen.getByRole('menuitemcheckbox', { name: 'Running' })
    await user.click(runningOption)

    expect(onChange).toHaveBeenCalledWith(['running'])
  })

  it('calls onChange with correct values', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={['running']}
        onChange={onChange}
      />
    )

    const trigger = screen.getByRole('button', { name: /status/i })
    await user.click(trigger)

    const idleOption = screen.getByRole('menuitemcheckbox', { name: 'Idle' })
    await user.click(idleOption)

    expect(onChange).toHaveBeenCalledWith(['running', 'idle'])
  })

  it('shows all options', async () => {
    const user = userEvent.setup()

    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={[]}
        onChange={() => {}}
      />
    )

    const trigger = screen.getByRole('button', { name: /status/i })
    await user.click(trigger)

    expect(screen.getByRole('menuitemcheckbox', { name: 'Running' })).toBeInTheDocument()
    expect(screen.getByRole('menuitemcheckbox', { name: 'Idle' })).toBeInTheDocument()
    expect(screen.getByRole('menuitemcheckbox', { name: 'Down' })).toBeInTheDocument()
  })

  it('can clear all selections', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(
      <FilterGroup
        label="Status"
        options={mockOptions}
        value={['running', 'idle']}
        onChange={onChange}
      />
    )

    const trigger = screen.getByRole('button', { name: /status/i })
    await user.click(trigger)

    const runningOption = screen.getByRole('menuitemcheckbox', { name: 'Running' })
    await user.click(runningOption)

    expect(onChange).toHaveBeenCalledWith(['idle'])
  })
})
