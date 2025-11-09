/**
 * PMScheduleForm Component
 *
 * Form for creating and editing PM schedules
 */
import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createPMScheduleSchema, updatePMScheduleSchema } from '../schemas/maintenance.schema'
import type { PMSchedule, CreatePMScheduleDTO, UpdatePMScheduleDTO } from '../types/maintenance.types'
import './PMScheduleForm.css'

interface Machine {
  id: number
  name: string
}

interface PMScheduleFormProps {
  machines: Machine[]
  schedule?: PMSchedule
  onSubmit: (data: CreatePMScheduleDTO | UpdatePMScheduleDTO) => void
  onCancel?: () => void
}

export const PMScheduleForm: React.FC<PMScheduleFormProps> = ({
  machines,
  schedule,
  onSubmit,
  onCancel,
}) => {
  const isEditMode = !!schedule

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    reset,
  } = useForm<any>({
    resolver: zodResolver(isEditMode ? updatePMScheduleSchema : createPMScheduleSchema),
    defaultValues: schedule
      ? {
          schedule_name: schedule.schedule_name,
          frequency_days: schedule.frequency_days || undefined,
          meter_threshold: schedule.meter_threshold || undefined,
          is_active: schedule.is_active,
        }
      : {
          is_active: true,
        },
  })

  const triggerType = watch('trigger_type')

  useEffect(() => {
    if (schedule) {
      reset({
        schedule_name: schedule.schedule_name,
        frequency_days: schedule.frequency_days || undefined,
        meter_threshold: schedule.meter_threshold || undefined,
        is_active: schedule.is_active,
      })
    }
  }, [schedule, reset])

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="pm-schedule-form">
      <div className="form-group">
        <label htmlFor="schedule_code">Schedule Code *</label>
        <input
          id="schedule_code"
          type="text"
          disabled={isEditMode}
          {...register('schedule_code')}
          className={errors.schedule_code ? 'error' : ''}
          defaultValue={schedule?.schedule_code}
        />
        {errors.schedule_code && (
          <span className="error-message">{errors.schedule_code.message}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="schedule_name">Schedule Name *</label>
        <input
          id="schedule_name"
          type="text"
          {...register('schedule_name')}
          className={errors.schedule_name ? 'error' : ''}
        />
        {errors.schedule_name && (
          <span className="error-message">{errors.schedule_name.message}</span>
        )}
      </div>

      {!isEditMode && (
        <>
          <div className="form-group">
            <label htmlFor="machine_id">Machine *</label>
            <select
              id="machine_id"
              {...register('machine_id', { valueAsNumber: true })}
              className={errors.machine_id ? 'error' : ''}
            >
              <option value="">Select a machine</option>
              {machines.map((machine) => (
                <option key={machine.id} value={machine.id}>
                  {machine.name}
                </option>
              ))}
            </select>
            {errors.machine_id && (
              <span className="error-message">{errors.machine_id.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="trigger_type">Trigger Type *</label>
            <select
              id="trigger_type"
              {...register('trigger_type')}
              className={errors.trigger_type ? 'error' : ''}
            >
              <option value="">Select trigger type</option>
              <option value="CALENDAR">CALENDAR</option>
              <option value="METER">METER</option>
            </select>
            {errors.trigger_type && (
              <span className="error-message">{errors.trigger_type.message}</span>
            )}
          </div>
        </>
      )}

      {(triggerType === 'CALENDAR' || schedule?.trigger_type === 'CALENDAR') && (
        <div className="form-group">
          <label htmlFor="frequency_days">Frequency (days) *</label>
          <input
            id="frequency_days"
            type="number"
            {...register('frequency_days', { valueAsNumber: true })}
            className={errors.frequency_days ? 'error' : ''}
          />
          {errors.frequency_days && (
            <span className="error-message">{errors.frequency_days.message}</span>
          )}
        </div>
      )}

      {(triggerType === 'METER' || schedule?.trigger_type === 'METER') && (
        <div className="form-group">
          <label htmlFor="meter_threshold">Meter Threshold *</label>
          <input
            id="meter_threshold"
            type="number"
            {...register('meter_threshold', { valueAsNumber: true })}
            className={errors.meter_threshold ? 'error' : ''}
          />
          {errors.meter_threshold && (
            <span className="error-message">{errors.meter_threshold.message}</span>
          )}
        </div>
      )}

      <div className="form-group">
        <label className="checkbox-label">
          <input type="checkbox" {...register('is_active')} />
          <span>Active</span>
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary">
          {isEditMode ? 'Update' : 'Create'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn btn--secondary">
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
