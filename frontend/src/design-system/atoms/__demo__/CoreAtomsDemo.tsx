/**
 * Core Atoms Batch 1 Demo
 * Visual demonstration of Badge, Chip, Spinner, Skeleton, and Progress components
 */

import { useState } from 'react'
import { Badge, Chip, Spinner, Skeleton, Progress } from '../index'
import { ThemeProvider } from '../../ThemeProvider'

export function CoreAtomsDemo() {
  const [chips, setChips] = useState(['React', 'TypeScript', 'Vitest'])
  const [progress, setProgress] = useState(65)

  const removeChip = (index: number) => {
    setChips(chips.filter((_, i) => i !== index))
  }

  return (
    <ThemeProvider>
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>Core Atoms - Status & Indicators</h1>

        {/* Badge Examples */}
        <section style={{ marginBottom: '3rem' }}>
          <h2>Badge Component</h2>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <Badge variant="success">Passed</Badge>
            <Badge variant="warning">Pending</Badge>
            <Badge variant="error">Failed</Badge>
            <Badge variant="info">Info</Badge>
            <Badge variant="neutral">Neutral</Badge>
          </div>

          <h3>With Dot Indicator</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <Badge variant="success" dot>Running</Badge>
            <Badge variant="warning" dot>Idle</Badge>
            <Badge variant="error" dot>Down</Badge>
          </div>

          <h3>Sizes</h3>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <Badge variant="info" size="sm">Small</Badge>
            <Badge variant="info" size="md">Medium</Badge>
            <Badge variant="info" size="lg">Large</Badge>
          </div>
        </section>

        {/* Chip Examples */}
        <section style={{ marginBottom: '3rem' }}>
          <h2>Chip Component</h2>
          <h3>Removable Tags</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            {chips.map((chip, index) => (
              <Chip
                key={chip}
                label={chip}
                onDelete={() => removeChip(index)}
              />
            ))}
          </div>

          <h3>Variants</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <Chip label="Filled" variant="filled" />
            <Chip label="Outlined" variant="outlined" />
          </div>

          <h3>With Icons</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Chip label="Priority High" icon={<span>⚠️</span>} />
            <Chip label="Completed" icon={<span>✓</span>} />
          </div>
        </section>

        {/* Spinner Examples */}
        <section style={{ marginBottom: '3rem' }}>
          <h2>Spinner Component</h2>
          <h3>Sizes</h3>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', marginBottom: '1rem' }}>
            <Spinner size="sm" />
            <Spinner size="md" />
            <Spinner size="lg" />
            <Spinner size="xl" />
          </div>

          <h3>Colors</h3>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <Spinner color="primary" />
            <Spinner color="secondary" />
            <Spinner color="neutral" />
          </div>
        </section>

        {/* Skeleton Examples */}
        <section style={{ marginBottom: '3rem' }}>
          <h2>Skeleton Component</h2>
          <h3>Text Variant</h3>
          <div style={{ marginBottom: '1rem' }}>
            <Skeleton variant="text" width="100%" />
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
          </div>

          <h3>Shapes</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <Skeleton variant="circular" width={80} height={80} />
            <Skeleton variant="rectangular" width={200} height={120} />
          </div>

          <h3>Animations</h3>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <p>Pulse</p>
              <Skeleton animation="pulse" width="100%" height={40} />
            </div>
            <div style={{ flex: 1 }}>
              <p>Wave</p>
              <Skeleton animation="wave" width="100%" height={40} />
            </div>
          </div>
        </section>

        {/* Progress Examples */}
        <section style={{ marginBottom: '3rem' }}>
          <h2>Progress Component</h2>
          <div style={{ marginBottom: '2rem' }}>
            <h3>Interactive Progress</h3>
            <Progress value={progress} showLabel />
            <div style={{ marginTop: '1rem' }}>
              <button onClick={() => setProgress(Math.max(0, progress - 10))}>-10</button>
              <button onClick={() => setProgress(Math.min(100, progress + 10))} style={{ marginLeft: '0.5rem' }}>+10</button>
            </div>
          </div>

          <h3>Variants</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
            <Progress value={75} variant="default" showLabel />
            <Progress value={100} variant="success" showLabel />
            <Progress value={50} variant="warning" showLabel />
            <Progress value={25} variant="error" showLabel />
          </div>

          <h3>Sizes</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Progress value={60} size="sm" />
            <Progress value={60} size="md" />
            <Progress value={60} size="lg" />
          </div>
        </section>
      </div>
    </ThemeProvider>
  )
}
