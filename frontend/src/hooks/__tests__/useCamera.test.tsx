import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCamera } from '../useCamera'

describe('useCamera', () => {
  let mockStream: MediaStream
  let mockGetUserMedia: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Create mock MediaStream with tracks
    const mockTrack = {
      stop: vi.fn(),
      kind: 'video',
      id: 'mock-track-id',
      label: 'mock camera',
      enabled: true,
      muted: false,
      readyState: 'live',
    } as unknown as MediaStreamTrack

    mockStream = {
      getTracks: vi.fn(() => [mockTrack]),
      getVideoTracks: vi.fn(() => [mockTrack]),
      getAudioTracks: vi.fn(() => []),
      active: true,
    } as unknown as MediaStream

    // Mock getUserMedia
    mockGetUserMedia = vi.fn().mockResolvedValue(mockStream)
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: mockGetUserMedia,
      },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with null stream and no error', () => {
    const { result } = renderHook(() => useCamera())

    expect(result.current.stream).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.hasPermission).toBeNull()
  })

  it('should request camera access successfully', async () => {
    const { result } = renderHook(() => useCamera())

    let streamResult: MediaStream | undefined
    await act(async () => {
      streamResult = await result.current.requestCamera()
    })

    expect(mockGetUserMedia).toHaveBeenCalledWith({
      video: { facingMode: 'environment' },
    })
    expect(result.current.stream).toBe(mockStream)
    expect(result.current.hasPermission).toBe(true)
    expect(result.current.error).toBeNull()
    expect(streamResult).toBe(mockStream)
  })

  it('should handle camera access denial', async () => {
    const mockError = new Error('Permission denied')
    mockGetUserMedia.mockRejectedValueOnce(mockError)

    const { result } = renderHook(() => useCamera())

    await act(async () => {
      try {
        await result.current.requestCamera()
      } catch (err) {
        expect(err).toBe(mockError)
      }
    })

    expect(result.current.stream).toBeNull()
    expect(result.current.hasPermission).toBe(false)
    expect(result.current.error).toBe(mockError)
  })

  it('should stop camera and clean up tracks', async () => {
    const { result } = renderHook(() => useCamera())

    await act(async () => {
      await result.current.requestCamera()
    })

    expect(result.current.stream).toBe(mockStream)

    act(() => {
      result.current.stopCamera()
    })

    const tracks = mockStream.getTracks()
    expect(tracks[0].stop).toHaveBeenCalled()
    expect(result.current.stream).toBeNull()
  })

  it('should handle stopCamera when no stream exists', () => {
    const { result } = renderHook(() => useCamera())

    expect(() => {
      act(() => {
        result.current.stopCamera()
      })
    }).not.toThrow()

    expect(result.current.stream).toBeNull()
  })

  it('should request rear camera on mobile devices', async () => {
    const { result } = renderHook(() => useCamera())

    await act(async () => {
      await result.current.requestCamera()
    })

    expect(mockGetUserMedia).toHaveBeenCalledWith(
      expect.objectContaining({
        video: expect.objectContaining({
          facingMode: 'environment',
        }),
      })
    )
  })

  it('should capture photo and return data URL', async () => {
    const { result } = renderHook(() => useCamera())

    // Mock canvas and image capture
    const mockCanvas = document.createElement('canvas')
    const mockContext = {
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D
    vi.spyOn(document, 'createElement').mockReturnValue(mockCanvas)
    vi.spyOn(mockCanvas, 'getContext').mockReturnValue(mockContext)
    vi.spyOn(mockCanvas, 'toDataURL').mockReturnValue('data:image/png;base64,mockImageData')

    // Create mock video element
    const mockVideo = document.createElement('video')
    Object.defineProperty(mockVideo, 'videoWidth', { value: 1920 })
    Object.defineProperty(mockVideo, 'videoHeight', { value: 1080 })

    // Request camera first
    await act(async () => {
      await result.current.requestCamera()
    })

    let photoDataUrl: string | undefined
    await act(async () => {
      photoDataUrl = await result.current.capturePhoto(mockVideo)
    })

    expect(result.current.isCapturing).toBe(false)
    expect(photoDataUrl).toBe('data:image/png;base64,mockImageData')
    expect(mockContext.drawImage).toHaveBeenCalledWith(mockVideo, 0, 0, 1920, 1080)
  })

  it('should handle capture errors when no stream exists', async () => {
    const { result } = renderHook(() => useCamera())

    await expect(async () => {
      await act(async () => {
        const mockVideo = document.createElement('video')
        await result.current.capturePhoto(mockVideo)
      })
    }).rejects.toThrow('Camera stream not initialized')
  })

  it('should set isCapturing state during photo capture', async () => {
    const { result } = renderHook(() => useCamera())

    const mockCanvas = document.createElement('canvas')
    const mockContext = {
      drawImage: vi.fn(),
    } as unknown as CanvasRenderingContext2D
    vi.spyOn(document, 'createElement').mockReturnValue(mockCanvas)
    vi.spyOn(mockCanvas, 'getContext').mockReturnValue(mockContext)
    vi.spyOn(mockCanvas, 'toDataURL').mockReturnValue('data:image/png;base64,test')

    const mockVideo = {
      videoWidth: 640,
      videoHeight: 480,
    } as HTMLVideoElement

    await act(async () => {
      await result.current.requestCamera()
    })

    // Verify initial state
    expect(result.current.isCapturing).toBe(false)

    // Capture photo
    await act(async () => {
      await result.current.capturePhoto(mockVideo)
    })

    // Should return to false after capture
    expect(result.current.isCapturing).toBe(false)
  })

  it('should cleanup on unmount', async () => {
    const { result, unmount } = renderHook(() => useCamera())

    await act(async () => {
      await result.current.requestCamera()
    })

    const tracks = mockStream.getTracks()

    unmount()

    expect(tracks[0].stop).toHaveBeenCalled()
  })
})
