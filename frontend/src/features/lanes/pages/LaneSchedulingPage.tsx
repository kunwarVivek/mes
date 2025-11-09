/**
 * LaneSchedulingPage Component
 *
 * Main page for lane scheduling with calendar view and assignment management
 */
import React, { useState } from 'react'
import { Heading1, Body, Button, Badge } from '@/design-system/atoms'
import { useAuthStore } from '@/stores/auth.store'
import { CalendarGrid } from '../components/CalendarGrid'
import { AssignmentForm } from '../components/AssignmentForm'
import {
  useLanes,
  useLaneAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
} from '../hooks/useLanes'
import type { LaneAssignment, LaneAssignmentCreateRequest, LaneAssignmentUpdateRequest } from '../types/lane.types'

export const LaneSchedulingPage: React.FC = () => {
  const { currentPlant, currentOrg } = useAuthStore()
  const [startDate, setStartDate] = useState(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return today
  })
  const [daysToShow, setDaysToShow] = useState(7)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [selectedLane, setSelectedLane] = useState<number | undefined>()
  const [selectedDate, setSelectedDate] = useState<string | undefined>()
  const [editingAssignment, setEditingAssignment] = useState<LaneAssignment | null>(null)

  // Calculate date range for assignments query
  const endDate = new Date(startDate)
  endDate.setDate(endDate.getDate() + daysToShow)

  const formatDateForAPI = (date: Date): string => {
    return date.toLocaleDateString('en-CA') // YYYY-MM-DD
  }

  // Data fetching
  const { data: lanesData, isLoading: lanesLoading } = useLanes(currentPlant?.id)
  const { data: assignmentsData, isLoading: assignmentsLoading } = useLaneAssignments({
    plant_id: currentPlant?.id,
    start_date: formatDateForAPI(startDate),
    end_date: formatDateForAPI(endDate),
  })

  // Mutations
  const createMutation = useCreateAssignment()
  const updateMutation = useUpdateAssignment()

  const handleCellClick = (laneId: number, date: string) => {
    setSelectedLane(laneId)
    setSelectedDate(date)
    setEditingAssignment(null)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (
    data: LaneAssignmentCreateRequest | LaneAssignmentUpdateRequest
  ) => {
    try {
      if (editingAssignment) {
        await updateMutation.mutateAsync({
          id: editingAssignment.id,
          data: data as LaneAssignmentUpdateRequest,
        })
      } else {
        // Add org and plant IDs for create
        const createData = data as LaneAssignmentCreateRequest
        createData.organization_id = currentOrg?.id || 1
        createData.plant_id = currentPlant?.id || 100
        await createMutation.mutateAsync(createData)
      }
      setIsFormOpen(false)
      setEditingAssignment(null)
    } catch (error) {
      console.error('Failed to save assignment:', error)
    }
  }

  const handleFormCancel = () => {
    setIsFormOpen(false)
    setEditingAssignment(null)
    setSelectedLane(undefined)
    setSelectedDate(undefined)
  }

  const toggleDaysView = () => {
    setDaysToShow((prev) => (prev === 7 ? 14 : 7))
  }

  // Guard: No plant selected
  if (!currentPlant) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Heading1>Lane Scheduling</Heading1>
          <Body className="mt-4 text-gray-600">Please select a plant to view lane scheduling.</Body>
        </div>
      </div>
    )
  }

  const lanes = lanesData?.items || []
  const assignments = assignmentsData?.items || []
  const isLoading = lanesLoading || assignmentsLoading

  // Calculate summary statistics
  const totalAssignments = assignments.length
  const activeAssignments = assignments.filter((a) => a.status === 'ACTIVE').length

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Heading1>Lane Scheduling</Heading1>
          <Body className="text-gray-600 mt-1">
            {currentPlant.plant_name} ({currentPlant.plant_code})
          </Body>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={toggleDaysView}>
            {daysToShow === 7 ? '14-Day View' : '7-Day View'}
          </Button>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="flex gap-4">
        <div className="bg-white p-4 rounded shadow border border-gray-200">
          <Body className="text-gray-600">Total Assignments</Body>
          <Heading1>{totalAssignments}</Heading1>
        </div>
        <div className="bg-white p-4 rounded shadow border border-gray-200">
          <Body className="text-gray-600">Active</Body>
          <Heading1>{activeAssignments}</Heading1>
        </div>
        <div className="bg-white p-4 rounded shadow border border-gray-200">
          <Body className="text-gray-600">Total Lanes</Body>
          <Heading1>{lanes.length}</Heading1>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="bg-white p-4 rounded shadow border border-gray-200">
        <CalendarGrid
          lanes={lanes}
          assignments={assignments}
          startDate={startDate}
          daysToShow={daysToShow}
          onDateChange={setStartDate}
          onCellClick={handleCellClick}
          isLoading={isLoading}
        />
      </div>

      {/* Status Legend */}
      <div className="flex gap-4 items-center">
        <Body className="font-semibold">Status:</Body>
        <div className="flex items-center gap-2">
          <Badge variant="info">PLANNED</Badge>
          <Body className="text-sm">Blue</Body>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">ACTIVE</Badge>
          <Body className="text-sm">Green</Body>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="neutral">COMPLETED</Badge>
          <Body className="text-sm">Gray</Body>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="error">CANCELLED</Badge>
          <Body className="text-sm">Red</Body>
        </div>
      </div>

      {/* Assignment Form Modal */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <Heading1 className="text-xl">
                {editingAssignment ? 'Edit Assignment' : 'New Assignment'}
              </Heading1>
            </div>
            <AssignmentForm
              assignment={editingAssignment}
              preSelectedLane={selectedLane}
              preSelectedDate={selectedDate}
              onSubmit={handleFormSubmit}
              onCancel={handleFormCancel}
              isLoading={createMutation.isPending || updateMutation.isPending}
            />
          </div>
        </div>
      )}
    </div>
  )
}
