import { useState } from 'react'
import { Heart, Settings, Trash2, X, Home, ExternalLink } from 'lucide-react'
import { IconButton, Link, Tooltip, Divider } from '../index'

/**
 * Navigation & Layout Atoms Demo
 * Batch 3: IconButton, Link, Tooltip, Divider
 */

export const NavLayoutDemo = () => {
  const [likeCount, setLikeCount] = useState(0)

  return (
    <div style={{ padding: '40px', maxWidth: '900px', margin: '0 auto' }}>
      <h1>Navigation & Layout Atoms - Batch 3</h1>

      <Divider spacing="lg" />

      {/* IconButton Demo */}
      <section>
        <h2>IconButton Component</h2>
        <p>Icon-only buttons for toolbars and actions</p>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '16px' }}>
          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Variants
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <IconButton
                icon={<Heart />}
                variant="default"
                aria-label="Like (default)"
                onClick={() => setLikeCount(likeCount + 1)}
              />
              <IconButton
                icon={<Heart />}
                variant="primary"
                aria-label="Like (primary)"
                onClick={() => setLikeCount(likeCount + 1)}
              />
              <IconButton
                icon={<Trash2 />}
                variant="danger"
                aria-label="Delete"
              />
              <IconButton
                icon={<X />}
                variant="ghost"
                aria-label="Close"
              />
            </div>
          </div>

          <Divider orientation="vertical" spacing="md" />

          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Sizes
            </p>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <IconButton
                icon={<Settings />}
                size="sm"
                aria-label="Settings (small)"
              />
              <IconButton
                icon={<Settings />}
                size="md"
                aria-label="Settings (medium)"
              />
              <IconButton
                icon={<Settings />}
                size="lg"
                aria-label="Settings (large)"
              />
            </div>
          </div>

          <Divider orientation="vertical" spacing="md" />

          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Disabled
            </p>
            <IconButton
              icon={<Heart />}
              variant="primary"
              disabled
              aria-label="Like (disabled)"
            />
          </div>
        </div>

        <div style={{ marginTop: '16px', padding: '12px', background: 'var(--color-background-secondary)', borderRadius: '8px' }}>
          <p style={{ fontSize: '14px' }}>
            Likes: <strong>{likeCount}</strong> (click heart icons to increment)
          </p>
        </div>
      </section>

      <Divider spacing="lg" />

      {/* Link Demo */}
      <section>
        <h2>Link Component</h2>
        <p>Navigation links with hover states</p>

        <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Variants
            </p>
            <div style={{ display: 'flex', gap: '16px' }}>
              <Link href="/dashboard" variant="default">
                <Home size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Dashboard (default)
              </Link>
              <Link href="/settings" variant="primary">
                Settings (primary)
              </Link>
              <Link href="/help" variant="muted">
                Help (muted)
              </Link>
            </div>
          </div>

          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Underline Styles
            </p>
            <div style={{ display: 'flex', gap: '16px' }}>
              <Link href="#" underline="always">
                Always underlined
              </Link>
              <Link href="#" underline="hover">
                Hover underline
              </Link>
              <Link href="#" underline="none">
                No underline
              </Link>
            </div>
          </div>

          <div>
            <p style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              External & Disabled
            </p>
            <div style={{ display: 'flex', gap: '16px' }}>
              <Link href="https://github.com" external variant="primary">
                <ExternalLink size={16} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                GitHub (opens in new tab)
              </Link>
              <Link href="/disabled" disabled>
                Disabled link
              </Link>
            </div>
          </div>
        </div>
      </section>

      <Divider spacing="lg" />

      {/* Tooltip Demo */}
      <section>
        <h2>Tooltip Component</h2>
        <p>Contextual help on hover, click, or focus</p>

        <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Placement Options
            </p>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <Tooltip content="Top tooltip (hover me)" placement="top">
                <button style={{ padding: '8px 16px' }}>Top</button>
              </Tooltip>
              <Tooltip content="Bottom tooltip" placement="bottom">
                <button style={{ padding: '8px 16px' }}>Bottom</button>
              </Tooltip>
              <Tooltip content="Left tooltip" placement="left">
                <button style={{ padding: '8px 16px' }}>Left</button>
              </Tooltip>
              <Tooltip content="Right tooltip" placement="right">
                <button style={{ padding: '8px 16px' }}>Right</button>
              </Tooltip>
            </div>
          </div>

          <div>
            <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Trigger Types
            </p>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <Tooltip content="Hover to see this tooltip (300ms delay)" trigger="hover">
                <button style={{ padding: '8px 16px' }}>Hover</button>
              </Tooltip>
              <Tooltip content="Click to toggle tooltip" trigger="click">
                <button style={{ padding: '8px 16px' }}>Click</button>
              </Tooltip>
              <Tooltip content="Focus to see tooltip" trigger="focus">
                <button style={{ padding: '8px 16px' }}>Focus</button>
              </Tooltip>
            </div>
          </div>

          <div>
            <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              Custom Delay
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <Tooltip content="Instant tooltip" delay={0}>
                <button style={{ padding: '8px 16px' }}>No Delay</button>
              </Tooltip>
              <Tooltip content="Appears after 1 second" delay={1000}>
                <button style={{ padding: '8px 16px' }}>1s Delay</button>
              </Tooltip>
            </div>
          </div>

          <div>
            <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
              With Icon Buttons
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <Tooltip content="Add to favorites">
                <IconButton icon={<Heart />} variant="ghost" aria-label="Favorite" />
              </Tooltip>
              <Tooltip content="Settings">
                <IconButton icon={<Settings />} variant="ghost" aria-label="Settings" />
              </Tooltip>
              <Tooltip content="Delete permanently" placement="bottom">
                <IconButton icon={<Trash2 />} variant="danger" aria-label="Delete" />
              </Tooltip>
            </div>
          </div>
        </div>
      </section>

      <Divider spacing="lg" />

      {/* Divider Demo */}
      <section>
        <h2>Divider Component</h2>
        <p>Visual separators for content</p>

        <div style={{ marginTop: '16px' }}>
          <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Horizontal Variants
          </p>
          <div>
            <p>Solid divider</p>
            <Divider variant="solid" />
            <p>Dashed divider</p>
            <Divider variant="dashed" />
            <p>Dotted divider</p>
            <Divider variant="dotted" />
          </div>

          <Divider spacing="lg" />

          <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Spacing Options
          </p>
          <div>
            <p>Small spacing</p>
            <Divider spacing="sm" />
            <p>Medium spacing (default)</p>
            <Divider spacing="md" />
            <p>Large spacing</p>
            <Divider spacing="lg" />
            <p>End of spacing demo</p>
          </div>

          <Divider spacing="lg" />

          <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Thickness Options
          </p>
          <div>
            <p>Thin</p>
            <Divider thickness="thin" />
            <p>Medium (default)</p>
            <Divider thickness="medium" />
            <p>Thick</p>
            <Divider thickness="thick" />
          </div>

          <Divider spacing="lg" />

          <p style={{ marginBottom: '12px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Vertical Dividers
          </p>
          <div style={{ display: 'flex', alignItems: 'center', height: '60px' }}>
            <span>Section 1</span>
            <Divider orientation="vertical" />
            <span>Section 2</span>
            <Divider orientation="vertical" variant="dashed" />
            <span>Section 3</span>
            <Divider orientation="vertical" variant="dotted" />
            <span>Section 4</span>
          </div>
        </div>
      </section>

      <Divider spacing="lg" />

      {/* Combined Example */}
      <section>
        <h2>Combined Example</h2>
        <p>Navigation & Layout atoms working together</p>

        <div
          style={{
            marginTop: '16px',
            padding: '16px',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
          }}
        >
          {/* Toolbar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <Link href="/" variant="primary" underline="none">
                <Home size={20} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                Home
              </Link>
              <Link href="/about">About</Link>
              <Link href="/contact">Contact</Link>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Tooltip content="Favorite this page">
                <IconButton icon={<Heart />} variant="ghost" aria-label="Favorite" />
              </Tooltip>
              <Tooltip content="Settings">
                <IconButton icon={<Settings />} variant="ghost" aria-label="Settings" />
              </Tooltip>
            </div>
          </div>

          <Divider spacing="md" />

          {/* Content */}
          <div>
            <h3>Product Card</h3>
            <p>This is an example of using navigation and layout atoms together.</p>

            <Divider spacing="sm" variant="dashed" />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Tooltip content="Like this product">
                  <IconButton
                    icon={<Heart />}
                    variant="primary"
                    aria-label="Like"
                    onClick={() => setLikeCount(likeCount + 1)}
                  />
                </Tooltip>
                <Tooltip content="Delete this product" placement="bottom">
                  <IconButton icon={<Trash2 />} variant="danger" aria-label="Delete" />
                </Tooltip>
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <Link href="#" variant="primary">
                  View Details
                </Link>
                <Link href="#" variant="muted">
                  Learn More
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
