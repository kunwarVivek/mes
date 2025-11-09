/**
 * BOMLineForm Component
 *
 * Form for creating and editing BOM lines
 * Supports parent-child relationships
 */
import { useState, FormEvent } from 'react'
import { Button } from '../../../design-system/atoms/Button'
import { Input } from '../../../design-system/atoms/Input'
import type { BOMLineWithChildren, CreateBOMLineDTO } from '../types/bom.types'
import './BOMLineForm.css'

interface BOMLineFormProps {
  bomHeaderId: number
  line?: BOMLineWithChildren
  parentLine?: BOMLineWithChildren
  onSubmit: (data: CreateBOMLineDTO) => void
  onCancel: () => void
}

export function BOMLineForm({
  bomHeaderId,
  line,
  parentLine,
  onSubmit,
  onCancel
}: BOMLineFormProps) {
  const [formData, setFormData] = useState({
    component_material_id: line?.component_material_id?.toString() || '',
    quantity: line?.quantity?.toString() || '',
    unit_of_measure_id: line?.unit_of_measure_id?.toString() || '1',
    line_number: line?.line_number?.toString() || '',
    scrap_factor: line?.scrap_factor?.toString() || '0',
    is_phantom: line?.is_phantom || false,
    backflush: line?.backflush || false
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    const submitData: CreateBOMLineDTO = {
      bom_header_id: bomHeaderId,
      component_material_id: Number(formData.component_material_id),
      quantity: Number(formData.quantity),
      unit_of_measure_id: Number(formData.unit_of_measure_id),
      line_number: Number(formData.line_number),
      scrap_factor: Number(formData.scrap_factor),
      is_phantom: formData.is_phantom,
      backflush: formData.backflush
    }

    onSubmit(submitData)
  }

  const getTitle = () => {
    if (line) return 'Edit BOM Line'
    if (parentLine) return `Add Child to ${parentLine.component_material_name}`
    return 'Add BOM Line'
  }

  return (
    <form onSubmit={handleSubmit} className="bom-line-form">
      <h3 className="bom-line-form-title">{getTitle()}</h3>

      <div className="bom-line-form-grid">
        <div className="bom-line-form-field">
          <label htmlFor="component_material_id" className="bom-line-form-label">
            Component Material ID
          </label>
          <Input
            id="component_material_id"
            type="number"
            value={formData.component_material_id}
            onChange={(e) => setFormData({ ...formData, component_material_id: e.target.value })}
            required
            fullWidth
          />
        </div>

        <div className="bom-line-form-field">
          <label htmlFor="quantity" className="bom-line-form-label">
            Quantity
          </label>
          <Input
            id="quantity"
            type="number"
            step="0.001"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            required
            fullWidth
          />
        </div>

        <div className="bom-line-form-field">
          <label htmlFor="unit_of_measure" className="bom-line-form-label">
            Unit of Measure
          </label>
          <select
            id="unit_of_measure"
            value={formData.unit_of_measure_id}
            onChange={(e) => setFormData({ ...formData, unit_of_measure_id: e.target.value })}
            className="bom-line-form-select"
            required
          >
            <option value="1">Each (EA)</option>
            <option value="2">Kilogram (KG)</option>
            <option value="3">Pound (LB)</option>
            <option value="4">Meter (M)</option>
            <option value="5">Foot (FT)</option>
            <option value="6">Liter (L)</option>
            <option value="7">Gallon (GAL)</option>
          </select>
        </div>

        <div className="bom-line-form-field">
          <label htmlFor="line_number" className="bom-line-form-label">
            Line Number
          </label>
          <Input
            id="line_number"
            type="number"
            value={formData.line_number}
            onChange={(e) => setFormData({ ...formData, line_number: e.target.value })}
            required
            fullWidth
          />
        </div>

        <div className="bom-line-form-field">
          <label htmlFor="scrap_factor" className="bom-line-form-label">
            Scrap Factor (%)
          </label>
          <Input
            id="scrap_factor"
            type="number"
            step="0.1"
            value={formData.scrap_factor}
            onChange={(e) => setFormData({ ...formData, scrap_factor: e.target.value })}
            fullWidth
          />
        </div>

        <div className="bom-line-form-field-full">
          <div className="bom-line-form-checkbox">
            <input
              type="checkbox"
              id="is_phantom"
              checked={formData.is_phantom}
              onChange={(e) => setFormData({ ...formData, is_phantom: e.target.checked })}
            />
            <label htmlFor="is_phantom" className="bom-line-form-checkbox-label">
              Phantom BOM (consumed without stock transaction)
            </label>
          </div>

          <div className="bom-line-form-checkbox">
            <input
              type="checkbox"
              id="backflush"
              checked={formData.backflush}
              onChange={(e) => setFormData({ ...formData, backflush: e.target.checked })}
            />
            <label htmlFor="backflush" className="bom-line-form-checkbox-label">
              Backflush (automatically consume on production)
            </label>
          </div>
        </div>
      </div>

      <div className="bom-line-form-actions">
        <Button type="submit">
          {line ? 'Update' : 'Add'}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}
