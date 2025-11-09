/**
 * Layout Templates Tests
 * TDD approach: RED -> GREEN -> REFACTOR
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '../ThemeProvider'
import { Bell, User } from 'lucide-react'

// Components will be imported once they exist
import { Sidebar } from '../templates/Sidebar'
import { Navbar } from '../templates/Navbar'
import { AppLayout } from '../templates/AppLayout'
import { AuthLayout } from '../templates/AuthLayout'

// Test wrapper with ThemeProvider
function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>)
}

// ===================================
// SIDEBAR COMPONENT TESTS
// ===================================

describe('Sidebar Component', () => {
  it('renders sidebar with children', () => {
    renderWithTheme(
      <Sidebar isOpen={true} onClose={() => {}}>
        <nav>Navigation</nav>
      </Sidebar>
    )
    const sidebar = screen.getByRole('complementary')
    expect(sidebar).toBeTruthy()
  })

  describe('Permanent Variant (Desktop)', () => {
    it('renders permanent sidebar', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}} variant="permanent">
          <nav>Navigation</nav>
        </Sidebar>
      )
      const sidebar = screen.getByRole('complementary')
      expect(sidebar.className).toContain('sidebar--permanent')
    })

    it('does not show close button in permanent mode', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}} variant="permanent">
          <nav>Navigation</nav>
        </Sidebar>
      )
      const closeButton = screen.queryByRole('button', { name: /close/i })
      expect(closeButton).toBeFalsy()
    })
  })

  describe('Temporary Variant (Mobile)', () => {
    it('renders temporary sidebar', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}} variant="temporary">
          <nav>Navigation</nav>
        </Sidebar>
      )
      const sidebar = screen.getByRole('complementary')
      expect(sidebar.className).toContain('sidebar--temporary')
    })

    it('shows close button in temporary mode', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}} variant="temporary">
          <nav>Navigation</nav>
        </Sidebar>
      )
      const closeButton = screen.getByRole('button', { name: /close/i })
      expect(closeButton).toBeTruthy()
    })

    it('calls onClose when close button clicked', async () => {
      const handleClose = vi.fn()
      const user = userEvent.setup()

      renderWithTheme(
        <Sidebar isOpen={true} onClose={handleClose} variant="temporary">
          <nav>Navigation</nav>
        </Sidebar>
      )

      const closeButton = screen.getByRole('button', { name: /close/i })
      await user.click(closeButton)
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when Escape key pressed', async () => {
      const handleClose = vi.fn()
      const user = userEvent.setup()

      renderWithTheme(
        <Sidebar isOpen={true} onClose={handleClose} variant="temporary">
          <nav>Navigation</nav>
        </Sidebar>
      )

      await user.keyboard('{Escape}')
      expect(handleClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Open/Close States', () => {
    it('shows sidebar when isOpen is true', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}}>
          <nav>Navigation</nav>
        </Sidebar>
      )
      const sidebar = screen.getByRole('complementary')
      expect(sidebar.className).toContain('sidebar--open')
    })

    it('hides sidebar when isOpen is false', () => {
      const { container } = renderWithTheme(
        <Sidebar isOpen={false} onClose={() => {}}>
          <nav>Navigation</nav>
        </Sidebar>
      )
      const sidebar = container.querySelector('.sidebar--closed')
      expect(sidebar).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA label', () => {
      renderWithTheme(
        <Sidebar isOpen={true} onClose={() => {}}>
          <nav>Navigation</nav>
        </Sidebar>
      )
      const sidebar = screen.getByRole('complementary')
      expect(sidebar).toHaveAttribute('aria-label')
    })
  })
})

// ===================================
// NAVBAR COMPONENT TESTS
// ===================================

describe('Navbar Component', () => {
  it('renders navbar', () => {
    renderWithTheme(<Navbar />)
    const navbar = screen.getByRole('banner')
    expect(navbar).toBeTruthy()
  })

  describe('Title', () => {
    it('renders title when provided', () => {
      renderWithTheme(<Navbar title="Dashboard" />)
      expect(screen.getByText('Dashboard')).toBeTruthy()
    })

    it('does not render title when not provided', () => {
      renderWithTheme(<Navbar />)
      const navbar = screen.getByRole('banner')
      expect(navbar.textContent).toBe('')
    })
  })

  describe('Menu Button', () => {
    it('shows menu button when showMenuButton is true', () => {
      renderWithTheme(<Navbar showMenuButton onMenuClick={() => {}} />)
      const menuButton = screen.getByRole('button', { name: /menu/i })
      expect(menuButton).toBeTruthy()
    })

    it('hides menu button when showMenuButton is false', () => {
      renderWithTheme(<Navbar showMenuButton={false} />)
      const menuButton = screen.queryByRole('button', { name: /menu/i })
      expect(menuButton).toBeFalsy()
    })

    it('calls onMenuClick when menu button clicked', async () => {
      const handleMenuClick = vi.fn()
      const user = userEvent.setup()

      renderWithTheme(<Navbar showMenuButton onMenuClick={handleMenuClick} />)

      const menuButton = screen.getByRole('button', { name: /menu/i })
      await user.click(menuButton)
      expect(handleMenuClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('Actions', () => {
    it('renders actions when provided', () => {
      renderWithTheme(
        <Navbar
          actions={
            <>
              <button aria-label="Notifications">
                <Bell />
              </button>
              <button aria-label="User menu">
                <User />
              </button>
            </>
          }
        />
      )
      const notificationButton = screen.getByRole('button', { name: 'Notifications' })
      const userButton = screen.getByRole('button', { name: 'User menu' })
      expect(notificationButton).toBeTruthy()
      expect(userButton).toBeTruthy()
    })
  })
})

// ===================================
// APPLAYOUT COMPONENT TESTS
// ===================================

describe('AppLayout Component', () => {
  it('renders app layout with children', () => {
    renderWithTheme(
      <AppLayout>
        <div>Main content</div>
      </AppLayout>
    )
    expect(screen.getByText('Main content')).toBeTruthy()
  })

  describe('Default Sidebar and Navbar', () => {
    it('renders default sidebar and navbar', () => {
      renderWithTheme(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )
      const sidebar = screen.getByRole('complementary')
      const navbar = screen.getByRole('banner')
      expect(sidebar).toBeTruthy()
      expect(navbar).toBeTruthy()
    })
  })

  describe('Custom Sidebar and Navbar', () => {
    it('renders custom sidebar when provided', () => {
      const customSidebar = <aside data-testid="custom-sidebar">Custom</aside>
      renderWithTheme(
        <AppLayout sidebar={customSidebar}>
          <div>Content</div>
        </AppLayout>
      )
      expect(screen.getByTestId('custom-sidebar')).toBeTruthy()
    })

    it('renders custom navbar when provided', () => {
      const customNavbar = <header data-testid="custom-navbar">Custom</header>
      renderWithTheme(
        <AppLayout navbar={customNavbar}>
          <div>Content</div>
        </AppLayout>
      )
      expect(screen.getByTestId('custom-navbar')).toBeTruthy()
    })
  })

  describe('Responsive Behavior', () => {
    it('sidebar can be toggled via navbar menu button', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      )

      const menuButton = screen.getByRole('button', { name: /menu/i })
      await user.click(menuButton)

      const sidebar = screen.getByRole('complementary')
      expect(sidebar.className).toContain('sidebar--open')
    })
  })

  describe('Main Content Area', () => {
    it('renders main content in correct area', () => {
      renderWithTheme(
        <AppLayout>
          <div data-testid="main-content">Main content</div>
        </AppLayout>
      )
      const main = screen.getByRole('main')
      const content = within(main).getByTestId('main-content')
      expect(content).toBeTruthy()
    })
  })
})

// ===================================
// AUTHLAYOUT COMPONENT TESTS
// ===================================

describe('AuthLayout Component', () => {
  it('renders auth layout with children', () => {
    renderWithTheme(
      <AuthLayout>
        <form>Login form</form>
      </AuthLayout>
    )
    expect(screen.getByText('Login form')).toBeTruthy()
  })

  describe('Title and Subtitle', () => {
    it('renders title when provided', () => {
      renderWithTheme(
        <AuthLayout title="Sign In">
          <form>Form</form>
        </AuthLayout>
      )
      expect(screen.getByText('Sign In')).toBeTruthy()
    })

    it('renders subtitle when provided', () => {
      renderWithTheme(
        <AuthLayout subtitle="Welcome back">
          <form>Form</form>
        </AuthLayout>
      )
      expect(screen.getByText('Welcome back')).toBeTruthy()
    })

    it('renders both title and subtitle', () => {
      renderWithTheme(
        <AuthLayout title="Sign In" subtitle="Welcome back">
          <form>Form</form>
        </AuthLayout>
      )
      expect(screen.getByText('Sign In')).toBeTruthy()
      expect(screen.getByText('Welcome back')).toBeTruthy()
    })
  })

  describe('Logo', () => {
    it('renders logo when provided', () => {
      renderWithTheme(
        <AuthLayout logo={<div data-testid="logo">Logo</div>}>
          <form>Form</form>
        </AuthLayout>
      )
      expect(screen.getByTestId('logo')).toBeTruthy()
    })
  })

  describe('Layout Structure', () => {
    it('centers content in card', () => {
      const { container } = renderWithTheme(
        <AuthLayout>
          <form>Form</form>
        </AuthLayout>
      )
      const card = container.querySelector('.auth-layout__card')
      expect(card).toBeTruthy()
    })
  })
})
