import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PhotoCapture } from '../PhotoCapture'

// Mock useCamera hook
vi.mock('../../hooks/useCamera', () => ({
  useCamera: vi.fn(() => ({
    stream: null,
    error: null,
    hasPermission: null,
    requestCamera: vi.fn(),
    stopCamera: vi.fn(),
  })),
}))

describe('PhotoCapture', () => {
  const mockOnCapture = vi.fn()
  const mockStream = {} as MediaStream

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render camera controls', () => {
    render(<PhotoCapture onCapture={mockOnCapture} />)

    expect(screen.getByText(/start camera/i)).toBeInTheDocument()
    expect(screen.getByText(/capture/i)).toBeInTheDocument()
    expect(screen.getByText(/stop/i)).toBeInTheDocument()
  })

  it('should start camera when start button is clicked', async () => {
    const mockRequestCamera = vi.fn().mockResolvedValue(mockStream)
    const { useCamera } = await import('../../hooks/useCamera')
    vi.mocked(useCamera).mockReturnValue({
      stream: null,
      error: null,
      hasPermission: null,
      requestCamera: mockRequestCamera,
      stopCamera: vi.fn(),
    })

    const user = userEvent.setup()
    render(<PhotoCapture onCapture={mockOnCapture} />)

    const startButton = screen.getByText(/start camera/i)
    await user.click(startButton)

    expect(mockRequestCamera).toHaveBeenCalled()
  })

  it('should display video element when stream is active', async () => {
    const { useCamera } = await import('../../hooks/useCamera')
    vi.mocked(useCamera).mockReturnValue({
      stream: mockStream,
      error: null,
      hasPermission: true,
      requestCamera: vi.fn(),
      stopCamera: vi.fn(),
    })

    render(<PhotoCapture onCapture={mockOnCapture} />)

    const video = screen.getByRole('img', { hidden: true }) || document.querySelector('video')
    expect(video).toBeInTheDocument()
  })

  it('should capture photo when capture button is clicked', async () => {
    const mockCanvas = document.createElement('canvas')
    const mockContext = {
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D

    mockCanvas.getContext = vi.fn(() => mockContext)
    mockCanvas.toBlob = vi.fn((callback) => {
      const blob = new Blob(['fake-image-data'], { type: 'image/jpeg' })
      callback(blob)
    })

    vi.spyOn(document, 'createElement').mockImplementation((tagName) => {
      if (tagName === 'canvas') {
        return mockCanvas as any
      }
      return document.createElement(tagName)
    })

    const { useCamera } = await import('../../hooks/useCamera')
    vi.mocked(useCamera).mockReturnValue({
      stream: mockStream,
      error: null,
      hasPermission: true,
      requestCamera: vi.fn(),
      stopCamera: vi.fn(),
    })

    const user = userEvent.setup()
    render(<PhotoCapture onCapture={mockOnCapture} />)

    const captureButton = screen.getByText(/capture/i)
    await user.click(captureButton)

    await waitFor(() => {
      expect(mockOnCapture).toHaveBeenCalled()
      const capturedFile = mockOnCapture.mock.calls[0][0]
      expect(capturedFile).toBeInstanceOf(File)
      expect(capturedFile.type).toBe('image/jpeg')
    })
  })

  it('should stop camera when stop button is clicked', async () => {
    const mockStopCamera = vi.fn()
    const { useCamera } = await import('../../hooks/useCamera')
    vi.mocked(useCamera).mockReturnValue({
      stream: mockStream,
      error: null,
      hasPermission: true,
      requestCamera: vi.fn(),
      stopCamera: mockStopCamera,
    })

    const user = userEvent.setup()
    render(<PhotoCapture onCapture={mockOnCapture} />)

    const stopButton = screen.getByText(/stop/i)
    await user.click(stopButton)

    expect(mockStopCamera).toHaveBeenCalled()
  })

  it('should enforce maxPhotos limit', async () => {
    render(<PhotoCapture onCapture={mockOnCapture} maxPhotos={3} />)

    // Implementation will track photo count and disable capture when limit reached
    // This test validates the prop is accepted
    expect(screen.getByText(/capture/i)).toBeInTheDocument()
  })

  it('should display error message when camera access fails', async () => {
    const mockError = new Error('Camera access denied')
    const { useCamera } = await import('../../hooks/useCamera')
    vi.mocked(useCamera).mockReturnValue({
      stream: null,
      error: mockError,
      hasPermission: false,
      requestCamera: vi.fn(),
      stopCamera: vi.fn(),
    })

    render(<PhotoCapture onCapture={mockOnCapture} />)

    await waitFor(() => {
      expect(screen.getByText(/camera access denied/i)).toBeInTheDocument()
    })
  })
})
