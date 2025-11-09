/**
 * ProjectsTable Component
 *
 * Displays projects in a table format with actions
 * Aligned with backend Project model
 */
import { Badge, Button } from '../../../design-system/atoms'
import type { Project } from '../types/project.types'
import { ProjectStatus } from '../types/project.types'

interface ProjectsTableProps {
  projects: Project[]
  isLoading: boolean
  onEdit: (project: Project) => void
  onDelete: (id: number) => void
}

const STATUS_COLORS: Record<ProjectStatus, 'blue' | 'green' | 'yellow' | 'gray' | 'red'> = {
  [ProjectStatus.PLANNING]: 'blue',
  [ProjectStatus.ACTIVE]: 'green',
  [ProjectStatus.ON_HOLD]: 'yellow',
  [ProjectStatus.COMPLETED]: 'gray',
  [ProjectStatus.CANCELLED]: 'red',
}

function formatDate(date?: string): string {
  if (!date) return '-'
  return new Intl.DateTimeFormat('en-US').format(new Date(date))
}

export function ProjectsTable({ projects, isLoading, onEdit, onDelete }: ProjectsTableProps) {
  if (isLoading) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Loading projects...</p>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No projects found</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Project Code
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Planned Start
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Planned End
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Priority
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Active
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {projects.map((project) => (
            <tr key={project.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {project.project_code}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <div>
                  <div className="font-medium">{project.project_name}</div>
                  {project.description && (
                    <div className="text-gray-500 text-xs truncate max-w-xs">
                      {project.description}
                    </div>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge color={STATUS_COLORS[project.status]}>{project.status}</Badge>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(project.planned_start_date)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(project.planned_end_date)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {project.priority}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className={project.is_active ? 'text-green-600' : 'text-gray-400'}>
                  {project.is_active ? 'Yes' : 'No'}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                <Button variant="ghost" size="sm" onClick={() => onEdit(project)} aria-label="Edit project">
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(project.id)}
                  aria-label="Delete project"
                  className="text-red-600 hover:text-red-900"
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
