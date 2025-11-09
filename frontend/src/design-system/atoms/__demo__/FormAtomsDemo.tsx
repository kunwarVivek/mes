import { useState } from 'react'
import { Switch, Radio, Checkbox, Textarea } from '../index'

/**
 * Demo page for Form Atoms (Batch 2)
 * Shows all form components with interactive examples
 */

export const FormAtomsDemo = () => {
  // Switch states
  const [notifications, setNotifications] = useState(false)
  const [darkMode, setDarkMode] = useState(true)

  // Radio states
  const [size, setSize] = useState('medium')
  const [color, setColor] = useState('blue')

  // Checkbox states
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [newsletter, setNewsletter] = useState(false)
  const [allSelected, setAllSelected] = useState(false)
  const [indeterminate, setIndeterminate] = useState(true)

  // Textarea states
  const [comment, setComment] = useState('')
  const [description, setDescription] = useState('This is a sample description with some initial text.')
  const [feedback, setFeedback] = useState('')

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Form Atoms - Batch 2 Demo</h1>

      {/* Switch Examples */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>Switch Component</h2>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Sizes</h3>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <Switch
              checked={notifications}
              onChange={setNotifications}
              label="Small"
              size="sm"
            />
            <Switch
              checked={notifications}
              onChange={setNotifications}
              label="Medium (default)"
              size="md"
            />
            <Switch
              checked={darkMode}
              onChange={setDarkMode}
              label="Large"
              size="lg"
            />
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>States</h3>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <Switch
              checked={true}
              onChange={() => {}}
              label="Checked"
            />
            <Switch
              checked={false}
              onChange={() => {}}
              label="Unchecked"
            />
            <Switch
              checked={true}
              onChange={() => {}}
              label="Disabled"
              disabled
            />
          </div>
        </div>
      </section>

      {/* Radio Examples */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>Radio Component</h2>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Size Selection</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Radio
              value="small"
              checked={size === 'small'}
              onChange={setSize}
              name="size"
              label="Small"
              size="sm"
            />
            <Radio
              value="medium"
              checked={size === 'medium'}
              onChange={setSize}
              name="size"
              label="Medium"
              size="md"
            />
            <Radio
              value="large"
              checked={size === 'large'}
              onChange={setSize}
              name="size"
              label="Large"
              size="lg"
            />
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Color Selection (with disabled option)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Radio
              value="blue"
              checked={color === 'blue'}
              onChange={setColor}
              name="color"
              label="Blue"
            />
            <Radio
              value="red"
              checked={color === 'red'}
              onChange={setColor}
              name="color"
              label="Red"
            />
            <Radio
              value="green"
              checked={color === 'green'}
              onChange={setColor}
              name="color"
              label="Green (disabled)"
              disabled
            />
          </div>
        </div>
      </section>

      {/* Checkbox Examples */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>Checkbox Component</h2>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Basic Checkboxes</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <Checkbox
              checked={termsAccepted}
              onChange={setTermsAccepted}
              label="I accept the terms and conditions"
            />
            <Checkbox
              checked={newsletter}
              onChange={setNewsletter}
              label="Subscribe to newsletter"
            />
            <Checkbox
              checked={true}
              onChange={() => {}}
              label="Disabled checked"
              disabled
            />
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Indeterminate State</h3>
          <Checkbox
            checked={allSelected}
            onChange={(checked) => {
              setAllSelected(checked)
              setIndeterminate(false)
            }}
            indeterminate={indeterminate}
            label="Select all items"
          />
          <div style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
            <small>Indeterminate state shown when only some items are selected</small>
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Sizes</h3>
          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <Checkbox
              checked={true}
              onChange={() => {}}
              label="Small"
              size="sm"
            />
            <Checkbox
              checked={true}
              onChange={() => {}}
              label="Medium"
              size="md"
            />
            <Checkbox
              checked={true}
              onChange={() => {}}
              label="Large"
              size="lg"
            />
          </div>
        </div>
      </section>

      {/* Textarea Examples */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>Textarea Component</h2>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Basic Textarea</h3>
          <Textarea
            value={comment}
            onChange={setComment}
            placeholder="Enter your comment..."
            rows={4}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>With Character Counter</h3>
          <Textarea
            value={feedback}
            onChange={setFeedback}
            placeholder="Your feedback (max 200 characters)..."
            maxLength={200}
            rows={5}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Resize Options</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <p><strong>No Resize:</strong></p>
              <Textarea
                value={description}
                onChange={setDescription}
                resize="none"
                rows={3}
              />
            </div>
            <div>
              <p><strong>Vertical Only (default):</strong></p>
              <Textarea
                value={description}
                onChange={setDescription}
                resize="vertical"
                rows={3}
              />
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>States</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <p><strong>Error State:</strong></p>
              <Textarea
                value="Invalid input"
                onChange={() => {}}
                error
                rows={2}
              />
            </div>
            <div>
              <p><strong>Disabled:</strong></p>
              <Textarea
                value="Cannot edit this"
                onChange={() => {}}
                disabled
                rows={2}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Current State Display */}
      <section style={{
        marginTop: '3rem',
        padding: '1rem',
        backgroundColor: '#f3f4f6',
        borderRadius: '0.5rem'
      }}>
        <h3>Current State</h3>
        <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
{JSON.stringify({
  switches: { notifications, darkMode },
  radios: { size, color },
  checkboxes: { termsAccepted, newsletter, allSelected, indeterminate },
  textareas: {
    comment: comment.substring(0, 50) + (comment.length > 50 ? '...' : ''),
    feedback: feedback.substring(0, 50) + (feedback.length > 50 ? '...' : ''),
  }
}, null, 2)}
        </pre>
      </section>
    </div>
  )
}

export default FormAtomsDemo
