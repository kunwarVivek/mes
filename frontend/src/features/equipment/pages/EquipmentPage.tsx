/**
 * EquipmentPage Component
 *
 * Complete Equipment and Machine Management:
 * - Tab 1: Machines List (table view with filters)
 * - Tab 2: Status Dashboard (card grid view)
 * - Create/Edit machine functionality
 * - Machine detail modal with OEE metrics
 * - Status update capability
 */
import { useState } from 'react'
import { useMachines } from '../hooks/useMachines'
import { useCreateMachine, useUpdateMachine, useDeleteMachine, useUpdateMachineStatus } from '../hooks/useMachineMutations'
import { useMachineOEE } from '../hooks/useMachineOEE'
import { useMachineStatusHistory } from '../hooks/useMachineStatusHistory'
import { MachinesTable } from '../components/MachinesTable'
import { MachineStatusCard } from '../components/MachineStatusCard'
import { MachineForm } from '../components/MachineForm'
import { CircularOEEGauge } from '../components/CircularOEEGauge'
import { MachineStatusTimeline } from '../components/MachineStatusTimeline'
import type { Machine, CreateMachineDTO, UpdateMachineDTO, MachineStatusUpdateDTO } from '../types/machine.types'

type TabView = 'list' | 'dashboard'

export const EquipmentPage = () => {
  // State
  const [activeTab, setActiveTab] = useState<TabView>('list')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null)
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null)
  const [showStatusDialog, setShowStatusDialog] = useState(false)
  const [statusFormData, setStatusFormData] = useState({ status: '', notes: '' })
  const [showOEESection, setShowOEESection] = useState(false)
  const [oeeParams, setOEEParams] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    endDate: new Date().toISOString().split('T')[0], // today
    idealCycleTime: 1.5,
    totalPieces: 1000,
    defectPieces: 20,
  })

  // API hooks
  const { data: machinesData, isLoading, error } = useMachines(
    statusFilter !== 'ALL' ? { status: statusFilter } : undefined
  )
  const createMachine = useCreateMachine({
    onSuccess: () => {
      setShowCreateModal(false)
      // TODO: Add toast notification
    },
  })
  const updateMachine = useUpdateMachine({
    onSuccess: () => {
      setEditingMachine(null)
      // TODO: Add toast notification
    },
  })
  const deleteMachine = useDeleteMachine({
    onSuccess: () => {
      // TODO: Add toast notification
    },
  })
  const updateStatus = useUpdateMachineStatus({
    onSuccess: () => {
      setShowStatusDialog(false)
      setSelectedMachine(null)
      setStatusFormData({ status: '', notes: '' })
      // TODO: Add toast notification
    },
  })

  // OEE metrics hook (only fetch when machine is selected and OEE section is shown)
  const { data: oeeMetrics, isLoading: isLoadingOEE, error: oeeError } = useMachineOEE({
    machineId: selectedMachine?.id || 0,
    startDate: oeeParams.startDate,
    endDate: oeeParams.endDate,
    idealCycleTime: oeeParams.idealCycleTime,
    totalPieces: oeeParams.totalPieces,
    defectPieces: oeeParams.defectPieces,
  })

  // Status history hook (fetch last 20 records for selected machine)
  const { data: statusHistory, isLoading: isLoadingHistory } = useMachineStatusHistory({
    machineId: selectedMachine?.id || 0,
    limit: 20,
  })

  // Filter machines by search query
  const filteredMachines = machinesData?.filter((machine: Machine) =>
    searchQuery
      ? machine.machine_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        machine.machine_name.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  ) || []

  // Status counts for filter badges
  const statusCounts = machinesData?.reduce((acc: Record<string, number>, machine: Machine) => {
    acc[machine.status] = (acc[machine.status] || 0) + 1
    return acc
  }, {} as Record<string, number>) || {}

  // Handlers
  const handleCreate = async (data: CreateMachineDTO) => {
    await createMachine.mutateAsync(data)
  }

  const handleEdit = async (data: UpdateMachineDTO) => {
    if (editingMachine) {
      await updateMachine.mutateAsync({ id: editingMachine.id, data })
    }
  }

  const handleDelete = async (machine: Machine) => {
    if (confirm(`Are you sure you want to delete machine ${machine.machine_code}?`)) {
      await deleteMachine.mutateAsync(machine.id)
    }
  }

  const handleOpenStatusDialog = (machine: Machine) => {
    setSelectedMachine(machine)
    setStatusFormData({ status: machine.status, notes: '' })
    setShowStatusDialog(true)
  }

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedMachine) {
      const statusUpdate: MachineStatusUpdateDTO = {
        status: statusFormData.status as any,
        notes: statusFormData.notes || undefined,
      }
      await updateStatus.mutateAsync({ id: selectedMachine.id, data: statusUpdate })
    }
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Equipment Management</h1>
        <p className="text-gray-600">Manage machines, monitor status, and track utilization</p>
      </div>

      {/* Controls Bar */}
      <div className="flex flex-wrap gap-4 mb-6 items-center justify-between">
        {/* Left side: Tabs and Filters */}
        <div className="flex flex-wrap gap-4 items-center">
          {/* View Tabs */}
          <div className="flex gap-2 border rounded-lg p-1 bg-gray-50">
            <button
              onClick={() => setActiveTab('list')}
              className={`px-4 py-2 rounded ${
                activeTab === 'list'
                  ? 'bg-white shadow text-blue-600 font-medium'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              List View
            </button>
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-4 py-2 rounded ${
                activeTab === 'dashboard'
                  ? 'bg-white shadow text-blue-600 font-medium'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Status Dashboard
            </button>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border rounded-lg bg-white"
          >
            <option value="ALL">All Status ({machinesData?.length || 0})</option>
            <option value="RUNNING">Running ({statusCounts.RUNNING || 0})</option>
            <option value="IDLE">Idle ({statusCounts.IDLE || 0})</option>
            <option value="DOWN">Down ({statusCounts.DOWN || 0})</option>
            <option value="SETUP">Setup ({statusCounts.SETUP || 0})</option>
            <option value="MAINTENANCE">Maintenance ({statusCounts.MAINTENANCE || 0})</option>
          </select>

          {/* Search */}
          <input
            type="text"
            placeholder="Search by code or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-4 py-2 border rounded-lg w-64"
          />
        </div>

        {/* Right side: Create button */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          + Create Machine
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          Error loading machines: {error.message}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading machines...</p>
        </div>
      )}

      {/* Content - List View */}
      {!isLoading && activeTab === 'list' && (
        <div className="bg-white rounded-lg shadow">
          <MachinesTable
            machines={filteredMachines}
            onEdit={(machine) => setEditingMachine(machine)}
            onDelete={handleDelete}
            onRowClick={(machine) => setSelectedMachine(machine)}
            onStatusChange={handleOpenStatusDialog}
          />
        </div>
      )}

      {/* Content - Dashboard View */}
      {!isLoading && activeTab === 'dashboard' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredMachines.map((machine) => (
            <MachineStatusCard
              key={machine.id}
              machine={machine}
              onClick={(m) => setSelectedMachine(m)}
              onStatusChange={handleOpenStatusDialog}
            />
          ))}
          {filteredMachines.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              No machines found
            </div>
          )}
        </div>
      )}

      {/* Create Machine Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Create Machine</h2>
            <MachineForm
              onSubmit={handleCreate}
              onCancel={() => setShowCreateModal(false)}
              isSubmitting={createMachine.isPending}
              error={createMachine.error?.message}
            />
          </div>
        </div>
      )}

      {/* Edit Machine Modal */}
      {editingMachine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Edit Machine</h2>
            <MachineForm
              initialData={editingMachine}
              onSubmit={handleEdit}
              onCancel={() => setEditingMachine(null)}
              isSubmitting={updateMachine.isPending}
              error={updateMachine.error?.message}
            />
          </div>
        </div>
      )}

      {/* Machine Detail Modal */}
      {selectedMachine && !showStatusDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold">{selectedMachine.machine_code}</h2>
                <p className="text-gray-600">{selectedMachine.machine_name}</p>
              </div>
              <button
                onClick={() => setSelectedMachine(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Machine Details */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <span
                  className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    selectedMachine.status === 'RUNNING'
                      ? 'bg-green-100 text-green-800'
                      : selectedMachine.status === 'IDLE'
                      ? 'bg-yellow-100 text-yellow-800'
                      : selectedMachine.status === 'DOWN'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {selectedMachine.status}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Active</label>
                <p>{selectedMachine.is_active ? 'Yes' : 'No'}</p>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <p className="text-gray-900">{selectedMachine.description || 'No description'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Work Center ID</label>
                <p className="text-gray-900">{selectedMachine.work_center_id}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Created</label>
                <p className="text-gray-900">
                  {new Date(selectedMachine.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* OEE Metrics Section */}
            <div className="mt-6 border-t pt-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">OEE Metrics</h3>
                <button
                  onClick={() => setShowOEESection(!showOEESection)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {showOEESection ? 'Hide' : 'Show'} OEE Calculator
                </button>
              </div>

              {showOEESection && (
                <>
                  {/* OEE Parameters Form */}
                  <div className="bg-gray-50 p-4 rounded-lg mb-4">
                    <p className="text-sm text-gray-600 mb-3">
                      Enter production parameters to calculate OEE metrics for this machine
                    </p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Start Date
                        </label>
                        <input
                          type="date"
                          value={oeeParams.startDate}
                          onChange={(e) => setOEEParams({ ...oeeParams, startDate: e.target.value })}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          End Date
                        </label>
                        <input
                          type="date"
                          value={oeeParams.endDate}
                          onChange={(e) => setOEEParams({ ...oeeParams, endDate: e.target.value })}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Ideal Cycle Time (min/piece)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={oeeParams.idealCycleTime}
                          onChange={(e) => setOEEParams({ ...oeeParams, idealCycleTime: parseFloat(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Total Pieces Produced
                        </label>
                        <input
                          type="number"
                          value={oeeParams.totalPieces}
                          onChange={(e) => setOEEParams({ ...oeeParams, totalPieces: parseInt(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Defective Pieces
                        </label>
                        <input
                          type="number"
                          value={oeeParams.defectPieces}
                          onChange={(e) => setOEEParams({ ...oeeParams, defectPieces: parseInt(e.target.value) || 0 })}
                          className="w-full px-3 py-2 border rounded-lg text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* OEE Results */}
                  {isLoadingOEE && (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-600">Calculating OEE...</p>
                    </div>
                  )}

                  {oeeError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                      Error calculating OEE: {oeeError.message}
                    </div>
                  )}

                  {oeeMetrics && !isLoadingOEE && (
                    <div className="bg-white border rounded-lg p-6">
                      <h4 className="text-md font-semibold mb-4 text-center">
                        Overall Equipment Effectiveness
                      </h4>
                      <div className="grid grid-cols-4 gap-6">
                        <CircularOEEGauge
                          value={oeeMetrics.oee_score * 100}
                          label="OEE Score"
                          size="medium"
                        />
                        <CircularOEEGauge
                          value={oeeMetrics.availability * 100}
                          label="Availability"
                          size="medium"
                        />
                        <CircularOEEGauge
                          value={oeeMetrics.performance * 100}
                          label="Performance"
                          size="medium"
                        />
                        <CircularOEEGauge
                          value={oeeMetrics.quality * 100}
                          label="Quality"
                          size="medium"
                        />
                      </div>
                      <div className="mt-4 text-center text-sm text-gray-600">
                        <p>
                          Period: {oeeParams.startDate} to {oeeParams.endDate}
                        </p>
                        <p className="mt-1">
                          {oeeMetrics.oee_score >= 0.85
                            ? 'Excellent performance (≥85%)'
                            : oeeMetrics.oee_score >= 0.60
                            ? 'Acceptable performance (60-85%)'
                            : 'Needs improvement (<60%)'}
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setEditingMachine(selectedMachine)
                  setSelectedMachine(null)
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Edit Machine
              </button>
              <button
                onClick={() => {
                  handleOpenStatusDialog(selectedMachine)
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Update Status
              </button>
              <button
                onClick={() => setSelectedMachine(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>

            {/* Status History Timeline */}
            <div className="mt-6 border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">Status History</h3>
              <div className="max-h-96 overflow-y-auto">
                <MachineStatusTimeline
                  history={statusHistory || []}
                  isLoading={isLoadingHistory}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status Update Dialog */}
      {showStatusDialog && selectedMachine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Update Machine Status</h2>
            <form onSubmit={handleUpdateStatus}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Machine: {selectedMachine.machine_code}
                </label>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Status <span className="text-red-500">*</span>
                </label>
                <select
                  value={statusFormData.status}
                  onChange={(e) => setStatusFormData({ ...statusFormData, status: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                >
                  <option value="">Select status...</option>
                  <option value="RUNNING">Running</option>
                  <option value="IDLE">Idle</option>
                  <option value="DOWN">Down</option>
                  <option value="SETUP">Setup</option>
                  <option value="MAINTENANCE">Maintenance</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                <textarea
                  value={statusFormData.notes}
                  onChange={(e) => setStatusFormData({ ...statusFormData, notes: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Optional notes about status change..."
                />
              </div>

              {updateStatus.error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  {updateStatus.error.message}
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowStatusDialog(false)
                    setStatusFormData({ status: '', notes: '' })
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  disabled={updateStatus.isPending}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  disabled={updateStatus.isPending}
                >
                  {updateStatus.isPending ? 'Updating...' : 'Update Status'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

EquipmentPage.displayName = 'EquipmentPage'
