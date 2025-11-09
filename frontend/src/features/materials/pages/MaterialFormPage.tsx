/**
 * MaterialFormPage Component
 *
 * Page for creating and editing materials
 */
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AppLayout } from '@/design-system/templates'
import { Heading1, Button } from '@/design-system/atoms'
import { MaterialForm } from '../components/MaterialForm'
import { useMaterial } from '../hooks/useMaterial'
import { useCreateMaterial } from '../hooks/useCreateMaterial'
import { useUpdateMaterial } from '../hooks/useUpdateMaterial'
import type { CreateMaterialDTO, UpdateMaterialDTO } from '../types/material.types'
import './MaterialFormPage.css'

export const MaterialFormPage = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEditMode = !!id

  const { data: material, isLoading: isFetching } = useMaterial(id ? parseInt(id) : 0)
  const createMutation = useCreateMaterial()
  const updateMutation = useUpdateMaterial()

  const isLoading = createMutation.isPending || updateMutation.isPending
  const error =
    createMutation.error instanceof Error
      ? createMutation.error.message
      : updateMutation.error instanceof Error
        ? updateMutation.error.message
        : undefined

  useEffect(() => {
    if (createMutation.isSuccess || updateMutation.isSuccess) {
      navigate('/materials')
    }
  }, [createMutation.isSuccess, updateMutation.isSuccess, navigate])

  const handleSubmit = async (data: CreateMaterialDTO | UpdateMaterialDTO) => {
    try {
      if (isEditMode && id) {
        await updateMutation.mutateAsync({
          id: parseInt(id),
          data: data as UpdateMaterialDTO,
        })
      } else {
        await createMutation.mutateAsync(data as CreateMaterialDTO)
      }
    } catch (err) {
      console.error('Failed to save material:', err)
    }
  }

  const handleCancel = () => {
    navigate('/materials')
  }

  if (isFetching && isEditMode) {
    return (
      <AppLayout>
        <div className="material-form-page">
          <div className="material-form-page__loading">Loading material...</div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="material-form-page">
        <div className="material-form-page__header">
          <Heading1>{isEditMode ? 'Edit Material' : 'Create Material'}</Heading1>
          <Button variant="ghost" onClick={handleCancel}>
            Back to Materials
          </Button>
        </div>

        <div className="material-form-page__breadcrumbs">
          <button onClick={() => navigate('/materials')} className="material-form-page__breadcrumb">
            Materials
          </button>
          <span className="material-form-page__breadcrumb-separator">/</span>
          <span className="material-form-page__breadcrumb-current">
            {isEditMode ? 'Edit' : 'Create'}
          </span>
        </div>

        <div className="material-form-page__content">
          <MaterialForm
            mode={isEditMode ? 'edit' : 'create'}
            initialData={material}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </AppLayout>
  )
}
