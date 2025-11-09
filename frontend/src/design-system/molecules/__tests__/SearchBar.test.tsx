import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBar } from '../SearchBar'

describe('SearchBar', () => {
  it('renders input with placeholder', () => {
    render(
      <SearchBar
        value=""
        onChange={() => {}}
        placeholder="Search orders..."
      />
    )
    expect(screen.getByPlaceholderText('Search orders...')).toBeInTheDocument()
  })

  it('calls onChange on input', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()

    render(<SearchBar value="" onChange={onChange} />)

    const input = screen.getByRole('textbox')
    await user.type(input, 'test')

    expect(onChange).toHaveBeenCalled()
  })

  it('calls onSearch on Enter key', async () => {
    const user = userEvent.setup()
    const onSearch = vi.fn()

    render(
      <SearchBar
        value="test query"
        onChange={() => {}}
        onSearch={onSearch}
      />
    )

    const input = screen.getByRole('textbox')
    await user.type(input, '{Enter}')

    expect(onSearch).toHaveBeenCalledWith('test query')
  })

  it('shows clear button when value exists', () => {
    const { container, rerender } = render(
      <SearchBar value="" onChange={() => {}} />
    )

    let clearButton = container.querySelector('button')
    expect(clearButton).not.toBeInTheDocument()

    rerender(<SearchBar value="test" onChange={() => {}} />)
    clearButton = container.querySelector('button')
    expect(clearButton).toBeInTheDocument()
  })

  it('clears value on clear button click', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const onSearch = vi.fn()

    render(
      <SearchBar
        value="test query"
        onChange={onChange}
        onSearch={onSearch}
      />
    )

    const clearButton = screen.getByRole('button')
    await user.click(clearButton)

    expect(onChange).toHaveBeenCalledWith('')
    expect(onSearch).toHaveBeenCalledWith('')
  })
})
