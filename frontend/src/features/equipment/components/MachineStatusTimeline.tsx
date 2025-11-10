/**
 * MachineStatusTimeline Component
 *
 * Displays machine status history as a visual timeline
 */
import type { MachineStatusHistory } from '../types/machine.types'

interface MachineStatusTimelineProps {
  history: MachineStatusHistory[]
  isLoading?: boolean
}

export function MachineStatusTimeline({ history, isLoading = false }: MachineStatusTimelineProps) {
  if (isLoading) {
    return (
      <div className="text-center py-4">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-sm text-gray-600">Loading history...</p>
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No status history available</p>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-green-500'
      case 'IDLE':
        return 'bg-yellow-500'
      case 'DOWN':
        return 'bg-red-500'
      case 'SETUP':
        return 'bg-blue-500'
      case 'MAINTENANCE':
        return 'bg-purple-500'
      case 'AVAILABLE':
        return 'bg-gray-400'
      default:
        return 'bg-gray-400'
    }
  }

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'Ongoing'
    if (minutes < 60) return `${Math.round(minutes)}m`
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return `${hours}h ${mins}m`
  }

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>

      {/* Timeline items */}
      <div className="space-y-4">
        {history.map((record, index) => (
          <div key={record.id} className="relative pl-10">
            {/* Status dot */}
            <div
              className={`absolute left-2 top-1.5 w-4 h-4 rounded-full ${getStatusColor(
                record.status
              )} ring-4 ring-white`}
            ></div>

            {/* Content */}
            <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium text-white ${getStatusColor(
                      record.status
                    )}`}
                  >
                    {record.status}
                  </span>
                  {index === 0 && (
                    <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      Current
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-600">
                  {formatDuration(record.duration_minutes)}
                </div>
              </div>

              <div className="text-sm text-gray-700">
                <p>
                  <span className="font-medium">Started:</span> {formatDateTime(record.started_at)}
                </p>
                {record.ended_at && (
                  <p>
                    <span className="font-medium">Ended:</span> {formatDateTime(record.ended_at)}
                  </p>
                )}
              </div>

              {record.notes && (
                <div className="mt-2 text-sm text-gray-600 italic">
                  <p>{record.notes}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
