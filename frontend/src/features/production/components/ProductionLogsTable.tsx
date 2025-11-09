/**
 * ProductionLogsTable Component
 *
 * Displays production logs in table format with pagination
 */
import { Card, Body, Caption, Button, Skeleton } from '@/design-system/atoms'
import type { ProductionLog } from '../types/productionLog.types'

export interface ProductionLogsTableProps {
  logs: ProductionLog[]
  isLoading: boolean
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function ProductionLogsTable({
  logs,
  isLoading,
  page,
  pageSize,
  total,
  onPageChange,
}: ProductionLogsTableProps) {
  const calculateYield = (log: ProductionLog): number => {
    const totalQty = log.quantity_produced + log.quantity_scrapped + log.quantity_reworked
    if (totalQty === 0) return 0
    return (log.quantity_produced / totalQty) * 100
  }

  const getYieldColor = (yieldRate: number): string => {
    if (yieldRate >= 95) return 'text-green-600'
    if (yieldRate >= 85) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }) + ' ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalPages = Math.ceil(total / pageSize)
  const canGoPrev = page > 1
  const canGoNext = page < totalPages

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </Card>
    )
  }

  if (logs.length === 0) {
    return (
      <Card className="p-6">
        <Body className="text-gray-500 text-center">No production logs available</Body>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">
                <Caption className="font-semibold">Timestamp</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Produced</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Scrapped</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Reworked</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Yield %</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Operator</Caption>
              </th>
              <th className="text-right p-2">
                <Caption className="font-semibold">Shift</Caption>
              </th>
              <th className="text-left p-2">
                <Caption className="font-semibold">Notes</Caption>
              </th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => {
              const yieldRate = calculateYield(log)
              return (
                <tr key={log.id} className="border-b hover:bg-gray-50">
                  <td className="p-2">
                    <Caption>{formatTimestamp(log.timestamp)}</Caption>
                  </td>
                  <td className="text-right p-2">
                    <Body>{log.quantity_produced}</Body>
                  </td>
                  <td className="text-right p-2">
                    <Body>{log.quantity_scrapped}</Body>
                  </td>
                  <td className="text-right p-2">
                    <Body>{log.quantity_reworked}</Body>
                  </td>
                  <td className="text-right p-2">
                    <Body className={`font-semibold ${getYieldColor(yieldRate)}`}>
                      {yieldRate.toFixed(1)}%
                    </Body>
                  </td>
                  <td className="text-right p-2">
                    <Caption>{log.operator_id || '-'}</Caption>
                  </td>
                  <td className="text-right p-2">
                    <Caption>{log.shift_id || '-'}</Caption>
                  </td>
                  <td className="p-2">
                    <Caption>{log.notes || '-'}</Caption>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4 pt-4 border-t">
        <Caption className="text-gray-600">
          Page {page} of {totalPages} ({total} total)
        </Caption>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={!canGoPrev}
          >
            Previous
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={!canGoNext}
          >
            Next
          </Button>
        </div>
      </div>
    </Card>
  )
}
