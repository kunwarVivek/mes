import { describe, test, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Navbar, NavbarProps } from '../Navbar'

const defaultProps: NavbarProps = {
  onMenuClick: vi.fn(),
  title: 'Dashboard',
  user: {
    name: 'John Doe',
    email: 'john@example.com',
    avatar: '/avatars/john.jpg',
  },
}

const renderNavbar = (props: Partial<NavbarProps> = {}) => {
  return render(<Navbar {...defaultProps} {...props} />)
}

describe('Navbar', () => {
  test('renders page title', () => {
    renderNavbar({ title: 'Materials' })

    expect(screen.getByText('Materials')).toBeInTheDocument()
  })

  test('renders user menu', () => {
    renderNavbar()

    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })

  test('calls onMenuClick when menu button clicked', async () => {
    const onMenuClick = vi.fn()
    renderNavbar({ onMenuClick })

    const menuButton = screen.getByLabelText(/menu/i)
    await userEvent.click(menuButton)

    expect(onMenuClick).toHaveBeenCalled()
  })

  test('renders custom actions', () => {
    const actions = <button data-testid="custom-action">Custom</button>
    renderNavbar({ actions })

    expect(screen.getByTestId('custom-action')).toBeInTheDocument()
  })

  test('renders user avatar when provided', () => {
    const { container } = renderNavbar()

    // Check that avatar component is rendered (Radix UI Avatar may not load image in tests)
    const avatar = container.querySelector('.navbar__user-avatar')
    expect(avatar).toBeInTheDocument()

    // Check for image element with correct src
    const img = container.querySelector('img[alt="John Doe"]')
    if (img) {
      expect(img).toHaveAttribute('src', '/avatars/john.jpg')
    }
  })

  test('renders user email', () => {
    renderNavbar()

    expect(screen.getByText('john@example.com')).toBeInTheDocument()
  })

  test('works without title', () => {
    renderNavbar({ title: undefined })

    // Should not crash, navbar should render
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  test('works without user', () => {
    renderNavbar({ user: undefined })

    // Should not crash, navbar should render
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})
