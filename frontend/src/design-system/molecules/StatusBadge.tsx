import * as React from 'react'
import { Badge } from '@/components/ui/badge'
import { Circle } from 'lucide-react'
import { cn } from '@/lib/utils'

type MachineStatus = 'running' | 'idle' | 'down' | 'maintenance' | 'setup'
type WorkOrderStatus = 'planned' | 'released' | 'in_progress' | 'completed' | 'cancelled'
type QualityStatus = 'pass' | 'fail' | 'pending'
type NCRStatus = 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'CLOSED'

type Status = MachineStatus | WorkOrderStatus | QualityStatus | NCRStatus

interface StatusBadgeProps {
  status: Status
  withIcon?: boolean
  withPulse?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const statusConfig = {
  // Machine statuses
  running: { variant: 'default' as const, label: 'Running', color: 'text-green-600', pulse: true },
  idle: { variant: 'secondary' as const, label: 'Idle', color: 'text-yellow-600' },
  down: { variant: 'destructive' as const, label: 'Down', color: 'text-red-600' },
  maintenance: { variant: 'default' as const, label: 'Maintenance', color: 'text-blue-600' },
  setup: { variant: 'secondary' as const, label: 'Setup', color: 'text-gray-600' },

  // Work order statuses
  planned: { variant: 'secondary' as const, label: 'Planned' },
  released: { variant: 'default' as const, label: 'Released' },
  in_progress: { variant: 'default' as const, label: 'In Progress', pulse: true },
  completed: { variant: 'default' as const, label: 'Completed' },
  cancelled: { variant: 'destructive' as const, label: 'Cancelled' },

  // Quality statuses
  pass: { variant: 'default' as const, label: 'Pass' },
  fail: { variant: 'destructive' as const, label: 'Fail' },
  pending: { variant: 'secondary' as const, label: 'Pending' },

  // NCR statuses
  OPEN: { variant: 'destructive' as const, label: 'Open' },
  IN_REVIEW: { variant: 'default' as const, label: 'In Review' },
  RESOLVED: { variant: 'default' as const, label: 'Resolved' },
  CLOSED: { variant: 'secondary' as const, label: 'Closed' },
}

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
}

export function StatusBadge({
  status,
  withIcon,
  withPulse,
  size = 'md',
  className
}: StatusBadgeProps) {
  const config = statusConfig[status]
  const shouldPulse = withPulse && config.pulse

  return (
    <Badge variant={config.variant} className={cn(sizeClasses[size], className)}>
      {withIcon && (
        <Circle
          className={cn(
            'h-3 w-3 fill-current mr-1',
            shouldPulse && 'animate-pulse'
          )}
        />
      )}
      <span>{config.label}</span>
    </Badge>
  )
}
