/**
 * useProjects Hooks Tests
 *
 * TDD: RED phase - Tests written before implementation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProjects, useProject, useCreateProject, useUpdateProject, useDeleteProject } from '../hooks/useProjects'
import { projectsService } from '../services/projects.service'
import { ProjectStatus } from '../types/project.types'
import type { ReactNode } from 'react'

vi.mock('../services/projects.service')
vi.mock('../../../stores/auth.store', () => ({
  useAuthStore: vi.fn((selector) => {
    const state = {
      currentPlant: { id: 1, plant_code: 'P001', plant_name: 'Test Plant' },
    }
    return selector ? selector(state) : state
  }),
}))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const wrapper = ({ children }: { children: ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
)

describe('useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('should fetch projects list', async () => {
    const mockProjects = {
      projects: [
        {
          id: 1,
          organization_id: 1,
          plant_id: 1,
          project_code: 'PRJ-001',
          project_name: 'Test Project',
          status: ProjectStatus.ACTIVE,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    }

    vi.mocked(projectsService.list).mockResolvedValue(mockProjects)

    const { result } = renderHook(() => useProjects(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProjects)
    expect(projectsService.list).toHaveBeenCalledWith({ plant_id: 1 })
  })

  it('should fetch projects with custom filters', async () => {
    const mockProjects = {
      projects: [],
      total: 0,
      page: 1,
      page_size: 10,
    }

    vi.mocked(projectsService.list).mockResolvedValue(mockProjects)

    const { result } = renderHook(
      () => useProjects({ status: ProjectStatus.PLANNING, page: 1, page_size: 10 }),
      { wrapper }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(projectsService.list).toHaveBeenCalledWith({
      plant_id: 1,
      status: ProjectStatus.PLANNING,
      page: 1,
      page_size: 10,
    })
  })

  it('should handle errors', async () => {
    vi.mocked(projectsService.list).mockRejectedValue(new Error('API Error'))

    const { result } = renderHook(() => useProjects(), { wrapper })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeTruthy()
  })
})

describe('useProject', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('should fetch single project by ID', async () => {
    const mockProject = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      project_code: 'PRJ-001',
      project_name: 'Test Project',
      status: ProjectStatus.ACTIVE,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }

    vi.mocked(projectsService.getById).mockResolvedValue(mockProject)

    const { result } = renderHook(() => useProject(1), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProject)
    expect(projectsService.getById).toHaveBeenCalledWith(1)
  })
})

describe('useCreateProject', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('should create a new project', async () => {
    const newProject = {
      plant_id: 1,
      project_code: 'PRJ-002',
      project_name: 'New Project',
      status: ProjectStatus.PLANNING,
    }

    const mockResponse = {
      id: 2,
      organization_id: 1,
      ...newProject,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }

    vi.mocked(projectsService.create).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useCreateProject(), { wrapper })

    result.current.mutate(newProject)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockResponse)
    expect(projectsService.create).toHaveBeenCalledWith(newProject)
  })

  it('should invalidate projects query on success', async () => {
    const newProject = {
      plant_id: 1,
      project_code: 'PRJ-002',
      project_name: 'New Project',
    }

    const mockResponse = {
      id: 2,
      organization_id: 1,
      ...newProject,
      status: ProjectStatus.PLANNING,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    }

    vi.mocked(projectsService.create).mockResolvedValue(mockResponse)

    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useCreateProject(), { wrapper })

    result.current.mutate(newProject)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['projects'] })
  })
})

describe('useUpdateProject', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('should update an existing project', async () => {
    const updateData = {
      id: 1,
      data: {
        project_name: 'Updated Project',
        status: ProjectStatus.ACTIVE,
      },
    }

    const mockResponse = {
      id: 1,
      organization_id: 1,
      plant_id: 1,
      project_code: 'PRJ-001',
      project_name: 'Updated Project',
      status: ProjectStatus.ACTIVE,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    }

    vi.mocked(projectsService.update).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useUpdateProject(), { wrapper })

    result.current.mutate(updateData)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockResponse)
    expect(projectsService.update).toHaveBeenCalledWith(1, updateData.data)
  })
})

describe('useDeleteProject', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    queryClient.clear()
  })

  it('should delete a project', async () => {
    vi.mocked(projectsService.delete).mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteProject(), { wrapper })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(projectsService.delete).toHaveBeenCalledWith(1)
  })

  it('should invalidate projects query on success', async () => {
    vi.mocked(projectsService.delete).mockResolvedValue(undefined)

    const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(() => useDeleteProject(), { wrapper })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['projects'] })
  })
})
