import { RouterProvider } from '@tanstack/react-router'
import { router } from './router'
import './App.css'

/**
 * Main Application Component
 *
 * Following SOLID principles:
 * - Single Responsibility: App composition with routing
 * - Open/Closed: Extensible through routing
 * - Uses TanStack Router for type-safe navigation
 */

function App() {
  return <RouterProvider router={router} />
}

export default App
