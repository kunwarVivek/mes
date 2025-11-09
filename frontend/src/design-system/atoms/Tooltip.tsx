import { ReactNode, useState, useRef, useEffect, cloneElement, isValidElement } from 'react'
import './Tooltip.css'

/**
 * Tooltip Atom
 *
 * Popover tooltip component:
 * - Single Responsibility: Contextual help on hover/click/focus
 * - Accessibility: role="tooltip", aria-describedby
 * - Placement options: top, bottom, left, right
 * - Configurable trigger and delay
 */

export interface TooltipProps {
  content: ReactNode
  children: ReactNode
  placement?: 'top' | 'bottom' | 'left' | 'right'
  trigger?: 'hover' | 'click' | 'focus'
  delay?: number // Show delay in ms (default 300)
  className?: string
}

export const Tooltip = ({
  content,
  children,
  placement = 'top',
  trigger = 'hover',
  delay = 300,
  className = '',
}: TooltipProps) => {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipId] = useState(() => `tooltip-${Math.random().toString(36).substr(2, 9)}`)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const triggerRef = useRef<HTMLElement>(null)

  const showTooltip = (immediate = false) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    if (immediate) {
      setIsVisible(true)
    } else {
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true)
      }, delay)
    }
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  const toggleTooltip = () => {
    if (isVisible) {
      hideTooltip()
    } else {
      showTooltip(true) // Show immediately on click
    }
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const getTriggerProps = () => {
    const baseProps = {
      ref: triggerRef,
      'aria-describedby': isVisible ? tooltipId : undefined,
    }

    if (trigger === 'hover') {
      return {
        ...baseProps,
        onMouseEnter: () => showTooltip(false), // Use delay for hover
        onMouseLeave: hideTooltip,
      }
    }

    if (trigger === 'click') {
      return {
        ...baseProps,
        onClick: toggleTooltip,
      }
    }

    if (trigger === 'focus') {
      return {
        ...baseProps,
        onFocus: () => showTooltip(true), // Show immediately on focus
        onBlur: hideTooltip,
      }
    }

    return baseProps
  }

  const triggerProps = getTriggerProps()

  // Clone the child element and add trigger props
  const triggerElement = isValidElement(children)
    ? cloneElement(children as React.ReactElement<any>, triggerProps)
    : children

  const tooltipClasses = [
    'tooltip',
    `tooltip--${placement}`,
    isVisible && 'tooltip--visible',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="tooltip-wrapper">
      {triggerElement}
      {isVisible && (
        <div
          id={tooltipId}
          role="tooltip"
          className={tooltipClasses}
          aria-hidden={!isVisible}
        >
          <div className="tooltip__content">{content}</div>
          <div className={`tooltip__arrow tooltip__arrow--${placement}`} />
        </div>
      )}
    </div>
  )
}

Tooltip.displayName = 'Tooltip'
