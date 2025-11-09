/**
 * ProductionEntryForm Component
 *
 * Form for logging production quantities with real-time yield calculation
 */
import { useState } from 'react'
import { Card, Input, Textarea, Label, Button, Body, Caption } from '@/design-system/atoms'
import { useAuthStore } from '@/stores/auth.store'
import { useLogProduction } from '../hooks/useProductionLogs'
import type { ProductionLog } from '../types/productionLog.types'

export interface ProductionEntryFormProps {
  workOrderId?: number
  onSuccess?: (log: ProductionLog) => void
}

export function ProductionEntryForm({ workOrderId, onSuccess }: ProductionEntryFormProps) {
  const { currentOrg, currentPlant } = useAuthStore()
  const logProductionMutation = useLogProduction()

  const [quantityProduced, setQuantityProduced] = useState('')
  const [quantityScrapped, setQuantityScrapped] = useState('0')
  const [quantityReworked, setQuantityReworked] = useState('0')
  const [operatorId, setOperatorId] = useState('')
  const [shiftId, setShiftId] = useState('')
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const calculateYieldRate = (): number | null => {
    const produced = parseFloat(quantityProduced) || 0
    const scrapped = parseFloat(quantityScrapped) || 0
    const reworked = parseFloat(quantityReworked) || 0
    const total = produced + scrapped + reworked

    if (total === 0) return null
    return (produced / total) * 100
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    const produced = parseFloat(quantityProduced)
    if (!quantityProduced || isNaN(produced) || produced < 0) {
      newErrors.quantityProduced = 'Quantity produced must be greater than or equal to 0'
    }

    const scrapped = parseFloat(quantityScrapped)
    if (isNaN(scrapped) || scrapped < 0) {
      newErrors.quantityScrapped = 'Quantity scrapped must be greater than or equal to 0'
    }

    const reworked = parseFloat(quantityReworked)
    if (isNaN(reworked) || reworked < 0) {
      newErrors.quantityReworked = 'Quantity reworked must be greater than or equal to 0'
    }

    if (produced + scrapped + reworked === 0) {
      newErrors.quantityProduced = 'At least one quantity must be greater than 0'
    }

    if (!workOrderId) {
      newErrors.workOrderId = 'Work order is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return
    if (!currentOrg || !currentPlant || !workOrderId) return

    try {
      const data = {
        organization_id: currentOrg.id,
        plant_id: currentPlant.id,
        work_order_id: workOrderId,
        quantity_produced: parseFloat(quantityProduced),
        quantity_scrapped: parseFloat(quantityScrapped) || 0,
        quantity_reworked: parseFloat(quantityReworked) || 0,
        operator_id: operatorId ? parseInt(operatorId) : undefined,
        shift_id: shiftId ? parseInt(shiftId) : undefined,
        notes: notes || undefined,
      }

      const result = await logProductionMutation.mutateAsync(data)

      // Reset form
      setQuantityProduced('')
      setQuantityScrapped('0')
      setQuantityReworked('0')
      setOperatorId('')
      setShiftId('')
      setNotes('')
      setErrors({})

      if (onSuccess) {
        onSuccess(result)
      }
    } catch (error) {
      // Error already captured by logProductionMutation.isError state
      // TanStack Query handles error state automatically
    }
  }

  const yieldRate = calculateYieldRate()
  const isValid = !errors.quantityProduced && quantityProduced && parseFloat(quantityProduced) >= 0

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="text-lg font-semibold mb-4">Log Production</h3>

        {!workOrderId && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
            <Caption className="text-yellow-800">Please select a work order first</Caption>
          </div>
        )}

        {/* Quantity Produced */}
        <div>
          <Label htmlFor="quantity-produced">Quantity Produced *</Label>
          <Input
            id="quantity-produced"
            type="number"
            min="0"
            step="1"
            value={quantityProduced}
            onChange={(e) => setQuantityProduced(e.target.value)}
            onBlur={() => validate()}
            className={errors.quantityProduced ? 'border-red-500' : ''}
          />
          {errors.quantityProduced && (
            <Caption className="text-red-600 mt-1">{errors.quantityProduced}</Caption>
          )}
        </div>

        {/* Quantity Scrapped */}
        <div>
          <Label htmlFor="quantity-scrapped">Quantity Scrapped</Label>
          <Input
            id="quantity-scrapped"
            type="number"
            min="0"
            step="1"
            value={quantityScrapped}
            onChange={(e) => setQuantityScrapped(e.target.value)}
            onBlur={() => validate()}
            className={errors.quantityScrapped ? 'border-red-500' : ''}
          />
          {errors.quantityScrapped && (
            <Caption className="text-red-600 mt-1">{errors.quantityScrapped}</Caption>
          )}
        </div>

        {/* Quantity Reworked */}
        <div>
          <Label htmlFor="quantity-reworked">Quantity Reworked</Label>
          <Input
            id="quantity-reworked"
            type="number"
            min="0"
            step="1"
            value={quantityReworked}
            onChange={(e) => setQuantityReworked(e.target.value)}
            onBlur={() => validate()}
            className={errors.quantityReworked ? 'border-red-500' : ''}
          />
          {errors.quantityReworked && (
            <Caption className="text-red-600 mt-1">{errors.quantityReworked}</Caption>
          )}
        </div>

        {/* Yield Rate Display */}
        {yieldRate !== null && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded">
            <Caption className="text-gray-600">Estimated Yield Rate:</Caption>
            <Body className="text-xl font-bold text-blue-600">{yieldRate.toFixed(1)}%</Body>
          </div>
        )}

        {/* Operator ID */}
        <div>
          <Label htmlFor="operator-id">Operator ID</Label>
          <Input
            id="operator-id"
            type="number"
            value={operatorId}
            onChange={(e) => setOperatorId(e.target.value)}
          />
        </div>

        {/* Shift ID */}
        <div>
          <Label htmlFor="shift-id">Shift ID</Label>
          <Input
            id="shift-id"
            type="number"
            value={shiftId}
            onChange={(e) => setShiftId(e.target.value)}
          />
        </div>

        {/* Notes */}
        <div>
          <Label htmlFor="notes">Notes</Label>
          <Textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
          />
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          disabled={!isValid || !workOrderId || logProductionMutation.isPending}
          isLoading={logProductionMutation.isPending}
          className="w-full"
        >
          {logProductionMutation.isPending ? 'Logging...' : 'Submit Production Log'}
        </Button>

        {logProductionMutation.isSuccess && (
          <div className="p-3 bg-green-50 border border-green-200 rounded">
            <Caption className="text-green-800">Production logged successfully!</Caption>
          </div>
        )}

        {logProductionMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded">
            <Caption className="text-red-800">
              Error logging production. Please try again.
            </Caption>
          </div>
        )}
      </form>
    </Card>
  )
}
