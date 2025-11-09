import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Configuration options for camera initialization
 */
export interface UseCameraOptions {
  /** Camera facing mode - 'user' for front camera, 'environment' for rear camera */
  facingMode?: 'user' | 'environment'
  /** Ideal video width */
  width?: number
  /** Ideal video height */
  height?: number
}

/**
 * Return type for useCamera hook
 */
export interface UseCameraReturn {
  /** Active media stream or null */
  stream: MediaStream | null
  /** Last error encountered or null */
  error: Error | null
  /** Camera permission status - null if not requested yet */
  hasPermission: boolean | null
  /** True when photo capture is in progress */
  isCapturing: boolean
  /** Request camera access with optional configuration */
  requestCamera: (options?: UseCameraOptions) => Promise<MediaStream>
  /** Stop camera and release resources */
  stopCamera: () => void
  /** Capture photo from video element and return data URL */
  capturePhoto: (videoElement: HTMLVideoElement) => Promise<string>
}

/**
 * Hook for managing camera access and photo capture in PWA
 *
 * @example
 * ```tsx
 * const { requestCamera, capturePhoto, stopCamera, error } = useCamera()
 *
 * // Request camera access
 * const stream = await requestCamera({ facingMode: 'environment' })
 * videoRef.current.srcObject = stream
 *
 * // Capture photo
 * const dataUrl = await capturePhoto(videoRef.current)
 *
 * // Cleanup
 * stopCamera()
 * ```
 */
export function useCamera(): UseCameraReturn {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [isCapturing, setIsCapturing] = useState(false)

  // Use ref to track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true)

  /**
   * Request camera access with specified constraints
   */
  const requestCamera = useCallback(
    async (options: UseCameraOptions = {}): Promise<MediaStream> => {
      try {
        // Validate input constraints to prevent malicious values
        const MAX_DIMENSION = 3840 // 4K max
        const validWidth = options.width && options.width > 0 && options.width <= MAX_DIMENSION
          ? options.width
          : undefined
        const validHeight = options.height && options.height > 0 && options.height <= MAX_DIMENSION
          ? options.height
          : undefined

        const constraints: MediaStreamConstraints = {
          video: {
            facingMode: options.facingMode || 'environment',
            ...(validWidth && { width: { ideal: validWidth } }),
            ...(validHeight && { height: { ideal: validHeight } }),
          },
        }

        const mediaStream = await navigator.mediaDevices.getUserMedia(
          constraints
        )

        if (isMountedRef.current) {
          setStream(mediaStream)
          setHasPermission(true)
          setError(null)
        }

        return mediaStream
      } catch (err) {
        const cameraError = err instanceof Error ? err : new Error(String(err))

        if (isMountedRef.current) {
          setError(cameraError)
          setHasPermission(false)
          setStream(null)
        }

        throw cameraError
      }
    },
    []
  )

  /**
   * Stop camera stream and release all tracks
   */
  const stopCamera = useCallback(() => {
    // Check stream at runtime instead of dependency to maintain stable reference
    setStream((currentStream) => {
      if (currentStream) {
        currentStream.getTracks().forEach((track) => track.stop())
      }
      return null
    })
  }, [])

  /**
   * Capture photo from video element and return as data URL
   * Validates data URL format for security
   */
  const capturePhoto = useCallback(
    async (videoElement: HTMLVideoElement): Promise<string> => {
      if (!stream) {
        throw new Error('Camera stream not initialized')
      }

      if (!videoElement || !videoElement.videoWidth || !videoElement.videoHeight) {
        throw new Error('Invalid video element or video not ready')
      }

      if (isMountedRef.current) {
        setIsCapturing(true)
      }

      try {
        const canvas = document.createElement('canvas')
        canvas.width = videoElement.videoWidth
        canvas.height = videoElement.videoHeight

        const context = canvas.getContext('2d')
        if (!context) {
          throw new Error('Failed to get canvas context')
        }

        context.drawImage(
          videoElement,
          0,
          0,
          videoElement.videoWidth,
          videoElement.videoHeight
        )

        const dataUrl = canvas.toDataURL('image/png')

        // Validate data URL format for security - whitelist safe MIME types
        // This prevents XSS attacks from SVG images with embedded scripts
        const SAFE_MIME_TYPES = ['data:image/png', 'data:image/jpeg', 'data:image/webp']
        const isSafeMimeType = SAFE_MIME_TYPES.some(type => dataUrl.startsWith(type))

        if (!isSafeMimeType) {
          throw new Error('Invalid data URL format: unsafe MIME type')
        }

        return dataUrl
      } finally {
        if (isMountedRef.current) {
          setIsCapturing(false)
        }
      }
    },
    [stream]
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [stream])

  return {
    stream,
    error,
    hasPermission,
    isCapturing,
    requestCamera,
    stopCamera,
    capturePhoto,
  }
}
