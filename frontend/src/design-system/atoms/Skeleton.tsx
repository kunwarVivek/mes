import { CSSProperties } from 'react'
import './Skeleton.css'

/**
 * Skeleton Atom
 *
 * Loading placeholder component with animations
 * - Multiple shape variants (text, circular, rectangular)
 * - Customizable dimensions
 * - Pulse and wave animation options
 */

export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular'
  width?: number | string
  height?: number | string
  animation?: 'pulse' | 'wave' | 'none'
  className?: string
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  animation = 'pulse',
  className = '',
}: SkeletonProps) {
  const classes = [
    'skeleton',
    `skeleton--${variant}`,
    animation !== 'none' && `skeleton--${animation}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')

  const styles: CSSProperties = {}

  if (width !== undefined) {
    styles.width = typeof width === 'number' ? `${width}px` : width
  }

  if (height !== undefined) {
    styles.height = typeof height === 'number' ? `${height}px` : height
  }

  return <div className={classes} style={styles} aria-hidden="true" data-testid="skeleton" />
}

Skeleton.displayName = 'Skeleton'
