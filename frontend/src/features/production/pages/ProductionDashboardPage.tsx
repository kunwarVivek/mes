/**
 * ProductionDashboardPage
 *
 * Main production logging dashboard with form, summary, and logs table
 */
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Heading1, Body, Card } from '@/design-system/atoms'
import { useAuthStore } from '@/stores/auth.store'
import { ProductionEntryForm } from '../components/ProductionEntryForm'
import { ProductionSummaryCard } from '../components/ProductionSummaryCard'
import { ProductionLogsTable } from '../components/ProductionLogsTable'
import { useProductionLogs, useProductionSummary } from '../hooks/useProductionLogs'

export function ProductionDashboardPage() {
  const { currentPlant } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const workOrderIdParam = searchParams.get('workOrderId')
  const workOrderId = workOrderIdParam ? parseInt(workOrderIdParam) : undefined

  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  // Fetch production logs and summary (only if work order selected)
  const {
    data: logsData,
    isLoading: isLoadingLogs,
  } = useProductionLogs(
    workOrderId!,
    { page: currentPage, page_size: pageSize },
  )

  const {
    data: summary,
    isLoading: isLoadingSummary,
  } = useProductionSummary(workOrderId!)

  const handleWorkOrderSelect = (woId: number) => {
    setSearchParams({ workOrderId: woId.toString() })
    setCurrentPage(1)
  }

  if (!currentPlant) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-8 text-center">
          <Heading1 className="mb-4">Production Logging</Heading1>
          <Body className="text-gray-500">
            Please select a plant to access production logging.
          </Body>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <Heading1>Production Logging</Heading1>
        <Body className="text-gray-600 mt-2">
          Log production quantities and monitor yield rates in real-time
        </Body>
      </div>

      {/* Work Order Selector */}
      <div className="mb-6">
        <Card className="p-4">
          <label htmlFor="work-order-select" className="block text-sm font-medium mb-2">
            Select Work Order
          </label>
          <select
            id="work-order-select"
            className="w-full p-2 border rounded"
            value={workOrderId || ''}
            onChange={(e) => {
              const value = e.target.value
              if (value) {
                handleWorkOrderSelect(parseInt(value))
              }
            }}
          >
            <option value="">-- Select a work order --</option>
            <option value="10">WO-001 - Production Run A</option>
            <option value="20">WO-002 - Production Run B</option>
            <option value="30">WO-003 - Production Run C</option>
          </select>
        </Card>
      </div>

      {workOrderId ? (
        <>
          {/* Two-column layout: Form and Summary */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <ProductionEntryForm
              workOrderId={workOrderId}
              onSuccess={() => {
                // Form will auto-refresh via query invalidation
              }}
            />
            <ProductionSummaryCard summary={summary} isLoading={isLoadingSummary} />
          </div>

          {/* Full-width logs table */}
          <ProductionLogsTable
            logs={logsData?.items || []}
            isLoading={isLoadingLogs}
            page={currentPage}
            pageSize={pageSize}
            total={logsData?.total || 0}
            onPageChange={setCurrentPage}
          />
        </>
      ) : (
        <Card className="p-8 text-center">
          <Body className="text-gray-500">Select a work order to start logging production</Body>
        </Card>
      )}
    </div>
  )
}
