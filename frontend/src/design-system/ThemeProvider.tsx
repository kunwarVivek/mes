/**
 * ThemeProvider Component
 * Provides theme context and manages theme switching with localStorage persistence
 */

import { createContext, useState, useEffect, ReactNode } from 'react'
import { ThemeConfig, ThemeMode, getThemeConfig } from './theme'

interface ThemeContextValue {
  theme: ThemeConfig
  setTheme: (mode: ThemeMode) => void
  colorScheme: ThemeMode
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
  defaultTheme?: ThemeMode
}

export function ThemeProvider({ children, defaultTheme = 'blue' }: ThemeProviderProps) {
  const [colorScheme, setColorScheme] = useState<ThemeMode>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem('theme') as ThemeMode | null
    return stored || defaultTheme
  })

  const [theme, setThemeConfig] = useState<ThemeConfig>(() => getThemeConfig(colorScheme))

  useEffect(() => {
    // Persist to localStorage when theme changes
    localStorage.setItem('theme', colorScheme)
    setThemeConfig(getThemeConfig(colorScheme))
  }, [colorScheme])

  const setTheme = (mode: ThemeMode) => {
    setColorScheme(mode)
  }

  const value: ThemeContextValue = {
    theme,
    setTheme,
    colorScheme,
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
