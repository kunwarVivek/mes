/**
 * MachineStatusCard Component
 *
 * Real-time machine status display card
 */
import './MachineStatusCard.css'
import type { Machine } from '../types/machine.types'

interface MachineStatusCardProps {
  machine: Machine
  onClick?: (machine: Machine) => void
  onStatusChange?: (machine: Machine) => void
  compact?: boolean
  isLoading?: boolean
}

export function MachineStatusCard({
  machine,
  onClick,
  onStatusChange,
  compact = false,
  isLoading = false,
}: MachineStatusCardProps) {
  if (isLoading) {
    return <div data-testid="loading-skeleton">Loading...</div>
  }

  return (
    <div
      className={`machine-status-card ${compact ? 'compact' : ''}`}
      onClick={() => onClick?.(machine)}
    >
      <div className="card-header">
        <h3>{machine.machine_code}</h3>
        {!machine.is_active && <span className="inactive-badge">Inactive</span>}
      </div>

      <div className="card-body">
        <p className="machine-name">{machine.machine_name}</p>
        <span
          className={`status-badge status-${machine.status.toLowerCase()} ${
            machine.status === 'RUNNING' ? 'status-pulse' : ''
          }`}
        >
          {machine.status}
        </span>
      </div>

      {onStatusChange && (
        <div className="card-actions">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onStatusChange(machine)
            }}
          >
            Change Status
          </button>
        </div>
      )}
    </div>
  )
}
