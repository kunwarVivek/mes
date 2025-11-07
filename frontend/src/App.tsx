import { UsersPage } from './pages/UsersPage'
import './App.css'

/**
 * Main Application Component
 *
 * Following SOLID principles:
 * - Single Responsibility: App composition
 * - Open/Closed: Extensible through routing
 */

function App() {
  return (
    <div className="app">
      <UsersPage />
    </div>
  )
}

export default App
