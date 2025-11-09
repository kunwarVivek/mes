/**
 * CircularOEEGauge Component Tests
 *
 * TDD: Testing circular gauge display with color coding
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CircularOEEGauge } from '../components/CircularOEEGauge'

describe('CircularOEEGauge', () => {
  describe('rendering', () => {
    it('should render gauge with value and label', () => {
      render(<CircularOEEGauge value={85.5} label="Overall OEE" />)

      expect(screen.getByText('85.5%')).toBeInTheDocument()
      expect(screen.getByText('Overall OEE')).toBeInTheDocument()
    })

    it('should render with small size', () => {
      const { container } = render(<CircularOEEGauge value={75} label="Test" size="small" />)

      const sizeDiv = container.querySelector('.w-24')
      expect(sizeDiv).toBeInTheDocument()
    })

    it('should render with medium size by default', () => {
      const { container } = render(<CircularOEEGauge value={75} label="Test" />)

      const sizeDiv = container.querySelector('.w-32')
      expect(sizeDiv).toBeInTheDocument()
    })

    it('should render with large size', () => {
      const { container } = render(<CircularOEEGauge value={75} label="Test" size="large" />)

      const sizeDiv = container.querySelector('.w-40')
      expect(sizeDiv).toBeInTheDocument()
    })
  })

  describe('color coding', () => {
    it('should show green for values >= 85%', () => {
      const { container } = render(<CircularOEEGauge value={90} label="Excellent" />)

      const valueText = container.querySelector('span.text-green-600')
      expect(valueText).toBeInTheDocument()
      expect(valueText?.textContent).toBe('90.0%')
    })

    it('should show green for exactly 85%', () => {
      const { container } = render(<CircularOEEGauge value={85} label="World Class" />)

      const valueText = container.querySelector('span.text-green-600')
      expect(valueText).toBeInTheDocument()
    })

    it('should show yellow for values 60-84%', () => {
      const { container } = render(<CircularOEEGauge value={75} label="Good" />)

      const valueText = container.querySelector('span.text-yellow-600')
      expect(valueText).toBeInTheDocument()
      expect(valueText?.textContent).toBe('75.0%')
    })

    it('should show yellow for exactly 60%', () => {
      const { container } = render(<CircularOEEGauge value={60} label="Acceptable" />)

      const valueText = container.querySelector('span.text-yellow-600')
      expect(valueText).toBeInTheDocument()
    })

    it('should show red for values < 60%', () => {
      const { container } = render(<CircularOEEGauge value={45} label="Needs Improvement" />)

      const valueText = container.querySelector('span.text-red-600')
      expect(valueText).toBeInTheDocument()
      expect(valueText?.textContent).toBe('45.0%')
    })
  })

  describe('SVG rendering', () => {
    it('should render SVG circles', () => {
      const { container } = render(<CircularOEEGauge value={75} label="Test" />)

      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()

      const circles = container.querySelectorAll('circle')
      expect(circles).toHaveLength(2) // Background + progress circle
    })

    it('should calculate correct stroke-dashoffset for 0%', () => {
      const { container } = render(<CircularOEEGauge value={0} label="Test" />)

      const progressCircle = container.querySelectorAll('circle')[1]
      const circumference = 2 * Math.PI * 52 // Medium size radius
      const expectedOffset = circumference // 0% means full offset

      expect(progressCircle.getAttribute('stroke-dashoffset')).toBe(String(expectedOffset))
    })

    it('should calculate correct stroke-dashoffset for 100%', () => {
      const { container } = render(<CircularOEEGauge value={100} label="Test" />)

      const progressCircle = container.querySelectorAll('circle')[1]
      const expectedOffset = 0 // 100% means no offset

      expect(progressCircle.getAttribute('stroke-dashoffset')).toBe(String(expectedOffset))
    })

    it('should calculate correct stroke-dashoffset for 50%', () => {
      const { container } = render(<CircularOEEGauge value={50} label="Test" />)

      const progressCircle = container.querySelectorAll('circle')[1]
      const circumference = 2 * Math.PI * 52
      const expectedOffset = circumference / 2 // 50% means half offset

      expect(progressCircle.getAttribute('stroke-dashoffset')).toBe(String(expectedOffset))
    })
  })

  describe('value formatting', () => {
    it('should format value to 1 decimal place', () => {
      render(<CircularOEEGauge value={85.567} label="Test" />)

      expect(screen.getByText('85.6%')).toBeInTheDocument()
    })

    it('should format integer value with .0', () => {
      render(<CircularOEEGauge value={85} label="Test" />)

      expect(screen.getByText('85.0%')).toBeInTheDocument()
    })
  })
})
