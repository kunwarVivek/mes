/**
 * Sanitization Utility
 *
 * Provides DOMPurify-based sanitization for user-generated content
 * to prevent XSS attacks
 */
import DOMPurify from 'dompurify'

/**
 * Sanitizes HTML content to prevent XSS attacks
 *
 * @param content - Raw HTML content that may contain malicious code
 * @returns Sanitized HTML safe for rendering
 *
 * @example
 * ```typescript
 * const userInput = '<script>alert("XSS")</script>Hello'
 * const safe = sanitizeHtml(userInput) // Returns: 'Hello'
 * ```
 */
export function sanitizeHtml(content: string | null | undefined): string {
  // Handle null/undefined
  if (content == null) {
    return ''
  }

  // Handle non-string values
  if (typeof content !== 'string') {
    return ''
  }

  // Sanitize using DOMPurify with strict configuration
  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'b', 'i', 'ul', 'ol', 'li', 'span', 'div'],
    ALLOWED_ATTR: ['class'],
    KEEP_CONTENT: true, // Keep text content even if tags are removed
    ALLOW_DATA_ATTR: false,
    ALLOW_UNKNOWN_PROTOCOLS: false,
  })
}
