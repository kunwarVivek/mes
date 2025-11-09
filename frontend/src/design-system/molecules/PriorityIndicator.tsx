import * as React from 'react'
import { Badge } from '@/components/ui/badge'
import { ArrowUp, ArrowDown, Minus, AlertTriangle } from 'lucide-react'

type Priority = 'low' | 'medium' | 'high' | 'critical'

interface PriorityIndicatorProps {
  priority: Priority
  withLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const priorityConfig = {
  low: {
    icon: ArrowDown,
    variant: 'secondary' as const,
    label: 'Low',
    color: 'text-gray-600'
  },
  medium: {
    icon: Minus,
    variant: 'default' as const,
    label: 'Medium',
    color: 'text-blue-600'
  },
  high: {
    icon: ArrowUp,
    variant: 'secondary' as const,
    label: 'High',
    color: 'text-orange-600'
  },
  critical: {
    icon: AlertTriangle,
    variant: 'destructive' as const,
    label: 'Critical',
    color: 'text-red-600'
  },
}

export function PriorityIndicator({
  priority,
  withLabel,
  size = 'md'
}: PriorityIndicatorProps) {
  const config = priorityConfig[priority]
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <Icon className="h-3 w-3" />
      {withLabel && <span>{config.label}</span>}
    </Badge>
  )
}
