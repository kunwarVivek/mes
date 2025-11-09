/**
 * ThemeSystem Test Suite
 * Tests theme switching, persistence, and semantic colors
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { waitFor } from '@testing-library/react'
import { renderHook, act } from '@testing-library/react'
import { ThemeProvider } from '../ThemeProvider'
import { useTheme } from '../useTheme'
import { getThemeConfig } from '../theme'

describe('ThemeSystem', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Theme Configuration', () => {
    it('should provide all 5 color schemes', () => {
      const blueTheme = getThemeConfig('blue')
      const purpleTheme = getThemeConfig('purple')
      const greenTheme = getThemeConfig('green')
      const orangeTheme = getThemeConfig('orange')
      const customTheme = getThemeConfig('custom')

      expect(blueTheme.colors.primary[500]).toBeDefined()
      expect(purpleTheme.colors.primary[500]).toBeDefined()
      expect(greenTheme.colors.primary[500]).toBeDefined()
      expect(orangeTheme.colors.primary[500]).toBeDefined()
      expect(customTheme.colors.primary[500]).toBeDefined()
    })

    it('should include manufacturing semantic colors', () => {
      const theme = getThemeConfig('blue')

      // Machine status colors
      expect(theme.colors.machine.running).toBe('#10b981') // green
      expect(theme.colors.machine.idle).toBe('#f59e0b') // yellow
      expect(theme.colors.machine.down).toBe('#ef4444') // red
      expect(theme.colors.machine.maintenance).toBe('#3b82f6') // blue

      // Quality colors
      expect(theme.colors.quality.pass).toBe('#10b981')
      expect(theme.colors.quality.fail).toBe('#ef4444')
      expect(theme.colors.quality.pending).toBe('#f59e0b')
      expect(theme.colors.quality.inspection).toBe('#3b82f6')

      // Priority colors
      expect(theme.colors.priority.low).toBe('#737373')
      expect(theme.colors.priority.medium).toBe('#f59e0b')
      expect(theme.colors.priority.high).toBe('#fb923c')
      expect(theme.colors.priority.critical).toBe('#ef4444')

      // Severity colors
      expect(theme.colors.severity.minor).toBe('#3b82f6')
      expect(theme.colors.severity.moderate).toBe('#f59e0b')
      expect(theme.colors.severity.major).toBe('#fb923c')
      expect(theme.colors.severity.critical).toBe('#ef4444')
    })

    it('should have complete color palettes (50-950)', () => {
      const theme = getThemeConfig('purple')
      const scales = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950] as const

      scales.forEach((scale) => {
        expect(theme.colors.primary[scale]).toBeDefined()
        expect(theme.colors.primary[scale]).toMatch(/^#[0-9a-f]{6}$/i)
      })
    })
  })

  describe('ThemeProvider', () => {
    it('should provide default blue theme', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )

      const { result } = renderHook(() => useTheme(), { wrapper })

      expect(result.current.colorScheme).toBe('blue')
      expect(result.current.theme.colors.primary[500]).toBe('#0ea5e9')
    })

    it('should switch themes', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )

      const { result } = renderHook(() => useTheme(), { wrapper })

      act(() => {
        result.current.setTheme('purple')
      })

      expect(result.current.colorScheme).toBe('purple')
      expect(result.current.theme.colors.primary[500]).toBe('#a855f7')
    })

    it('should persist theme to localStorage', async () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )

      const { result } = renderHook(() => useTheme(), { wrapper })

      act(() => {
        result.current.setTheme('green')
      })

      await waitFor(() => {
        expect(localStorage.getItem('theme')).toBe('green')
      })
    })

    it('should load theme from localStorage on mount', () => {
      localStorage.setItem('theme', 'orange')

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )

      const { result } = renderHook(() => useTheme(), { wrapper })

      expect(result.current.colorScheme).toBe('orange')
      expect(result.current.theme.colors.primary[500]).toBe('#f97316')
    })
  })

  describe('useTheme hook', () => {
    it('should throw error when used outside ThemeProvider', () => {
      // Suppress console.error for this test
      const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        renderHook(() => useTheme())
      }).toThrow('useTheme must be used within ThemeProvider')

      spy.mockRestore()
    })

    it('should provide theme, setTheme, and colorScheme', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )

      const { result } = renderHook(() => useTheme(), { wrapper })

      expect(result.current.theme).toBeDefined()
      expect(result.current.setTheme).toBeInstanceOf(Function)
      expect(result.current.colorScheme).toBe('blue')
    })
  })

  describe('Color Scheme Variations', () => {
    it('should have distinct primary colors for each scheme', () => {
      const blue = getThemeConfig('blue').colors.primary[500]
      const purple = getThemeConfig('purple').colors.primary[500]
      const green = getThemeConfig('green').colors.primary[500]
      const orange = getThemeConfig('orange').colors.primary[500]
      const custom = getThemeConfig('custom').colors.primary[500]

      const colors = [blue, purple, green, orange, custom]
      const uniqueColors = new Set(colors)

      expect(uniqueColors.size).toBe(5) // All distinct
    })
  })
})
