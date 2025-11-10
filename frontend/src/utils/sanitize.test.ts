/**
 * Sanitization Utility Tests
 *
 * Tests for DOMPurify sanitization utility to prevent XSS attacks
 */
import { describe, it, expect } from 'vitest'
import { sanitizeHtml } from './sanitize'

describe('sanitizeHtml', () => {
  it('should remove script tags from user input', () => {
    const maliciousInput = '<script>alert("XSS")</script>Hello'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('<script>')
    expect(sanitized).not.toContain('alert')
    expect(sanitized).toContain('Hello')
  })

  it('should remove inline JavaScript event handlers', () => {
    const maliciousInput = '<div onclick="alert(\'XSS\')">Click me</div>'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('onclick')
    expect(sanitized).not.toContain('alert')
    expect(sanitized).toContain('Click me')
  })

  it('should remove javascript: protocol in links', () => {
    const maliciousInput = '<a href="javascript:alert(\'XSS\')">Click</a>'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('javascript:')
    expect(sanitized).not.toContain('alert')
  })

  it('should remove iframe tags', () => {
    const maliciousInput = '<iframe src="http://evil.com"></iframe>Normal text'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('<iframe')
    expect(sanitized).toContain('Normal text')
  })

  it('should preserve safe HTML formatting', () => {
    const safeInput = '<p>Hello <strong>World</strong></p>'
    const sanitized = sanitizeHtml(safeInput)

    expect(sanitized).toContain('<p>')
    expect(sanitized).toContain('<strong>')
    expect(sanitized).toContain('Hello')
    expect(sanitized).toContain('World')
  })

  it('should handle plain text without HTML', () => {
    const plainText = 'Just plain text'
    const sanitized = sanitizeHtml(plainText)

    expect(sanitized).toBe('Just plain text')
  })

  it('should handle empty strings', () => {
    const empty = ''
    const sanitized = sanitizeHtml(empty)

    expect(sanitized).toBe('')
  })

  it('should handle null and undefined gracefully', () => {
    expect(sanitizeHtml(null as any)).toBe('')
    expect(sanitizeHtml(undefined as any)).toBe('')
  })

  it('should remove dangerous style attributes', () => {
    const maliciousInput = '<div style="background-image: url(javascript:alert(\'XSS\'))">Text</div>'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('javascript:')
    expect(sanitized).toContain('Text')
  })

  it('should prevent data exfiltration via images', () => {
    const maliciousInput = '<img src="x" onerror="alert(\'XSS\')">'
    const sanitized = sanitizeHtml(maliciousInput)

    expect(sanitized).not.toContain('onerror')
    expect(sanitized).not.toContain('alert')
  })
})
