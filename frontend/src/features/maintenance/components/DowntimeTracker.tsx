/**
 * DowntimeTracker Component
 *
 * Track and display downtime events with MTBF/MTTR metrics
 */
import React, { useState, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createDowntimeEventSchema, updateDowntimeEventSchema } from '../schemas/maintenance.schema'
import type {
  DowntimeEvent,
  CreateDowntimeEventDTO,
  UpdateDowntimeEventDTO,
  MTBFMTTRMetrics,
  DowntimeCategory,
} from '../types/maintenance.types'
import './DowntimeTracker.css'

interface DowntimeTrackerProps {
  events: DowntimeEvent[]
  machineId: number
  metrics?: MTBFMTTRMetrics
  onCreate?: (data: CreateDowntimeEventDTO) => void
  onEnd?: (id: number, data: UpdateDowntimeEventDTO) => void
}

export const DowntimeTracker: React.FC<DowntimeTrackerProps> = ({
  events,
  machineId,
  metrics,
  onCreate,
  onEnd,
}) => {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [endingEventId, setEndingEventId] = useState<number | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<DowntimeCategory | ''>('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    formState: { errors: createErrors },
    reset: resetCreate,
  } = useForm<CreateDowntimeEventDTO>({
    resolver: zodResolver(createDowntimeEventSchema),
    defaultValues: {
      machine_id: machineId,
    },
  })

  const {
    register: registerEnd,
    handleSubmit: handleSubmitEnd,
    formState: { errors: endErrors },
    reset: resetEnd,
  } = useForm<UpdateDowntimeEventDTO>({
    resolver: zodResolver(updateDowntimeEventSchema),
  })

  const filteredEvents = useMemo(() => {
    let filtered = [...events]

    if (categoryFilter) {
      filtered = filtered.filter((event) => event.category === categoryFilter)
    }

    if (startDate) {
      filtered = filtered.filter(
        (event) => new Date(event.started_at) >= new Date(startDate)
      )
    }

    if (endDate) {
      const endDateTime = new Date(endDate)
      endDateTime.setHours(23, 59, 59, 999) // End of day
      filtered = filtered.filter(
        (event) => new Date(event.started_at) <= endDateTime
      )
    }

    return filtered
  }, [events, categoryFilter, startDate, endDate])

  const handleCreate = (data: CreateDowntimeEventDTO) => {
    if (onCreate) {
      onCreate(data)
      setShowCreateForm(false)
      resetCreate()
    }
  }

  const handleEnd = (data: UpdateDowntimeEventDTO) => {
    if (onEnd && endingEventId) {
      const event = events.find((e) => e.id === endingEventId)
      if (event && data.ended_at) {
        if (new Date(data.ended_at) <= new Date(event.started_at)) {
          return
        }
      }
      onEnd(endingEventId, data)
      setEndingEventId(null)
      resetEnd()
    }
  }

  const getCategoryColor = (category: DowntimeCategory) => {
    const colors: Record<DowntimeCategory, string> = {
      BREAKDOWN: 'red',
      PLANNED_MAINTENANCE: 'blue',
      CHANGEOVER: 'orange',
      NO_OPERATOR: 'purple',
      MATERIAL_SHORTAGE: 'yellow',
    }
    return colors[category]
  }

  if (events.length === 0 && !showCreateForm) {
    return (
      <div className="downtime-tracker">
        <div className="downtime-tracker__header">
          <h3>Downtime Events</h3>
          <button
            className="btn btn--primary"
            onClick={() => setShowCreateForm(true)}
          >
            Log Downtime
          </button>
        </div>
        <div className="downtime-tracker__empty">No downtime events recorded</div>
      </div>
    )
  }

  return (
    <div className="downtime-tracker">
      <div className="downtime-tracker__header">
        <h3>Downtime Events</h3>
        <button
          className="btn btn--primary"
          onClick={() => setShowCreateForm(true)}
        >
          Log Downtime
        </button>
      </div>

      {showCreateForm && (
        <div className="downtime-form">
          <h4>Log New Downtime Event</h4>
          <form onSubmit={handleSubmitCreate(handleCreate)}>
            <div className="form-group">
              <label htmlFor="category">Category *</label>
              <select
                id="category"
                {...registerCreate('category')}
                className={createErrors.category ? 'error' : ''}
              >
                <option value="">Select category</option>
                <option value="BREAKDOWN">Breakdown</option>
                <option value="PLANNED_MAINTENANCE">Planned Maintenance</option>
                <option value="CHANGEOVER">Changeover</option>
                <option value="NO_OPERATOR">No Operator</option>
                <option value="MATERIAL_SHORTAGE">Material Shortage</option>
              </select>
              {createErrors.category && (
                <span className="error-message">{createErrors.category.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="reason">Reason *</label>
              <input
                id="reason"
                type="text"
                {...registerCreate('reason')}
                className={createErrors.reason ? 'error' : ''}
              />
              {createErrors.reason && (
                <span className="error-message">{createErrors.reason.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="started_at">Started At *</label>
              <input
                id="started_at"
                type="datetime-local"
                {...registerCreate('started_at')}
                className={createErrors.started_at ? 'error' : ''}
              />
              {createErrors.started_at && (
                <span className="error-message">{createErrors.started_at.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                {...registerCreate('notes')}
                rows={3}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn--primary">
                Submit
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="btn btn--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {endingEventId && (
        <div className="downtime-form">
          <h4>End Downtime Event</h4>
          <form onSubmit={handleSubmitEnd(handleEnd)}>
            <div className="form-group">
              <label htmlFor="ended_at">Ended At *</label>
              <input
                id="ended_at"
                type="datetime-local"
                {...registerEnd('ended_at')}
                className={endErrors.ended_at ? 'error' : ''}
              />
              {endErrors.ended_at && (
                <span className="error-message">{endErrors.ended_at.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="end_notes">Notes</label>
              <textarea
                id="end_notes"
                {...registerEnd('notes')}
                rows={3}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn--primary">
                Confirm
              </button>
              <button
                type="button"
                onClick={() => setEndingEventId(null)}
                className="btn btn--secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {metrics && (
        <div className="metrics-panel">
          <h4>MTBF/MTTR Metrics</h4>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">MTBF</span>
              <span className="metric-value">{Math.round(metrics.mtbf)} min</span>
            </div>
            <div className="metric">
              <span className="metric-label">MTTR</span>
              <span className="metric-value">{Math.round(metrics.mttr)} min</span>
            </div>
            <div className="metric">
              <span className="metric-label">Availability</span>
              <span className="metric-value">
                {(metrics.availability * 100).toFixed(1)}%
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Failures</span>
              <span className="metric-value">{metrics.number_of_failures}</span>
            </div>
          </div>
        </div>
      )}

      <div className="filters-bar">
        <div className="filter-group">
          <label htmlFor="category-filter">Filter by Category</label>
          <select
            id="category-filter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as DowntimeCategory | '')}
          >
            <option value="">All Categories</option>
            <option value="BREAKDOWN">Breakdown</option>
            <option value="PLANNED_MAINTENANCE">Planned Maintenance</option>
            <option value="CHANGEOVER">Changeover</option>
            <option value="NO_OPERATOR">No Operator</option>
            <option value="MATERIAL_SHORTAGE">Material Shortage</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="start-date">Start Date</label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="end-date">End Date</label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>

      <div className="events-list">
        {filteredEvents.map((event) => (
          <div key={event.id} className="event-card">
            <div className="event-header">
              <span
                className={`category-badge category-badge--${getCategoryColor(event.category)}`}
              >
                {event.category}
              </span>
              <span className="event-duration">
                {event.duration_minutes !== null
                  ? `${Math.round(event.duration_minutes)} min`
                  : 'Ongoing'}
              </span>
            </div>
            <div className="event-body">
              <p className="event-reason">{event.reason}</p>
              <p className="event-time">
                Started: {new Date(event.started_at).toLocaleString()}
              </p>
              {event.ended_at && (
                <p className="event-time">
                  Ended: {new Date(event.ended_at).toLocaleString()}
                </p>
              )}
              {event.notes && <p className="event-notes">{event.notes}</p>}
            </div>
            {!event.ended_at && onEnd && (
              <div className="event-actions">
                <button
                  className="btn btn--end"
                  onClick={() => setEndingEventId(event.id)}
                  aria-label="End downtime event"
                >
                  End
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
