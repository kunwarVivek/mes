import { ReactNode, useState } from 'react'
import './Avatar.css'

/**
 * Avatar Atom
 *
 * User profile image component with fallback support
 * - Multiple size variants from xs (24px) to xl (80px)
 * - Circle or square shapes with rounded corners
 * - Status indicator for online/offline/away/busy
 * - Automatic fallback to initials or custom content on error
 * - Accessible with proper alt text
 */

export interface AvatarProps {
  src?: string
  alt: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  fallback?: ReactNode
  shape?: 'circle' | 'square'
  status?: 'online' | 'offline' | 'away' | 'busy'
  className?: string
}

export function Avatar({
  src,
  alt,
  size = 'md',
  fallback,
  shape = 'circle',
  status,
  className = '',
}: AvatarProps) {
  const [imageError, setImageError] = useState(false)

  const handleError = () => {
    setImageError(true)
  }

  const showFallback = !src || imageError

  const classes = [
    'avatar',
    `avatar--${size}`,
    `avatar--${shape}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes}>
      {showFallback ? (
        <div className="avatar__fallback">
          {fallback || alt.charAt(0).toUpperCase()}
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          className="avatar__img"
          onError={handleError}
        />
      )}
      {status && (
        <span
          className={`avatar__status avatar__status--${status}`}
          aria-label={`Status: ${status}`}
        />
      )}
    </div>
  )
}

Avatar.displayName = 'Avatar'
