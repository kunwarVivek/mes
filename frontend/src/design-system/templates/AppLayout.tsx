import { ReactNode, useState } from 'react'
import { Sidebar } from './Sidebar'
import { Navbar } from './Navbar'
import { Navigation } from '../../components/Navigation'
import './AppLayout.css'

/**
 * AppLayout Template Component
 *
 * Main application layout with sidebar and navbar:
 * - Single Responsibility: Application shell layout
 * - Composition: Combines Sidebar + Navbar + Content
 * - Responsive: Sidebar becomes drawer on mobile
 * - Flexible: Supports custom sidebar and navbar
 */

export interface AppLayoutProps {
  children: ReactNode
  sidebar?: ReactNode
  navbar?: ReactNode
  className?: string
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  sidebar,
  navbar,
  className = '',
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const classes = [
    'app-layout',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes}>
      {/* Sidebar - custom or default */}
      {sidebar || (
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          variant="permanent"
        >
          <Navigation />
        </Sidebar>
      )}

      {/* Main area with navbar and content */}
      <div className="app-layout__main">
        {/* Navbar - custom or default */}
        {navbar || (
          <Navbar
            showMenuButton
            onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          />
        )}

        {/* Main content */}
        <main className="app-layout__content" role="main">
          {children}
        </main>
      </div>
    </div>
  )
}

AppLayout.displayName = 'AppLayout'
