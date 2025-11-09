import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { InstallPrompt } from '../InstallPrompt'

describe('InstallPrompt', () => {
  let mockDeferredPrompt: {
    prompt: ReturnType<typeof vi.fn>
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockDeferredPrompt = {
      prompt: vi.fn(),
      userChoice: Promise.resolve({ outcome: 'accepted' as const }),
    }
  })

  it('should not render initially when no install prompt event', () => {
    const { container } = render(<InstallPrompt />)
    expect(container.firstChild).toBeNull()
  })

  it('should render when beforeinstallprompt event fires', async () => {
    const { rerender } = render(<InstallPrompt />)

    // Simulate beforeinstallprompt event
    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)

    window.dispatchEvent(event)
    rerender(<InstallPrompt />)

    await waitFor(() => {
      expect(screen.getByText(/install unison mes for offline access/i)).toBeInTheDocument()
    })
  })

  it('should call prompt when install button is clicked', async () => {
    const { rerender } = render(<InstallPrompt />)

    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)
    window.dispatchEvent(event)
    rerender(<InstallPrompt />)

    await waitFor(() => {
      expect(screen.getByText(/install/i)).toBeInTheDocument()
    })

    const user = userEvent.setup()
    const installButton = screen.getByRole('button', { name: /install/i })
    await user.click(installButton)

    await waitFor(() => {
      expect(mockDeferredPrompt.prompt).toHaveBeenCalled()
    })
  })

  it('should hide prompt when dismiss button is clicked', async () => {
    const { rerender } = render(<InstallPrompt />)

    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)
    window.dispatchEvent(event)
    rerender(<InstallPrompt />)

    await waitFor(() => {
      expect(screen.getByText(/dismiss/i)).toBeInTheDocument()
    })

    const user = userEvent.setup()
    const dismissButton = screen.getByRole('button', { name: /dismiss/i })
    await user.click(dismissButton)

    await waitFor(() => {
      expect(screen.queryByText(/install unison mes/i)).not.toBeInTheDocument()
    })
  })

  it('should hide prompt after successful install', async () => {
    const { rerender } = render(<InstallPrompt />)

    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)
    window.dispatchEvent(event)
    rerender(<InstallPrompt />)

    const user = userEvent.setup()
    const installButton = screen.getByRole('button', { name: /install/i })
    await user.click(installButton)

    await waitFor(() => {
      expect(screen.queryByText(/install unison mes/i)).not.toBeInTheDocument()
    })
  })

  it('should prevent default on beforeinstallprompt event', async () => {
    render(<InstallPrompt />)

    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)

    window.dispatchEvent(event)

    await waitFor(() => {
      expect(event.preventDefault).toHaveBeenCalled()
    })
  })

  it('should log install outcome', async () => {
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    const { rerender } = render(<InstallPrompt />)

    const event = new Event('beforeinstallprompt') as any
    event.preventDefault = vi.fn()
    Object.assign(event, mockDeferredPrompt)
    window.dispatchEvent(event)
    rerender(<InstallPrompt />)

    const user = userEvent.setup()
    const installButton = screen.getByRole('button', { name: /install/i })
    await user.click(installButton)

    await waitFor(() => {
      expect(consoleLogSpy).toHaveBeenCalledWith('Install outcome:', 'accepted')
    })

    consoleLogSpy.mockRestore()
  })
})
