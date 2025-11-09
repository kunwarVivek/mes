/**
 * ThemeSystem Integration Tests
 * Verifies integration with existing app structure
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider, useTheme } from '../index'

// Test Component that uses theme
function TestAppComponent() {
  const { theme, colorScheme } = useTheme()
  
  return (
    <div>
      <h1 style={{ color: theme.colors.primary[600] }}>Test App</h1>
      <p>Current theme: {colorScheme}</p>
      <div style={{ background: theme.colors.surface, padding: theme.spacing.md }}>
        Content
      </div>
    </div>
  )
}

describe('ThemeSystem Integration', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('integrates with app wrapper without errors', () => {
    const { container } = render(
      <ThemeProvider>
        <TestAppComponent />
      </ThemeProvider>
    )
    
    expect(container).toBeTruthy()
    expect(screen.getByText('Test App')).toBeTruthy()
  })

  it('provides theme values to components', () => {
    render(
      <ThemeProvider>
        <TestAppComponent />
      </ThemeProvider>
    )
    
    expect(screen.getByText('Current theme: blue')).toBeTruthy()
  })

  it('applies default blue theme', () => {
    render(
      <ThemeProvider>
        <TestAppComponent />
      </ThemeProvider>
    )
    
    const heading = screen.getByText('Test App')
    expect(heading).toBeTruthy()
    // Default theme is blue, primary[600] = '#0284c7'
    expect(heading.style.color).toBe('rgb(2, 132, 199)')
  })

  it('allows theme customization via props', () => {
    render(
      <ThemeProvider defaultTheme="purple">
        <TestAppComponent />
      </ThemeProvider>
    )
    
    expect(screen.getByText('Current theme: purple')).toBeTruthy()
  })

  it('exports all necessary types and functions', () => {
    // This test verifies the public API is accessible
    expect(ThemeProvider).toBeDefined()
    expect(useTheme).toBeDefined()
  })
})

describe('Import Resolution', () => {
  it('can import from design-system/index.ts', async () => {
    const module = await import('../index')
    
    expect(module.ThemeProvider).toBeDefined()
    expect(module.useTheme).toBeDefined()
    expect(module.theme).toBeDefined()
    expect(module.getThemeConfig).toBeDefined()
  })
})
