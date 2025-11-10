/**
 * Sanitized Display Helpers
 *
 * Helper functions for safely displaying user-generated content
 */
import { sanitizeHtml } from './sanitize'

/**
 * Creates props for safely rendering sanitized HTML
 * 
 * @param content - User-generated content
 * @param maxLength - Optional truncation length
 * @returns Props object with dangerouslySetInnerHTML
 * 
 * @example
 * ```tsx
 * <span {...getSanitizedProps(userContent, 50)} />
 * ```
 */
export function getSanitizedProps(content: string | null | undefined, maxLength?: number) {
  const sanitized = sanitizeHtml(content)
  const displayContent = maxLength && sanitized.length > maxLength
    ? sanitized.substring(0, maxLength) + '...'
    : sanitized

  return {
    dangerouslySetInnerHTML: { __html: displayContent },
    title: sanitized,
  }
}
