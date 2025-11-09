import { render, screen, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Avatar } from '../Avatar'
import { Image } from '../Image'

describe('Avatar Component', () => {
  describe('Basic Rendering', () => {
    it('should render with image when src is provided', () => {
      render(<Avatar src="https://example.com/avatar.jpg" alt="User Avatar" />)
      const img = screen.getByRole('img')
      expect(img).toBeInTheDocument()
      expect(img).toHaveAttribute('src', 'https://example.com/avatar.jpg')
      expect(img).toHaveAttribute('alt', 'User Avatar')
    })

    it('should render fallback when src is not provided', () => {
      render(<Avatar alt="John Doe" fallback={<span>JD</span>} />)
      expect(screen.getByText('JD')).toBeInTheDocument()
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })

    it('should render first letter of alt as default fallback', () => {
      render(<Avatar alt="John Doe" />)
      expect(screen.getByText('J')).toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('should apply xs size class', () => {
      const { container } = render(<Avatar alt="User" size="xs" />)
      expect(container.querySelector('.avatar--xs')).toBeInTheDocument()
    })

    it('should apply sm size class', () => {
      const { container } = render(<Avatar alt="User" size="sm" />)
      expect(container.querySelector('.avatar--sm')).toBeInTheDocument()
    })

    it('should apply md size class by default', () => {
      const { container } = render(<Avatar alt="User" />)
      expect(container.querySelector('.avatar--md')).toBeInTheDocument()
    })

    it('should apply lg size class', () => {
      const { container } = render(<Avatar alt="User" size="lg" />)
      expect(container.querySelector('.avatar--lg')).toBeInTheDocument()
    })

    it('should apply xl size class', () => {
      const { container } = render(<Avatar alt="User" size="xl" />)
      expect(container.querySelector('.avatar--xl')).toBeInTheDocument()
    })
  })

  describe('Shapes', () => {
    it('should apply circle shape by default', () => {
      const { container } = render(<Avatar alt="User" />)
      expect(container.querySelector('.avatar--circle')).toBeInTheDocument()
    })

    it('should apply square shape class', () => {
      const { container } = render(<Avatar alt="User" shape="square" />)
      expect(container.querySelector('.avatar--square')).toBeInTheDocument()
    })
  })

  describe('Status Indicator', () => {
    it('should render online status indicator', () => {
      const { container } = render(<Avatar alt="User" status="online" />)
      expect(container.querySelector('.avatar__status--online')).toBeInTheDocument()
    })

    it('should render offline status indicator', () => {
      const { container } = render(<Avatar alt="User" status="offline" />)
      expect(container.querySelector('.avatar__status--offline')).toBeInTheDocument()
    })

    it('should render away status indicator', () => {
      const { container } = render(<Avatar alt="User" status="away" />)
      expect(container.querySelector('.avatar__status--away')).toBeInTheDocument()
    })

    it('should render busy status indicator', () => {
      const { container } = render(<Avatar alt="User" status="busy" />)
      expect(container.querySelector('.avatar__status--busy')).toBeInTheDocument()
    })

    it('should not render status indicator when status is undefined', () => {
      const { container } = render(<Avatar alt="User" />)
      expect(container.querySelector('[class*="avatar__status"]')).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should show fallback when image fails to load', async () => {
      render(
        <Avatar
          src="https://example.com/broken.jpg"
          alt="User"
          fallback={<span>Fallback Content</span>}
        />
      )

      const img = screen.getByRole('img')

      // Simulate image load error
      await act(async () => {
        img.dispatchEvent(new Event('error'))
      })

      await waitFor(() => {
        expect(screen.getByText('Fallback Content')).toBeInTheDocument()
      })
    })

    it('should show first letter when image fails and no fallback provided', async () => {
      render(<Avatar src="https://example.com/broken.jpg" alt="John Doe" />)

      const img = screen.getByRole('img')
      await act(async () => {
        img.dispatchEvent(new Event('error'))
      })

      await waitFor(() => {
        expect(screen.getByText('J')).toBeInTheDocument()
      })
    })
  })

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(<Avatar alt="User" className="custom-class" />)
      expect(container.querySelector('.custom-class')).toBeInTheDocument()
    })
  })
})

describe('Image Component', () => {
  describe('Basic Rendering', () => {
    it('should render image with src and alt', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test Image" />)
      const img = screen.getByAltText('Test Image')
      expect(img).toBeInTheDocument()
      expect(img).toHaveAttribute('src', 'https://example.com/image.jpg')
    })

    it('should apply lazy loading by default', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test Image" />)
      const img = screen.getByAltText('Test Image')
      expect(img).toHaveAttribute('loading', 'lazy')
    })

    it('should apply eager loading when specified', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test Image" loading="eager" />)
      const img = screen.getByAltText('Test Image')
      expect(img).toHaveAttribute('loading', 'eager')
    })
  })

  describe('Dimensions', () => {
    it('should apply width as number', () => {
      const { container } = render(
        <Image src="https://example.com/image.jpg" alt="Test" width={300} />
      )
      const wrapper = container.querySelector('.image')
      expect(wrapper).toHaveStyle({ width: '300px' })
    })

    it('should apply width as string', () => {
      const { container } = render(
        <Image src="https://example.com/image.jpg" alt="Test" width="50%" />
      )
      const wrapper = container.querySelector('.image')
      expect(wrapper).toHaveStyle({ width: '50%' })
    })

    it('should apply height as number', () => {
      const { container } = render(
        <Image src="https://example.com/image.jpg" alt="Test" height={200} />
      )
      const wrapper = container.querySelector('.image')
      expect(wrapper).toHaveStyle({ height: '200px' })
    })
  })

  describe('Object Fit', () => {
    it('should apply cover object-fit', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test" objectFit="cover" />)
      const img = screen.getByAltText('Test')
      expect(img).toHaveClass('image__img--cover')
    })

    it('should apply contain object-fit', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test" objectFit="contain" />)
      const img = screen.getByAltText('Test')
      expect(img).toHaveClass('image__img--contain')
    })

    it('should apply fill object-fit', () => {
      render(<Image src="https://example.com/image.jpg" alt="Test" objectFit="fill" />)
      const img = screen.getByAltText('Test')
      expect(img).toHaveClass('image__img--fill')
    })
  })

  describe('Loading States', () => {
    it('should show loading skeleton initially', () => {
      const { container } = render(<Image src="https://example.com/image.jpg" alt="Test" />)
      expect(container.querySelector('.skeleton')).toBeInTheDocument()
    })

    it('should hide skeleton after image loads', async () => {
      const { container } = render(<Image src="https://example.com/image.jpg" alt="Test" />)

      const img = screen.getByAltText('Test')
      await act(async () => {
        img.dispatchEvent(new Event('load'))
      })

      await waitFor(() => {
        expect(container.querySelector('.skeleton')).not.toBeInTheDocument()
      })
    })

    it('should call onLoad callback when image loads', async () => {
      const onLoad = vi.fn()
      render(<Image src="https://example.com/image.jpg" alt="Test" onLoad={onLoad} />)

      const img = screen.getByAltText('Test')
      await act(async () => {
        img.dispatchEvent(new Event('load'))
      })

      await waitFor(() => {
        expect(onLoad).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Error States', () => {
    it('should show fallback when image fails to load', async () => {
      render(
        <Image
          src="https://example.com/broken.jpg"
          alt="Test"
          fallback={<div>Failed to load</div>}
        />
      )

      const img = screen.getByAltText('Test')
      await act(async () => {
        img.dispatchEvent(new Event('error'))
      })

      await waitFor(() => {
        expect(screen.getByText('Failed to load')).toBeInTheDocument()
      })
    })

    it('should call onError callback when image fails', async () => {
      const onError = vi.fn()
      render(<Image src="https://example.com/broken.jpg" alt="Test" onError={onError} />)

      const img = screen.getByAltText('Test')
      await act(async () => {
        img.dispatchEvent(new Event('error'))
      })

      await waitFor(() => {
        expect(onError).toHaveBeenCalledTimes(1)
      })
    })

    it('should hide skeleton on error', async () => {
      const { container } = render(
        <Image src="https://example.com/broken.jpg" alt="Test" fallback={<div>Error</div>} />
      )

      const img = screen.getByAltText('Test')
      await act(async () => {
        img.dispatchEvent(new Event('error'))
      })

      await waitFor(() => {
        expect(container.querySelector('.skeleton')).not.toBeInTheDocument()
      })
    })
  })

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <Image src="https://example.com/image.jpg" alt="Test" className="custom-image" />
      )
      expect(container.querySelector('.custom-image')).toBeInTheDocument()
    })
  })
})
