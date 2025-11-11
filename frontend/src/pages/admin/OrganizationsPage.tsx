import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  adminService,
  Organization,
  OrganizationListResponse,
} from '@/services/admin.service'
import { useAuthStore } from '@/stores/auth.store'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/design-system/atoms/Card'
import { Button } from '@/design-system/atoms/Button'
import { Input } from '@/design-system/atoms/Input'
import { Alert, AlertDescription } from '@/design-system/atoms/Alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/design-system/atoms/Select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/design-system/atoms/Table'
import { Badge } from '@/design-system/atoms/Badge'
import {
  Building2,
  Search,
  ArrowLeft,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

/**
 * Organizations List Page
 *
 * Admin view of all tenant organizations:
 * - Search by org name/code
 * - Filter by subscription tier and status
 * - Pagination
 * - Click to view org details
 *
 * Access: Requires is_superuser=true
 */

export function OrganizationsPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [data, setData] = useState<OrganizationListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [tierFilter, setTierFilter] = useState<string>('all')
  const [page, setPage] = useState(0)
  const pageSize = 20

  useEffect(() => {
    // Check if user is superuser
    if (!user?.is_superuser) {
      navigate({ to: '/dashboard' })
      return
    }

    loadOrganizations()
  }, [user, navigate, search, statusFilter, tierFilter, page])

  const loadOrganizations = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = {
        limit: pageSize,
        offset: page * pageSize,
      }

      if (search.trim()) {
        params.search = search.trim()
      }

      if (statusFilter !== 'all') {
        params.status = statusFilter
      }

      if (tierFilter !== 'all') {
        params.tier = tierFilter
      }

      const result = await adminService.listOrganizations(params)
      setData(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organizations')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status?: string) => {
    if (!status) return <Badge variant="secondary">No Subscription</Badge>

    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      trial: 'secondary',
      active: 'default',
      past_due: 'destructive',
      suspended: 'destructive',
      cancelled: 'outline',
    }

    const colors: Record<string, string> = {
      trial: 'text-blue-600 bg-blue-50',
      active: 'text-green-600 bg-green-50',
      past_due: 'text-orange-600 bg-orange-50',
      suspended: 'text-red-600 bg-red-50',
      cancelled: 'text-gray-600 bg-gray-50',
    }

    return (
      <Badge variant={variants[status] || 'secondary'} className={colors[status]}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    )
  }

  const getTierBadge = (tier?: string) => {
    if (!tier) return null

    const colors: Record<string, string> = {
      starter: 'text-blue-700 bg-blue-100',
      professional: 'text-purple-700 bg-purple-100',
      enterprise: 'text-green-700 bg-green-100',
    }

    return (
      <Badge variant="outline" className={colors[tier]}>
        {tier.toUpperCase()}
      </Badge>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/admin/dashboard' })}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Organizations</h1>
            <p className="text-gray-600 mt-1">
              {data ? `${data.total_count} total organizations` : 'Loading...'}
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Search and filter organizations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by org name or code..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(0) // Reset to first page on search
                  }}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div>
              <Select
                value={statusFilter}
                onValueChange={(value) => {
                  setStatusFilter(value)
                  setPage(0)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="trial">Trial</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="past_due">Past Due</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Tier Filter */}
            <div>
              <Select
                value={tierFilter}
                onValueChange={(value) => {
                  setTierFilter(value)
                  setPage(0)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Tiers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tiers</SelectItem>
                  <SelectItem value="starter">Starter</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="enterprise">Enterprise</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Organizations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
          <CardDescription>
            {loading
              ? 'Loading...'
              : `Showing ${page * pageSize + 1}-${Math.min(
                  (page + 1) * pageSize,
                  data?.total_count || 0
                )} of ${data?.total_count || 0}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading organizations...</p>
              </div>
            </div>
          ) : data && data.organizations.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization</TableHead>
                    <TableHead>Code</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.organizations.map((org) => (
                    <TableRow key={org.id} className="cursor-pointer hover:bg-gray-50">
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-gray-400" />
                          {org.org_name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {org.org_code}
                        </code>
                      </TableCell>
                      <TableCell>{getTierBadge(org.subscription?.tier)}</TableCell>
                      <TableCell>
                        {getStatusBadge(org.subscription?.status)}
                      </TableCell>
                      <TableCell>
                        {new Date(org.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            navigate({ to: `/admin/organizations/${org.id}` })
                          }
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-600">
                  Page {page + 1} of {Math.ceil((data.total_count || 0) / pageSize)}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 0}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!data.has_more}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No organizations found</p>
              {(search || statusFilter !== 'all' || tierFilter !== 'all') && (
                <Button
                  variant="link"
                  onClick={() => {
                    setSearch('')
                    setStatusFilter('all')
                    setTierFilter('all')
                    setPage(0)
                  }}
                >
                  Clear filters
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
