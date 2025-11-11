import { ReactNode, SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'

/**
 * Select Component
 *
 * Dropdown select with ShadCN-like API:
 * - Select (wrapper)
 * - SelectTrigger (button/input)
 * - SelectValue (placeholder/value display)
 * - SelectContent (dropdown menu)
 * - SelectItem (option)
 */

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children: ReactNode
  className?: string
}

export function Select({ value, onValueChange, children, className = '' }: SelectProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Simple native select for MVP */}
      <select
        value={value}
        onChange={(e) => onValueChange?.(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white pr-10"
      >
        {children}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
    </div>
  )
}

interface SelectTriggerProps {
  children: ReactNode
  className?: string
}

export function SelectTrigger({ children, className = '' }: SelectTriggerProps) {
  return <div className={className}>{children}</div>
}

interface SelectValueProps {
  placeholder?: string
}

export function SelectValue({ placeholder }: SelectValueProps) {
  return <span className="text-gray-500">{placeholder}</span>
}

interface SelectContentProps {
  children: ReactNode
}

export function SelectContent({ children }: SelectContentProps) {
  return <>{children}</>
}

interface SelectItemProps {
  value: string
  children: ReactNode
}

export function SelectItem({ value, children }: SelectItemProps) {
  return <option value={value}>{children}</option>
}
