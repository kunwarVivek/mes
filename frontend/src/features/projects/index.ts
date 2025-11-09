/**
 * Projects Feature Module
 *
 * Exports all public APIs for the Projects feature
 */

// Types
export type {
  Project,
  ProjectCreateRequest,
  ProjectUpdateRequest,
  ProjectListResponse,
  ProjectFilters,
} from './types/project.types'
export { ProjectStatus } from './types/project.types'

// Services
export { projectsService } from './services/projects.service'

// Hooks
export {
  useProjects,
  useProject,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
  PROJECTS_QUERY_KEY,
} from './hooks/useProjects'

// Components
export { ProjectsTable } from './components/ProjectsTable'
export { ProjectForm } from './components/ProjectForm'

// Pages
export { ProjectsPage } from './pages/ProjectsPage'
