/**
 * Core Atoms Batch 2 - Form Elements Tests
 * TDD approach: RED -> GREEN -> REFACTOR
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '../ThemeProvider'
import { Switch } from '../atoms/Switch'
import { Radio } from '../atoms/Radio'
import { Checkbox } from '../atoms/Checkbox'
import { Textarea } from '../atoms/Textarea'

// Test wrapper with ThemeProvider
function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>)
}

describe('Switch Component', () => {
  describe('Basic Rendering', () => {
    it('renders switch in unchecked state', () => {
      renderWithTheme(<Switch checked={false} onChange={() => {}} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeTruthy()
      expect(switchElement.getAttribute('aria-checked')).toBe('false')
    })

    it('renders switch in checked state', () => {
      renderWithTheme(<Switch checked={true} onChange={() => {}} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement.getAttribute('aria-checked')).toBe('true')
    })

    it('renders with label', () => {
      renderWithTheme(
        <Switch checked={false} onChange={() => {}} label="Enable notifications" />
      )
      expect(screen.getByText('Enable notifications')).toBeTruthy()
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(
        <Switch checked={false} onChange={() => {}} size="sm" />
      )
      const switchElement = container.querySelector('.switch')
      expect(switchElement?.className).toContain('switch--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(
        <Switch checked={false} onChange={() => {}} />
      )
      const switchElement = container.querySelector('.switch')
      expect(switchElement?.className).toContain('switch--md')
    })

    it('renders large size', () => {
      const { container } = renderWithTheme(
        <Switch checked={false} onChange={() => {}} size="lg" />
      )
      const switchElement = container.querySelector('.switch')
      expect(switchElement?.className).toContain('switch--lg')
    })
  })

  describe('User Interactions', () => {
    it('calls onChange when clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Switch checked={false} onChange={onChange} />)

      const switchElement = screen.getByRole('switch')
      await user.click(switchElement)

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('calls onChange when Space key is pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Switch checked={false} onChange={onChange} />)

      const switchElement = screen.getByRole('switch')
      switchElement.focus()
      await user.keyboard(' ')

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('calls onChange when Enter key is pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Switch checked={false} onChange={onChange} />)

      const switchElement = screen.getByRole('switch')
      switchElement.focus()
      await user.keyboard('{Enter}')

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('toggles from checked to unchecked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Switch checked={true} onChange={onChange} />)

      const switchElement = screen.getByRole('switch')
      await user.click(switchElement)

      expect(onChange).toHaveBeenCalledWith(false)
    })
  })

  describe('Disabled State', () => {
    it('renders disabled state', () => {
      renderWithTheme(<Switch checked={false} onChange={() => {}} disabled />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement.getAttribute('aria-disabled')).toBe('true')
    })

    it('does not call onChange when disabled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Switch checked={false} onChange={onChange} disabled />)

      const switchElement = screen.getByRole('switch')
      await user.click(switchElement)

      expect(onChange).not.toHaveBeenCalled()
    })

    it('applies disabled class', () => {
      const { container } = renderWithTheme(
        <Switch checked={false} onChange={() => {}} disabled />
      )
      const switchElement = container.querySelector('.switch')
      expect(switchElement?.className).toContain('switch--disabled')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA role', () => {
      renderWithTheme(<Switch checked={false} onChange={() => {}} />)
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeTruthy()
    })

    it('associates label with switch using id', () => {
      renderWithTheme(
        <Switch
          checked={false}
          onChange={() => {}}
          id="test-switch"
          label="Test Label"
        />
      )
      const label = screen.getByText('Test Label')
      expect(label.getAttribute('for')).toBe('test-switch')
    })

    it('supports name attribute for forms', () => {
      renderWithTheme(
        <Switch checked={false} onChange={() => {}} name="notifications" />
      )
      const switchElement = screen.getByRole('switch')
      expect(switchElement.getAttribute('name')).toBe('notifications')
    })
  })
})

describe('Radio Component', () => {
  describe('Basic Rendering', () => {
    it('renders radio in unchecked state', () => {
      renderWithTheme(
        <Radio value="option1" checked={false} onChange={() => {}} name="test" />
      )
      const radio = screen.getByRole('radio')
      expect(radio).toBeTruthy()
      expect(radio.getAttribute('aria-checked')).toBe('false')
    })

    it('renders radio in checked state', () => {
      renderWithTheme(
        <Radio value="option1" checked={true} onChange={() => {}} name="test" />
      )
      const radio = screen.getByRole('radio')
      expect(radio.getAttribute('aria-checked')).toBe('true')
    })

    it('renders with label', () => {
      renderWithTheme(
        <Radio
          value="option1"
          checked={false}
          onChange={() => {}}
          name="test"
          label="Option 1"
        />
      )
      expect(screen.getByText('Option 1')).toBeTruthy()
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" size="sm" />
      )
      const radio = container.querySelector('.radio')
      expect(radio?.className).toContain('radio--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" />
      )
      const radio = container.querySelector('.radio')
      expect(radio?.className).toContain('radio--md')
    })

    it('renders large size', () => {
      const { container } = renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" size="lg" />
      )
      const radio = container.querySelector('.radio')
      expect(radio?.className).toContain('radio--lg')
    })
  })

  describe('User Interactions', () => {
    it('calls onChange with value when clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(
        <Radio value="option1" checked={false} onChange={onChange} name="test" />
      )

      const radio = screen.getByRole('radio')
      await user.click(radio)

      expect(onChange).toHaveBeenCalledWith('option1')
    })

    it('calls onChange when Space key is pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(
        <Radio value="option1" checked={false} onChange={onChange} name="test" />
      )

      const radio = screen.getByRole('radio')
      radio.focus()
      await user.keyboard(' ')

      expect(onChange).toHaveBeenCalledWith('option1')
    })
  })

  describe('Disabled State', () => {
    it('renders disabled state', () => {
      renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" disabled />
      )
      const radio = screen.getByRole('radio')
      expect(radio.getAttribute('aria-disabled')).toBe('true')
    })

    it('does not call onChange when disabled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(
        <Radio
          value="option1"
          checked={false}
          onChange={onChange}
          name="test"
          disabled
        />
      )

      const radio = screen.getByRole('radio')
      await user.click(radio)

      expect(onChange).not.toHaveBeenCalled()
    })

    it('applies disabled class', () => {
      const { container } = renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" disabled />
      )
      const radio = container.querySelector('.radio')
      expect(radio?.className).toContain('radio--disabled')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA role', () => {
      renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="test" />
      )
      const radio = screen.getByRole('radio')
      expect(radio).toBeTruthy()
    })

    it('associates label with radio using id', () => {
      renderWithTheme(
        <Radio
          value="opt"
          checked={false}
          onChange={() => {}}
          name="test"
          id="test-radio"
          label="Test Option"
        />
      )
      const label = screen.getByText('Test Option')
      expect(label.getAttribute('for')).toBe('test-radio')
    })

    it('supports name attribute for form grouping', () => {
      renderWithTheme(
        <Radio value="opt" checked={false} onChange={() => {}} name="radio-group" />
      )
      const radio = screen.getByRole('radio')
      expect(radio.getAttribute('name')).toBe('radio-group')
    })
  })
})

describe('Checkbox Component', () => {
  describe('Basic Rendering', () => {
    it('renders checkbox in unchecked state', () => {
      renderWithTheme(<Checkbox checked={false} onChange={() => {}} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeTruthy()
      expect(checkbox.getAttribute('aria-checked')).toBe('false')
    })

    it('renders checkbox in checked state', () => {
      renderWithTheme(<Checkbox checked={true} onChange={() => {}} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox.getAttribute('aria-checked')).toBe('true')
    })

    it('renders checkbox in indeterminate state', () => {
      renderWithTheme(<Checkbox checked={false} onChange={() => {}} indeterminate />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox.getAttribute('aria-checked')).toBe('mixed')
    })

    it('renders with label', () => {
      renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} label="Accept terms" />
      )
      expect(screen.getByText('Accept terms')).toBeTruthy()
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} size="sm" />
      )
      const checkbox = container.querySelector('.checkbox')
      expect(checkbox?.className).toContain('checkbox--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} />
      )
      const checkbox = container.querySelector('.checkbox')
      expect(checkbox?.className).toContain('checkbox--md')
    })

    it('renders large size', () => {
      const { container } = renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} size="lg" />
      )
      const checkbox = container.querySelector('.checkbox')
      expect(checkbox?.className).toContain('checkbox--lg')
    })
  })

  describe('User Interactions', () => {
    it('calls onChange when clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Checkbox checked={false} onChange={onChange} />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('calls onChange when Space key is pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Checkbox checked={false} onChange={onChange} />)

      const checkbox = screen.getByRole('checkbox')
      checkbox.focus()
      await user.keyboard(' ')

      expect(onChange).toHaveBeenCalledWith(true)
    })

    it('toggles from checked to unchecked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Checkbox checked={true} onChange={onChange} />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(onChange).toHaveBeenCalledWith(false)
    })

    it('changes from indeterminate to checked when clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Checkbox checked={false} onChange={onChange} indeterminate />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(onChange).toHaveBeenCalledWith(true)
    })
  })

  describe('Disabled State', () => {
    it('renders disabled state', () => {
      renderWithTheme(<Checkbox checked={false} onChange={() => {}} disabled />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox.getAttribute('aria-disabled')).toBe('true')
    })

    it('does not call onChange when disabled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Checkbox checked={false} onChange={onChange} disabled />)

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(onChange).not.toHaveBeenCalled()
    })

    it('applies disabled class', () => {
      const { container } = renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} disabled />
      )
      const checkbox = container.querySelector('.checkbox')
      expect(checkbox?.className).toContain('checkbox--disabled')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA role', () => {
      renderWithTheme(<Checkbox checked={false} onChange={() => {}} />)
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeTruthy()
    })

    it('associates label with checkbox using id', () => {
      renderWithTheme(
        <Checkbox
          checked={false}
          onChange={() => {}}
          id="test-checkbox"
          label="Test Checkbox"
        />
      )
      const label = screen.getByText('Test Checkbox')
      expect(label.getAttribute('for')).toBe('test-checkbox')
    })

    it('supports name attribute for forms', () => {
      renderWithTheme(
        <Checkbox checked={false} onChange={() => {}} name="terms" />
      )
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox.getAttribute('name')).toBe('terms')
    })
  })
})

describe('Textarea Component', () => {
  describe('Basic Rendering', () => {
    it('renders textarea with value', () => {
      renderWithTheme(<Textarea value="Test content" onChange={() => {}} />)
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea).toBeTruthy()
      expect(textarea.value).toBe('Test content')
    })

    it('renders with placeholder', () => {
      renderWithTheme(
        <Textarea value="" onChange={() => {}} placeholder="Enter description..." />
      )
      const textarea = screen.getByPlaceholderText('Enter description...')
      expect(textarea).toBeTruthy()
    })

    it('renders with custom rows', () => {
      renderWithTheme(<Textarea value="" onChange={() => {}} rows={5} />)
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
      expect(textarea.rows).toBe(5)
    })
  })

  describe('User Interactions', () => {
    it('calls onChange when text is typed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Textarea value="" onChange={onChange} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'H')

      expect(onChange).toHaveBeenCalled()
      expect(onChange).toHaveBeenLastCalledWith('H')
    })

    it('updates value when typing', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Textarea value="" onChange={onChange} />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'T')

      const calls = onChange.mock.calls
      expect(calls[calls.length - 1][0]).toBe('T')
    })
  })

  describe('Resize Behavior', () => {
    it('applies none resize class', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} resize="none" />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--resize-none')
    })

    it('applies vertical resize class (default)', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--resize-vertical')
    })

    it('applies horizontal resize class', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} resize="horizontal" />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--resize-horizontal')
    })

    it('applies both resize class', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} resize="both" />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--resize-both')
    })
  })

  describe('Character Counter', () => {
    it('shows character counter when maxLength is provided', () => {
      renderWithTheme(<Textarea value="Hello" onChange={() => {}} maxLength={100} />)
      expect(screen.getByText('5 / 100')).toBeTruthy()
    })

    it('updates character count as user types', () => {
      renderWithTheme(<Textarea value="Test" onChange={() => {}} maxLength={50} />)
      expect(screen.getByText('4 / 50')).toBeTruthy()
    })

    it('does not show counter when maxLength is not provided', () => {
      const { container } = renderWithTheme(
        <Textarea value="Hello" onChange={() => {}} />
      )
      const counter = container.querySelector('.textarea__counter')
      expect(counter).toBeFalsy()
    })
  })

  describe('Error State', () => {
    it('applies error class when error is true', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} error />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--error')
    })

    it('sets aria-invalid when error is true', () => {
      renderWithTheme(<Textarea value="" onChange={() => {}} error />)
      const textarea = screen.getByRole('textbox')
      expect(textarea.getAttribute('aria-invalid')).toBe('true')
    })
  })

  describe('Disabled State', () => {
    it('renders disabled state', () => {
      renderWithTheme(<Textarea value="" onChange={() => {}} disabled />)
      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveProperty('disabled', true)
    })

    it('applies disabled class', () => {
      const { container } = renderWithTheme(
        <Textarea value="" onChange={() => {}} disabled />
      )
      const textarea = container.querySelector('.textarea')
      expect(textarea?.className).toContain('textarea--disabled')
    })

    it('does not call onChange when disabled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderWithTheme(<Textarea value="" onChange={onChange} disabled />)

      const textarea = screen.getByRole('textbox')
      await user.type(textarea, 'test')

      expect(onChange).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('supports id attribute', () => {
      renderWithTheme(<Textarea value="" onChange={() => {}} id="description" />)
      const textarea = screen.getByRole('textbox')
      expect(textarea.id).toBe('description')
    })

    it('supports name attribute for forms', () => {
      renderWithTheme(<Textarea value="" onChange={() => {}} name="comment" />)
      const textarea = screen.getByRole('textbox')
      expect(textarea.getAttribute('name')).toBe('comment')
    })
  })
})
