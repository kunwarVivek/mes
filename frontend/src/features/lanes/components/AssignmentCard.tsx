/**
 * AssignmentCard Component
 *
 * Display assignment as card/block on calendar with status color coding
 */
import React from 'react'
import { Tooltip, Body } from '@/design-system/atoms'
import type { LaneAssignment } from '../types/lane.types'

export interface AssignmentCardProps {
  assignment: LaneAssignment
  onClick: (assignment: LaneAssignment) => void
  startDate: Date
  daysToShow: number
}

export const AssignmentCard: React.FC<AssignmentCardProps> = ({
  assignment,
  onClick,
  startDate,
  daysToShow,
}) => {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'PLANNED':
        return 'bg-blue-500 hover:bg-blue-600'
      case 'ACTIVE':
        return 'bg-green-500 hover:bg-green-600'
      case 'COMPLETED':
        return 'bg-gray-500 hover:bg-gray-600'
      case 'CANCELLED':
        return 'bg-red-500 hover:bg-red-600'
      default:
        return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  const calculatePosition = (): { left: string; width: string } => {
    // Normalize dates to midnight local time to avoid DST issues
    const assignmentStart = new Date(assignment.scheduled_start + 'T00:00:00')
    const assignmentEnd = new Date(assignment.scheduled_end + 'T00:00:00')
    const calendarStart = new Date(startDate)
    calendarStart.setHours(0, 0, 0, 0)

    // Calculate day offset from calendar start using date-only comparison
    const dayOffset = Math.floor(
      (assignmentStart.getTime() - calendarStart.getTime()) / (1000 * 60 * 60 * 24)
    )

    // Calculate width in days (inclusive of both start and end dates)
    const widthInDays =
      Math.floor(
        (assignmentEnd.getTime() - assignmentStart.getTime()) / (1000 * 60 * 60 * 24)
      ) + 1

    // Each day is approximately 14.28% for 7-day view, 7.14% for 14-day view
    const dayPercentage = 100 / daysToShow

    return {
      left: `${dayOffset * dayPercentage}%`,
      width: `${widthInDays * dayPercentage}%`,
    }
  }

  const position = calculatePosition()
  const colorClass = getStatusColor(assignment.status)

  return (
    <Tooltip content={`WO-${assignment.work_order_id} | Priority: ${assignment.priority} | ${assignment.allocated_capacity} units`}>
      <button
        onClick={() => onClick(assignment)}
        className={`absolute ${colorClass} text-white p-1 rounded shadow-sm text-xs truncate transition-colors`}
        style={{
          left: position.left,
          width: position.width,
          top: '2px',
          height: 'calc(100% - 4px)',
        }}
        role="button"
      >
        <Body className="text-xs text-white font-semibold truncate">
          WO-{assignment.work_order_id}
        </Body>
        <Body className="text-xs text-white truncate">
          P{assignment.priority} | {assignment.allocated_capacity}
        </Body>
      </button>
    </Tooltip>
  )
}
