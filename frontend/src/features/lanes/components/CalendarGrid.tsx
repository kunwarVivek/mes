/**
 * CalendarGrid Component
 *
 * Calendar view for lane scheduling with date headers and capacity visualization
 */
import React from 'react'
import { Button, Heading3, Body, Spinner } from '@/design-system/atoms'
import type { Lane, LaneAssignment } from '../types/lane.types'

export interface CalendarGridProps {
  lanes: Lane[]
  assignments: LaneAssignment[]
  startDate: Date
  daysToShow: number
  onDateChange: (newStartDate: Date) => void
  onCellClick: (laneId: number, date: string) => void
  isLoading: boolean
}

export const CalendarGrid: React.FC<CalendarGridProps> = ({
  lanes,
  assignments,
  startDate,
  daysToShow,
  onDateChange,
  onCellClick,
  isLoading,
}) => {
  const handlePrevious = () => {
    const newDate = new Date(startDate)
    newDate.setDate(newDate.getDate() - daysToShow)
    onDateChange(newDate)
  }

  const handleNext = () => {
    const newDate = new Date(startDate)
    newDate.setDate(newDate.getDate() + daysToShow)
    onDateChange(newDate)
  }

  const handleToday = () => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    onDateChange(today)
  }

  const generateDateHeaders = (): Date[] => {
    const dates: Date[] = []
    for (let i = 0; i < daysToShow; i++) {
      const date = new Date(startDate)
      date.setDate(date.getDate() + i)
      dates.push(date)
    }
    return dates
  }

  const formatDateHeader = (date: Date): string => {
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
    return date.toLocaleDateString('en-US', options)
  }

  const formatDateForAPI = (date: Date): string => {
    return date.toLocaleDateString('en-CA') // YYYY-MM-DD format
  }

  const getDayOfWeek = (date: Date): string => {
    const options: Intl.DateTimeFormatOptions = { weekday: 'short' }
    return date.toLocaleDateString('en-US', options)
  }

  const getUtilizationForCell = (laneId: number, date: Date): number => {
    const dateStr = formatDateForAPI(date)
    const lane = lanes.find((l) => l.id === laneId)
    if (!lane) return 0

    const cellAssignments = assignments.filter((a) => {
      return (
        a.lane_id === laneId &&
        dateStr >= a.scheduled_start &&
        dateStr <= a.scheduled_end
      )
    })

    const allocated = cellAssignments.reduce(
      (sum, a) => sum + a.allocated_capacity,
      0
    )
    return (allocated / lane.capacity_per_day) * 100
  }

  const getUtilizationColor = (utilization: number): string => {
    if (utilization > 100) return 'bg-red-100 border-red-400'
    if (utilization >= 80) return 'bg-yellow-100 border-yellow-400'
    return 'bg-green-100 border-green-400'
  }

  const dateHeaders = generateDateHeaders()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Spinner size="lg" />
        <span className="ml-2">Loading calendar...</span>
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Navigation Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handlePrevious}>
            Previous
          </Button>
          <Button variant="secondary" size="sm" onClick={handleToday}>
            Today
          </Button>
          <Button variant="secondary" size="sm" onClick={handleNext}>
            Next
          </Button>
        </div>
        <Heading3>
          {formatDateHeader(dateHeaders[0])} - {formatDateHeader(dateHeaders[dateHeaders.length - 1])}
        </Heading3>
      </div>

      {/* Calendar Grid */}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr>
              <th className="border border-gray-300 bg-gray-100 p-2 text-left sticky left-0 z-10">
                <Body>Lane</Body>
              </th>
              <th className="border border-gray-300 bg-gray-100 p-2 text-left sticky left-0 z-10">
                <Body>Capacity</Body>
              </th>
              {dateHeaders.map((date, index) => (
                <th key={index} className="border border-gray-300 bg-gray-100 p-2 text-center min-w-[100px]">
                  <div>
                    <Body>{getDayOfWeek(date)}</Body>
                    <Body>{formatDateHeader(date)}</Body>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {lanes.map((lane) => (
              <tr key={lane.id}>
                <td className="border border-gray-300 p-2 sticky left-0 bg-white z-10">
                  <Body>{lane.lane_name}</Body>
                  <Body className="text-xs text-gray-500">{lane.lane_code}</Body>
                </td>
                <td className="border border-gray-300 p-2 sticky left-0 bg-white z-10">
                  <Body>{lane.capacity_per_day}</Body>
                </td>
                {dateHeaders.map((date, index) => {
                  const utilization = getUtilizationForCell(lane.id, date)
                  const colorClass = getUtilizationColor(utilization)
                  return (
                    <td
                      key={index}
                      className={`border border-gray-300 p-2 ${colorClass} cursor-pointer hover:opacity-75`}
                    >
                      <button
                        aria-label={`cell-${lane.id}-${index}`}
                        onClick={() => onCellClick(lane.id, formatDateForAPI(date))}
                        className="w-full h-full min-h-[60px] text-left"
                      >
                        {utilization > 0 && (
                          <Body className="text-xs">{utilization.toFixed(0)}%</Body>
                        )}
                      </button>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex gap-4 items-center">
        <Body className="font-semibold">Utilization:</Body>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-100 border border-green-400"></div>
          <Body className="text-sm">{'< 80%'}</Body>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-100 border border-yellow-400"></div>
          <Body className="text-sm">80-100%</Body>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-100 border border-red-400"></div>
          <Body className="text-sm">{`> 100%`}</Body>
        </div>
      </div>
    </div>
  )
}
