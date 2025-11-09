import { ReactNode, useState, CSSProperties } from 'react'
import { Skeleton } from './Skeleton'
import './Image.css'

/**
 * Image Atom
 *
 * Enhanced image component with loading and error states
 * - Loading state with skeleton placeholder
 * - Error state with custom fallback
 * - Lazy loading support
 * - Object-fit control for responsive images
 * - Customizable dimensions
 * - Lifecycle callbacks (onLoad, onError)
 */

export interface ImageProps {
  src: string
  alt: string
  width?: number | string
  height?: number | string
  loading?: 'lazy' | 'eager'
  objectFit?: 'cover' | 'contain' | 'fill' | 'none'
  fallback?: ReactNode
  onLoad?: () => void
  onError?: () => void
  className?: string
}

export function Image({
  src,
  alt,
  width,
  height,
  loading = 'lazy',
  objectFit,
  fallback,
  onLoad,
  onError,
  className = '',
}: ImageProps) {
  const [state, setState] = useState<'loading' | 'loaded' | 'error'>('loading')

  const handleLoad = () => {
    setState('loaded')
    onLoad?.()
  }

  const handleError = () => {
    setState('error')
    onError?.()
  }

  const containerClasses = ['image', className].filter(Boolean).join(' ')

  const imgClasses = [
    'image__img',
    objectFit && `image__img--${objectFit}`,
    state === 'loaded' && 'image__img--loaded',
  ]
    .filter(Boolean)
    .join(' ')

  const containerStyle: CSSProperties = {}

  if (width !== undefined) {
    containerStyle.width = typeof width === 'number' ? `${width}px` : width
  }

  if (height !== undefined) {
    containerStyle.height = typeof height === 'number' ? `${height}px` : height
  }

  return (
    <div className={containerClasses} style={containerStyle}>
      {state === 'loading' && (
        <Skeleton variant="rectangular" width="100%" height="100%" />
      )}
      {state === 'error' && fallback && (
        <div className="image__fallback">{fallback}</div>
      )}
      <img
        src={src}
        alt={alt}
        loading={loading}
        className={imgClasses}
        onLoad={handleLoad}
        onError={handleError}
        style={{ display: state === 'loaded' ? 'block' : 'none' }}
      />
    </div>
  )
}

Image.displayName = 'Image'
