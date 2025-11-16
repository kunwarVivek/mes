import React, { useState } from 'react';
import { CustomFieldsList } from '../components/CustomFieldsList';
import { CustomFieldForm } from '../components/CustomFieldForm';
import type { CustomField } from '@/types/customFields';

/**
 * Custom Fields Admin Page
 *
 * Allows administrators to configure custom fields for any entity type.
 * Core of the Configuration Engine for self-service customization.
 */
export const CustomFieldsPage: React.FC = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingField, setEditingField] = useState<CustomField | undefined>(undefined);

  const handleCreateNew = () => {
    setEditingField(undefined);
    setIsFormOpen(true);
  };

  const handleEdit = (field: CustomField) => {
    setEditingField(field);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingField(undefined);
  };

  return (
    <div className="p-6">
      <CustomFieldsList onEdit={handleEdit} onCreateNew={handleCreateNew} />

      {isFormOpen && (
        <CustomFieldForm field={editingField} onClose={handleCloseForm} />
      )}
    </div>
  );
};

export default CustomFieldsPage;
