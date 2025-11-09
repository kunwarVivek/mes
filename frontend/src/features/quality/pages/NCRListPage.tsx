/**
 * NCRListPage Component
 *
 * List page for NCRs with search, status filter, and navigation
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { NCRTable } from '../components/NCRTable'
import { useNCRs } from '../hooks/useNCRs'
import type { NCR } from '../schemas/ncr.schema'
import type { NCRListParams } from '../services/ncr.service'

const statusOptions = [
  { value: 'ALL', label: 'All' },
  { value: 'OPEN', label: 'Open' },
  { value: 'IN_REVIEW', label: 'In Review' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'CLOSED', label: 'Closed' },
]

export function NCRListPage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  // Build filters object for NCRTable
  const filters: NCRListParams = {}

  if (searchQuery) {
    filters.search = searchQuery
  }

  if (statusFilter && statusFilter !== 'ALL') {
    filters.status = statusFilter
  }

  // Use useNCRs to detect errors
  const { isError } = useNCRs(Object.keys(filters).length > 0 ? filters : undefined)

  const handleCreateClick = () => {
    navigate('/quality/ncrs/new')
  }

  const handleRowClick = (ncr: NCR) => {
    navigate(`/quality/ncrs/${ncr.id}`)
  }

  const handleSearchClear = () => {
    setSearchQuery('')
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Non-Conformance Reports</h1>
          <p className="text-muted-foreground">Track and manage quality non-conformances</p>
        </div>
        <Button onClick={handleCreateClick}>Create NCR</Button>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Input
            type="text"
            placeholder="Search NCR number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 px-2"
              onClick={handleSearchClear}
              aria-label="Clear search"
            >
              ✕
            </Button>
          )}
        </div>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            {statusOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Error State */}
      {isError && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to load NCRs. Please try again later.
          </p>
        </div>
      )}

      {/* NCR Table */}
      <NCRTable
        filters={Object.keys(filters).length > 0 ? filters : undefined}
        onRowClick={handleRowClick}
      />
    </div>
  )
}
