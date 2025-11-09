import '@testing-library/jest-dom'
import DOMPurify from 'dompurify'

// Initialize DOMPurify with jsdom window
if (typeof window !== 'undefined') {
  DOMPurify.sanitize('<div>test</div>')
}

// Mock localStorage with actual storage
class LocalStorageMock {
  private store: Record<string, string> = {}

  getItem(key: string): string | null {
    return this.store[key] || null
  }

  setItem(key: string, value: string): void {
    this.store[key] = value
  }

  removeItem(key: string): void {
    delete this.store[key]
  }

  clear(): void {
    this.store = {}
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).localStorage = new LocalStorageMock()

// Mock ResizeObserver for Recharts
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).ResizeObserver = ResizeObserverMock

// Mock hasPointerCapture and scrollIntoView for Radix UI components
// eslint-disable-next-line @typescript-eslint/no-explicit-any
if (typeof Element !== 'undefined') {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(Element.prototype as any).hasPointerCapture) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (Element.prototype as any).hasPointerCapture = function () {
        return false
      }
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(Element.prototype as any).setPointerCapture) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (Element.prototype as any).setPointerCapture = function () {}
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(Element.prototype as any).releasePointerCapture) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (Element.prototype as any).releasePointerCapture = function () {}
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(Element.prototype as any).scrollIntoView) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (Element.prototype as any).scrollIntoView = function () {}
    }
  } catch (e) {
    // Ignore if we can't set these properties
  }
}
