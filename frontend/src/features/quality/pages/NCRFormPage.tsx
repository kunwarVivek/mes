/**
 * NCRFormPage Component
 *
 * Page for creating NCRs with breadcrumb navigation and form
 */
import { useNavigate } from 'react-router-dom'
import { NCRForm } from '../components/NCRForm'

interface BreadcrumbItem {
  label: string
  onClick?: () => void
}

export function NCRFormPage() {
  const navigate = useNavigate()

  const breadcrumbs: BreadcrumbItem[] = [
    {
      label: 'Home',
      onClick: () => navigate('/'),
    },
    {
      label: 'Quality',
      onClick: () => navigate('/quality/ncrs'),
    },
    {
      label: 'Create NCR',
    },
  ]

  const handleSuccess = () => {
    navigate('/quality/ncrs')
  }

  return (
    <div className="space-y-6 p-6">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center space-x-2 text-sm text-muted-foreground">
          {breadcrumbs.map((crumb, index) => (
            <li key={index} className="flex items-center">
              {index > 0 && <span className="mx-2">/</span>}
              {crumb.onClick ? (
                <button
                  onClick={crumb.onClick}
                  className="hover:text-foreground transition-colors"
                >
                  {crumb.label}
                </button>
              ) : (
                <span className="text-foreground font-medium">{crumb.label}</span>
              )}
            </li>
          ))}
        </ol>
      </nav>

      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Create Non-Conformance Report</h1>
        <p className="text-muted-foreground">Record a new quality non-conformance</p>
      </div>

      {/* NCR Form */}
      <div className="max-w-3xl">
        <NCRForm onSuccess={handleSuccess} />
      </div>
    </div>
  )
}
