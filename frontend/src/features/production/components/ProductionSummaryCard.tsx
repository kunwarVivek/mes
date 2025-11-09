/**
 * ProductionSummaryCard Component
 *
 * Displays aggregated production statistics with color-coded yield rate
 */
import { Card, Heading3, Body, Caption, Skeleton } from '@/design-system/atoms'
import type { ProductionSummary } from '../types/productionLog.types'

export interface ProductionSummaryCardProps {
  summary?: ProductionSummary
  isLoading: boolean
}

export function ProductionSummaryCard({ summary, isLoading }: ProductionSummaryCardProps) {
  if (isLoading) {
    return (
      <Card className="p-6">
        <Heading3 className="mb-4">Production Summary</Heading3>
        <div className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      </Card>
    )
  }

  if (!summary) {
    return (
      <Card className="p-6">
        <Heading3 className="mb-4">Production Summary</Heading3>
        <Body className="text-gray-500">No production data available</Body>
      </Card>
    )
  }

  const getYieldColor = (yieldRate: number): string => {
    if (yieldRate >= 95) return 'text-green-600'
    if (yieldRate >= 85) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <Card className="p-6">
      <Heading3 className="mb-6">Production Summary</Heading3>

      <div className="space-y-4">
        {/* Total Produced */}
        <div className="flex flex-col">
          <Body className="text-4xl font-bold text-green-600">{summary.total_produced}</Body>
          <Caption className="text-gray-500">Total Produced</Caption>
        </div>

        {/* Total Scrapped */}
        <div className="flex justify-between items-center">
          <Caption className="text-gray-600">Total Scrapped</Caption>
          <Body className="text-xl font-semibold text-red-600">{summary.total_scrapped}</Body>
        </div>

        {/* Total Reworked */}
        <div className="flex justify-between items-center">
          <Caption className="text-gray-600">Total Reworked</Caption>
          <Body className="text-xl font-semibold text-yellow-600">{summary.total_reworked}</Body>
        </div>

        {/* Yield Rate */}
        <div className="flex justify-between items-center pt-4 border-t">
          <Caption className="text-gray-600">Yield Rate</Caption>
          <Body className={`text-2xl font-bold ${getYieldColor(summary.yield_rate)}`}>
            {summary.yield_rate.toFixed(1)}%
          </Body>
        </div>

        {/* Log Count */}
        <Caption className="text-gray-500 text-center pt-2">
          {summary.log_count} log entries from{' '}
          {new Date(summary.first_log).toLocaleDateString()} to{' '}
          {new Date(summary.last_log).toLocaleDateString()}
        </Caption>
      </div>
    </Card>
  )
}
