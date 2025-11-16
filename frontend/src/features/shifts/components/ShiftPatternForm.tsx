import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/services/api.client';
import { X } from 'lucide-react';

interface ShiftPatternFormProps {
  shift?: any;
  onClose: () => void;
}

/**
 * Shift Pattern Form
 *
 * Create or edit shift patterns with schedules, targets, and breaks.
 */
export const ShiftPatternForm: React.FC<ShiftPatternFormProps> = ({ shift, onClose }) => {
  const queryClient = useQueryClient();
  const isEditMode = !!shift;

  const [formData, setFormData] = useState({
    name: shift?.name || '',
    start_time: shift?.start_time || '08:00',
    end_time: shift?.end_time || '16:00',
    break_duration: shift?.break_duration || 30,
    days_active: shift?.days_active || 'Mon,Tue,Wed,Thu,Fri',
    production_target: shift?.production_target || 100,
    oee_target: shift?.oee_target || 85,
  });

  const saveMutation = useMutation({
    mutationFn: async (data: any) => {
      if (isEditMode) {
        return await apiClient.put(`/api/v1/shifts/${shift.id}`, data);
      } else {
        return await apiClient.post('/api/v1/shifts', data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shifts'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditMode ? 'Edit Shift Pattern' : 'Create Shift Pattern'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Shift Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Morning Shift, Day Shift"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Time <span className="text-red-500">*</span>
              </label>
              <input
                type="time"
                value={formData.start_time}
                onChange={e => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Time <span className="text-red-500">*</span>
              </label>
              <input
                type="time"
                value={formData.end_time}
                onChange={e => setFormData({ ...formData, end_time: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Break Duration (minutes)
            </label>
            <input
              type="number"
              value={formData.break_duration}
              onChange={e => setFormData({ ...formData, break_duration: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Days Active
            </label>
            <input
              type="text"
              value={formData.days_active}
              onChange={e => setFormData({ ...formData, days_active: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Mon,Tue,Wed,Thu,Fri"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Production Target (units/shift)
              </label>
              <input
                type="number"
                value={formData.production_target}
                onChange={e => setFormData({ ...formData, production_target: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                OEE Target (%)
              </label>
              <input
                type="number"
                value={formData.oee_target}
                onChange={e => setFormData({ ...formData, oee_target: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
                max="100"
                step="0.1"
              />
            </div>
          </div>

          <div className="border-t border-gray-200 pt-4 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saveMutation.isPending ? 'Saving...' : isEditMode ? 'Update Shift' : 'Create Shift'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ShiftPatternForm;
