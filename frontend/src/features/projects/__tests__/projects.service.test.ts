/**
 * Projects Service Tests
 *
 * TDD: RED phase - Tests written before implementation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import apiClient from '../../../lib/api-client'
import { projectsService } from '../services/projects.service'
import { ProjectStatus } from '../types/project.types'
import type { Project, ProjectCreateRequest, ProjectUpdateRequest } from '../types/project.types'

vi.mock('../../../lib/api-client')
const mockedApiClient = vi.mocked(apiClient, true)

describe('projectsService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('list', () => {
    it('should fetch all projects without filters', async () => {
      const mockResponse = {
        data: {
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
        },
      }

      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await projectsService.list()

      expect(mockedApiClient.get).toHaveBeenCalledWith('/projects', { params: undefined })
      expect(result).toEqual(mockResponse.data)
      expect(result.projects).toHaveLength(1)
      expect(result.projects[0].project_code).toBe('PRJ-001')
    })

    it('should fetch projects with filters', async () => {
      const mockResponse = {
        data: {
          projects: [],
          total: 0,
          page: 1,
          page_size: 20,
        },
      }

      const filters = {
        plant_id: 1,
        status: ProjectStatus.ACTIVE,
        page: 1,
        page_size: 10,
      }

      mockedApiClient.get.mockResolvedValue(mockResponse)

      const result = await projectsService.list(filters)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/projects', { params: filters })
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle API errors', async () => {
      mockedApiClient.get.mockRejectedValue(new Error('Internal Server Error'))

      await expect(projectsService.list()).rejects.toThrow()
    })
  })

  describe('getById', () => {
    it('should fetch project by ID', async () => {
      const mockProject: Project = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        project_code: 'PRJ-001',
        project_name: 'Test Project',
        description: 'Test description',
        status: ProjectStatus.ACTIVE,
        customer_name: 'ACME Corp',
        start_date: '2025-01-01',
        end_date: '2025-12-31',
        budget_amount: 100000,
        currency_code: 'USD',
        project_manager: 'John Doe',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockedApiClient.get.mockResolvedValue({ data: mockProject })

      const result = await projectsService.getById(1)

      expect(mockedApiClient.get).toHaveBeenCalledWith('/projects/1')
      expect(result).toEqual(mockProject)
      expect(result.id).toBe(1)
      expect(result.project_code).toBe('PRJ-001')
    })

    it('should handle 404 errors', async () => {
      mockedApiClient.get.mockRejectedValue(new Error('Not found'))

      await expect(projectsService.getById(999)).rejects.toThrow()
    })
  })

  describe('create', () => {
    it('should create a new project', async () => {
      const createData: ProjectCreateRequest = {
        plant_id: 1,
        project_code: 'PRJ-002',
        project_name: 'New Project',
        description: 'New project description',
        status: ProjectStatus.PLANNING,
        customer_name: 'ACME Corp',
        start_date: '2025-02-01',
        budget_amount: 50000,
        currency_code: 'USD',
      }

      const mockResponse: Project = {
        id: 2,
        organization_id: 1,
        ...createData,
        status: ProjectStatus.PLANNING,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockedApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await projectsService.create(createData)

      expect(mockedApiClient.post).toHaveBeenCalledWith('/projects', createData)
      expect(result).toEqual(mockResponse)
      expect(result.id).toBe(2)
      expect(result.project_code).toBe('PRJ-002')
    })

    it('should handle validation errors', async () => {
      const invalidData: ProjectCreateRequest = {
        plant_id: 1,
        project_code: '',
        project_name: '',
      }

      mockedApiClient.post.mockRejectedValue(new Error('Validation error'))

      await expect(projectsService.create(invalidData)).rejects.toThrow()
    })
  })

  describe('update', () => {
    it('should update an existing project', async () => {
      const updateData: ProjectUpdateRequest = {
        project_name: 'Updated Project Name',
        status: ProjectStatus.ACTIVE,
        budget_amount: 75000,
      }

      const mockResponse: Project = {
        id: 1,
        organization_id: 1,
        plant_id: 1,
        project_code: 'PRJ-001',
        project_name: 'Updated Project Name',
        status: ProjectStatus.ACTIVE,
        budget_amount: 75000,
        currency_code: 'USD',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      }

      mockedApiClient.put.mockResolvedValue({ data: mockResponse })

      const result = await projectsService.update(1, updateData)

      expect(mockedApiClient.put).toHaveBeenCalledWith('/projects/1', updateData)
      expect(result).toEqual(mockResponse)
      expect(result.project_name).toBe('Updated Project Name')
      expect(result.status).toBe(ProjectStatus.ACTIVE)
    })

    it('should handle update errors', async () => {
      mockedApiClient.put.mockRejectedValue(new Error('Not found'))

      await expect(projectsService.update(999, {})).rejects.toThrow()
    })
  })

  describe('delete', () => {
    it('should delete a project', async () => {
      mockedApiClient.delete.mockResolvedValue({ data: null })

      await projectsService.delete(1)

      expect(mockedApiClient.delete).toHaveBeenCalledWith('/projects/1')
    })

    it('should handle delete errors', async () => {
      mockedApiClient.delete.mockRejectedValue(new Error('Not found'))

      await expect(projectsService.delete(999)).rejects.toThrow()
    })
  })
})
