import { useState, FormEvent } from 'react'
import { Card, Button, Heading2 } from '../atoms'
import { FormField } from '../molecules'
import type { CreateUserDto } from '@/services/user.service'
import './UserForm.css'

/**
 * UserForm Organism
 *
 * Complete form for creating users:
 * - Composed of multiple molecules and atoms
 * - Single Responsibility: Handle user creation form
 * - Validation: Client-side validation with feedback
 */

export interface UserFormProps {
  onSubmit: (data: CreateUserDto) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const UserForm = ({ onSubmit, onCancel, isLoading, error }: UserFormProps) => {
  const [formData, setFormData] = useState<CreateUserDto>({
    email: '',
    username: '',
    password: '',
    is_active: true,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.username || formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters'
    }

    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    if (!formData.password || formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    await onSubmit(formData)
  }

  const handleChange = (field: keyof CreateUserDto) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <Card variant="elevated" padding="lg">
      <div className="user-form">
        <Heading2>Create New User</Heading2>

        <form onSubmit={handleSubmit} className="user-form__form">
          <FormField
            label="Username"
            type="text"
            value={formData.username}
            onChange={handleChange('username')}
            error={errors.username}
            required
            disabled={isLoading}
          />

          <FormField
            label="Email"
            type="email"
            value={formData.email}
            onChange={handleChange('email')}
            error={errors.email}
            required
            disabled={isLoading}
          />

          <FormField
            label="Password"
            type="password"
            value={formData.password}
            onChange={handleChange('password')}
            error={errors.password}
            helperText="Must be at least 8 characters"
            required
            disabled={isLoading}
          />

          <div className="user-form__checkbox">
            <label className="user-form__checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={handleChange('is_active')}
                disabled={isLoading}
              />
              <span>Active user</span>
            </label>
          </div>

          {error && (
            <div className="user-form__error" role="alert">
              {error}
            </div>
          )}

          <div className="user-form__actions">
            <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
              Create User
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="ghost"
                onClick={onCancel}
                disabled={isLoading}
                fullWidth
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </div>
    </Card>
  )
}
