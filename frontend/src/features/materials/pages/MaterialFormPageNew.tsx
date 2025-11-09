/**
 * MaterialFormPage Component
 *
 * Page for creating and editing materials
 */
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { MaterialForm } from '../components/MaterialForm'
import { useMaterial } from '../hooks/useMaterial'
import { ArrowLeft } from 'lucide-react'

export function MaterialFormPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const materialId = id ? parseInt(id, 10) : undefined

  const { data: material, isLoading, error } = useMaterial(materialId!)

  const isEditMode = !!materialId

  const handleSuccess = () => {
    navigate('/materials')
  }

  const handleBack = () => {
    navigate('/materials')
  }

  if (isEditMode && isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Loading...</p>
      </div>
    )
  }

  if (isEditMode && error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-destructive">Error loading material. Please try again.</p>
      </div>
    )
  }

  if (isEditMode && !material) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-destructive">Material not found.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={handleBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {isEditMode ? 'Edit Material' : 'Create Material'}
          </h1>
          <p className="text-muted-foreground">
            {isEditMode
              ? 'Update material information'
              : 'Create a new material in the system'}
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-card rounded-lg border p-6">
        <MaterialForm
          materialId={materialId}
          defaultValues={material}
          onSuccess={handleSuccess}
        />
      </div>
    </div>
  )
}
