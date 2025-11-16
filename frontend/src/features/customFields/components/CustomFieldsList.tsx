import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { customFieldsService } from '@/services/customFields.service';
import type { CustomField, EntityType } from '@/types/customFields';
import { Plus, Edit, Trash2, Search, Filter } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface CustomFieldsListProps {
  onEdit?: (field: CustomField) => void;
  onCreateNew?: () => void;
}

/**
 * Custom Fields List Component
 *
 * Displays all custom fields with filtering by entity type.
 * Allows create, edit, delete operations.
 */
export const CustomFieldsList: React.FC<CustomFieldsListProps> = ({
  onEdit,
  onCreateNew,
}) => {
  const queryClient = useQueryClient();
  const [selectedEntityType, setSelectedEntityType] = useState<EntityType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all custom fields
  const { data: allFields = [], isLoading, error } = useQuery<CustomField[]>({
    queryKey: ['customFields'],
    queryFn: () => customFieldsService.getAllFields(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (fieldId: number) => customFieldsService.deleteField(fieldId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customFields'] });
    },
  });

  // Filter fields
  const filteredFields = allFields.filter(field => {
    const matchesEntity =
      selectedEntityType === 'all' || field.entity_type === selectedEntityType;
    const matchesSearch =
      !searchQuery ||
      field.field_label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      field.field_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      field.entity_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesEntity && matchesSearch;
  });

  // Group by entity type
  const fieldsByEntity = filteredFields.reduce((acc, field) => {
    if (!acc[field.entity_type]) {
      acc[field.entity_type] = [];
    }
    acc[field.entity_type].push(field);
    return acc;
  }, {} as Record<EntityType, CustomField[]>);

  const handleDelete = async (field: CustomField) => {
    if (
      window.confirm(
        `Are you sure you want to delete the custom field "${field.field_label}"?\n\nThis will also delete all associated values.`
      )
    ) {
      deleteMutation.mutate(field.id);
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-600">Loading custom fields...</div>;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Failed to load custom fields: {error.message}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Custom Fields</h2>
          <p className="text-gray-600 mt-1">
            Configure custom fields for any entity type ({allFields.length} total)
          </p>
        </div>
        <button
          onClick={onCreateNew}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New Custom Field
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search by field name, code, or entity type..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Entity Type Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <select
            value={selectedEntityType}
            onChange={e => setSelectedEntityType(e.target.value as EntityType | 'all')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Entity Types</option>
            <option value="material">Materials</option>
            <option value="work_order">Work Orders</option>
            <option value="project">Projects</option>
            <option value="ncr">NCRs</option>
            <option value="machine">Machines</option>
            <option value="quality">Quality</option>
            <option value="maintenance">Maintenance</option>
            <option value="shift">Shifts</option>
            <option value="lane">Lanes</option>
            <option value="bom">BOMs</option>
          </select>
        </div>
      </div>

      {/* Fields grouped by entity type */}
      {Object.keys(fieldsByEntity).length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-500">No custom fields found</p>
          <p className="text-sm text-gray-400 mt-1">
            {searchQuery
              ? 'Try a different search term'
              : 'Create your first custom field to get started'}
          </p>
        </div>
      ) : (
        Object.entries(fieldsByEntity).map(([entityType, fields]) => (
          <div key={entityType} className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 capitalize">
                {entityType.replace('_', ' ')} ({fields.length})
              </h3>
            </div>

            <div className="divide-y divide-gray-200">
              {fields
                .sort((a, b) => a.display_order - b.display_order)
                .map(field => (
                  <div
                    key={field.id}
                    className="px-6 py-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h4 className="font-medium text-gray-900">{field.field_label}</h4>
                          <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
                            {field.field_type}
                          </span>
                          {field.is_required && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-800">
                              Required
                            </span>
                          )}
                          {!field.is_active && (
                            <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                              Inactive
                            </span>
                          )}
                        </div>

                        <div className="mt-1 text-sm text-gray-600 space-y-1">
                          <div>
                            <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                              {field.field_code}
                            </span>
                          </div>
                          {field.description && <p className="text-gray-500">{field.description}</p>}
                          {field.default_value && (
                            <p className="text-gray-500">Default: {field.default_value}</p>
                          )}
                          {field.validation_rules && Object.keys(field.validation_rules).length > 0 && (
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <span className="font-medium">Validation:</span>
                              <span>
                                {Object.entries(field.validation_rules)
                                  .map(([key, value]) => `${key}: ${value}`)
                                  .join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onEdit?.(field)}
                          className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Edit field"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(field)}
                          className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete field"
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default CustomFieldsList;
