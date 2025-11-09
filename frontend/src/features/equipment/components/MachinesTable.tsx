/**
 * MachinesTable Component
 *
 * Table component for displaying list of machines
 */
import './MachinesTable.css'
import type { Machine } from '../types/machine.types'

interface MachinesTableProps {
  machines: Machine[]
  isLoading?: boolean
  onEdit?: (machine: Machine) => void
  onDelete?: (machine: Machine) => void
  onRowClick?: (machine: Machine) => void
  onStatusChange?: (machine: Machine) => void
}

export function MachinesTable({
  machines,
  isLoading = false,
  onEdit,
  onDelete,
  onRowClick,
  onStatusChange,
}: MachinesTableProps) {
  if (isLoading) {
    return <div data-testid="loading-skeleton">Loading...</div>
  }

  if (machines.length === 0) {
    return <div>No machines found</div>
  }

  return (
    <table className="machines-table">
      <thead>
        <tr>
          <th>Machine Code</th>
          <th>Machine Name</th>
          <th>Description</th>
          <th>Status</th>
          <th>Active</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {machines.map((machine) => (
          <tr key={machine.id} onClick={() => onRowClick?.(machine)}>
            <td>{machine.machine_code}</td>
            <td>{machine.machine_name}</td>
            <td>{machine.description}</td>
            <td>
              <span
                className={`status-badge status-${machine.status.toLowerCase()} ${
                  machine.status === 'RUNNING' ? 'status-pulse' : ''
                }`}
              >
                {machine.status}
              </span>
            </td>
            <td>{machine.is_active ? 'Active' : 'Inactive'}</td>
            <td>
              <button onClick={(e) => { e.stopPropagation(); onEdit?.(machine) }}>
                Edit
              </button>
              <button onClick={(e) => { e.stopPropagation(); onDelete?.(machine) }}>
                Delete
              </button>
              <button onClick={(e) => { e.stopPropagation(); onStatusChange?.(machine) }}>
                Change Status
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
