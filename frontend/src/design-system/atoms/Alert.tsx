import { ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'

/**
 * Alert Component
 *
 * Display contextual feedback messages:
 * - Variants: default, destructive, success, info
 * - Auto-includes appropriate icon
 * - Supports custom children
 */

interface AlertProps {
  variant?: 'default' | 'destructive' | 'success' | 'info'
  children: ReactNode
  className?: string
}

export function Alert({ variant = 'default', children, className = '' }: AlertProps) {
  const variants = {
    default: 'bg-gray-50 border-gray-200 text-gray-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  return (
    <div
      className={`flex items-start gap-3 p-4 border rounded-lg ${variants[variant]} ${className}`}
      role="alert"
    >
      {children}
    </div>
  )
}

interface AlertDescriptionProps {
  children: ReactNode
  className?: string
}

export function AlertDescription({ children, className = '' }: AlertDescriptionProps) {
  return <div className={`text-sm ${className}`}>{children}</div>
}
