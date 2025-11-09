import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

describe('PWA Manifest Configuration', () => {
  const manifestPath = join(__dirname, '../../public/manifest.json')

  it('should have a valid manifest.json file', () => {
    expect(existsSync(manifestPath)).toBe(true)
  })

  it('should have valid JSON structure', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    expect(() => JSON.parse(manifestContent)).not.toThrow()
  })

  it('should contain required PWA fields', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    // Required fields
    expect(manifest.name).toBeDefined()
    expect(manifest.short_name).toBeDefined()
    expect(manifest.start_url).toBeDefined()
    expect(manifest.display).toBeDefined()
    expect(manifest.icons).toBeDefined()
    expect(Array.isArray(manifest.icons)).toBe(true)
  })

  it('should have correct display mode', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    expect(manifest.display).toBe('standalone')
  })

  it('should have secure start_url', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    // Start URL should be root or relative path, not external URL
    expect(manifest.start_url).toBe('/')
  })

  it('should have required icon sizes', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    const iconSizes = manifest.icons.map((icon: any) => icon.sizes)
    expect(iconSizes).toContain('192x192')
    expect(iconSizes).toContain('512x512')
  })

  it('should use local icon paths (security)', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    manifest.icons.forEach((icon: any) => {
      // Icons should start with / (relative to domain root)
      expect(icon.src).toMatch(/^\//)
      // Should not be external URLs
      expect(icon.src).not.toMatch(/^https?:\/\//)
    })
  })

  it('should have theme and background colors', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    expect(manifest.theme_color).toBeDefined()
    expect(manifest.background_color).toBeDefined()
    expect(manifest.theme_color).toMatch(/^#[0-9a-fA-F]{6}$/)
    expect(manifest.background_color).toMatch(/^#[0-9a-fA-F]{6}$/)
  })

  it('should have description for app stores', () => {
    const manifestContent = readFileSync(manifestPath, 'utf-8')
    const manifest = JSON.parse(manifestContent)

    expect(manifest.description).toBeDefined()
    expect(manifest.description.length).toBeGreaterThan(0)
  })
})
