import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../stores/auth.store'
import apiClient from '../lib/api-client'

/**
 * TenantSelector Component
 *
 * Allows users to switch between organizations and plants.
 * Sets tenant context for Row Level Security (RLS).
 *
 * Features:
 * - Fetches available organizations for user
 * - Fetches available plants for selected organization
 * - Updates auth store with current selections
 * - Displays current selections
 */

interface Organization {
  id: number
  org_code: string
  org_name: string
}

interface Plant {
  id: number
  plant_code: string
  plant_name: string
  organization_id: number
}

export function TenantSelector() {
  const { currentOrg, currentPlant, setCurrentOrg, setCurrentPlant } = useAuthStore()

  // Fetch available organizations
  const { data: organizations, isLoading: isLoadingOrgs } = useQuery<Organization[]>({
    queryKey: ['organizations'],
    queryFn: async () => {
      const response = await apiClient.get('/organizations')
      return response.data
    },
  })

  // Fetch plants for current organization
  const { data: plants, isLoading: isLoadingPlants } = useQuery<Plant[]>({
    queryKey: ['plants', currentOrg?.id],
    queryFn: async () => {
      if (!currentOrg) return []
      const response = await apiClient.get(`/organizations/${currentOrg.id}/plants`)
      return response.data
    },
    enabled: !!currentOrg,
  })

  const handleOrgChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const orgId = parseInt(e.target.value)
    const org = organizations?.find((o) => o.id === orgId)
    setCurrentOrg(org || null)
    // Clear plant selection when org changes
    setCurrentPlant(null)
  }

  const handlePlantChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const plantId = parseInt(e.target.value)
    const plant = plants?.find((p) => p.id === plantId)
    setCurrentPlant(plant || null)
  }

  return (
    <div className="flex gap-4 items-center">
      {/* Organization Selector */}
      <div className="flex flex-col">
        <label htmlFor="org-select" className="text-sm font-medium mb-1">
          Organization
        </label>
        <select
          id="org-select"
          value={currentOrg?.id || ''}
          onChange={handleOrgChange}
          disabled={isLoadingOrgs}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select Organization</option>
          {organizations?.map((org) => (
            <option key={org.id} value={org.id}>
              {org.org_code} - {org.org_name}
            </option>
          ))}
        </select>
      </div>

      {/* Plant Selector */}
      <div className="flex flex-col">
        <label htmlFor="plant-select" className="text-sm font-medium mb-1">
          Plant
        </label>
        <select
          id="plant-select"
          value={currentPlant?.id || ''}
          onChange={handlePlantChange}
          disabled={!currentOrg || isLoadingPlants}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">Select Plant</option>
          {plants?.map((plant) => (
            <option key={plant.id} value={plant.id}>
              {plant.plant_code} - {plant.plant_name}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
