import { createRoute } from '@tanstack/react-router';
import { authenticatedRoute } from '../_authenticated';
import { CustomFieldsPage } from '@/features/customFields/pages/CustomFieldsPage';

/**
 * Custom Fields Admin Route
 *
 * Configuration engine for custom fields.
 * Allows administrators to add custom fields to any entity type.
 */
export const customFieldsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/admin/custom-fields',
  component: CustomFieldsPage,
});
