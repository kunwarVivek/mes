/**
 * PMSchedulesTable Component
 *
 * Table view for PM schedules with filtering and actions
 */
import React, { useMemo } from 'react'
import type { PMSchedule } from '../types/maintenance.types'
import './PMSchedulesTable.css'

interface PMSchedulesTableProps {
  schedules: PMSchedule[]
  isLoading: boolean
  searchTerm?: string
  onEdit?: (schedule: PMSchedule) => void
  onDelete?: (schedule: PMSchedule) => void
}

export const PMSchedulesTable: React.FC<PMSchedulesTableProps> = ({
  schedules,
  isLoading,
  searchTerm = '',
  onEdit,
  onDelete,
}) => {
  const filteredSchedules = useMemo(() => {
    if (!searchTerm) return schedules

    const term = searchTerm.toLowerCase()
    return schedules.filter(
      (schedule) =>
        schedule.schedule_code.toLowerCase().includes(term) ||
        schedule.schedule_name.toLowerCase().includes(term)
    )
  }, [schedules, searchTerm])

  if (isLoading) {
    return <div className="pm-schedules-table__loading">Loading PM schedules...</div>
  }

  if (filteredSchedules.length === 0) {
    return <div className="pm-schedules-table__empty">No PM schedules found</div>
  }

  return (
    <div className="pm-schedules-table">
      <table className="pm-schedules-table__table">
        <thead>
          <tr>
            <th>Schedule Code</th>
            <th>Schedule Name</th>
            <th>Machine</th>
            <th>Trigger Type</th>
            <th>Frequency</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredSchedules.map((schedule) => (
            <tr key={schedule.id}>
              <td>{schedule.schedule_code}</td>
              <td>{schedule.schedule_name}</td>
              <td>Machine {schedule.machine_id}</td>
              <td>
                <span className={`trigger-badge trigger-badge--${schedule.trigger_type.toLowerCase()}`}>
                  {schedule.trigger_type}
                </span>
              </td>
              <td>
                {schedule.trigger_type === 'CALENDAR'
                  ? `${schedule.frequency_days} days`
                  : `${schedule.meter_threshold} units`}
              </td>
              <td>
                <span className={`status-badge status-badge--${schedule.is_active ? 'active' : 'inactive'}`}>
                  {schedule.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td>
                <div className="pm-schedules-table__actions">
                  {onEdit && (
                    <button
                      className="btn btn--edit"
                      onClick={() => onEdit(schedule)}
                      aria-label="Edit schedule"
                    >
                      Edit
                    </button>
                  )}
                  {onDelete && (
                    <button
                      className="btn btn--delete"
                      onClick={() => onDelete(schedule)}
                      aria-label="Delete schedule"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
