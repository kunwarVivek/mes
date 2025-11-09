import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthLayout } from '../../../design-system/templates/AuthLayout'
import { Input } from '../../../design-system/atoms/Input'
import { Button } from '../../../design-system/atoms/Button'
import { useAuth, RegisterFormData } from '../hooks/useAuth'
import './RegisterPage.css'

/**
 * RegisterPage Component
 *
 * Registration form with validation:
 * - Single Responsibility: User registration
 * - Registration form with organization details
 * - Password confirmation validation
 * - Form validation
 * - Error message display
 * - Loading state during submission
 * - Redirect to login on success
 */

interface FormErrors {
  email?: string
  password?: string
  confirmPassword?: string
  organizationName?: string
  fullName?: string
  general?: string
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export const RegisterPage = () => {
  const navigate = useNavigate()
  const { register, isLoading } = useAuth()

  const [formData, setFormData] = useState<RegisterFormData>({
    email: '',
    password: '',
    confirmPassword: '',
    organizationName: '',
    fullName: '',
  })

  const [errors, setErrors] = useState<FormErrors>({})

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password'
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords must match'
    }

    // Organization name validation
    if (!formData.organizationName) {
      newErrors.organizationName = 'Organization name is required'
    }

    // Full name validation
    if (!formData.fullName) {
      newErrors.fullName = 'Full name is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    // Clear previous errors
    setErrors({})

    // Validate form
    if (!validateForm()) {
      return
    }

    try {
      await register(formData)
      // Redirect to login after successful registration
      navigate('/login')
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Registration failed',
      })
    }
  }

  return (
    <AuthLayout
      title="Register"
      subtitle="Create your account to get started."
    >
      <form onSubmit={handleSubmit} className="register-form" noValidate>
        {/* Full Name Field */}
        <div className="register-form__field">
          <label htmlFor="fullName" className="register-form__label">
            Full Name
          </label>
          <Input
            id="fullName"
            type="text"
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            error={!!errors.fullName}
            fullWidth
            placeholder="John Doe"
            disabled={isLoading}
            autoComplete="name"
          />
          {errors.fullName && (
            <span className="register-form__error">{errors.fullName}</span>
          )}
        </div>

        {/* Email Field */}
        <div className="register-form__field">
          <label htmlFor="email" className="register-form__label">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={!!errors.email}
            fullWidth
            placeholder="you@example.com"
            disabled={isLoading}
            autoComplete="email"
          />
          {errors.email && (
            <span className="register-form__error">{errors.email}</span>
          )}
        </div>

        {/* Organization Name Field */}
        <div className="register-form__field">
          <label htmlFor="organizationName" className="register-form__label">
            Organization Name
          </label>
          <Input
            id="organizationName"
            type="text"
            value={formData.organizationName}
            onChange={(e) => setFormData({ ...formData, organizationName: e.target.value })}
            error={!!errors.organizationName}
            fullWidth
            placeholder="Your Company"
            disabled={isLoading}
            autoComplete="organization"
          />
          {errors.organizationName && (
            <span className="register-form__error">{errors.organizationName}</span>
          )}
        </div>

        {/* Password Field */}
        <div className="register-form__field">
          <label htmlFor="password" className="register-form__label">
            Password
          </label>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            error={!!errors.password}
            fullWidth
            placeholder="At least 8 characters"
            disabled={isLoading}
            autoComplete="new-password"
          />
          {errors.password && (
            <span className="register-form__error">{errors.password}</span>
          )}
        </div>

        {/* Confirm Password Field */}
        <div className="register-form__field">
          <label htmlFor="confirmPassword" className="register-form__label">
            Confirm Password
          </label>
          <Input
            id="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            error={!!errors.confirmPassword}
            fullWidth
            placeholder="Re-enter your password"
            disabled={isLoading}
            autoComplete="new-password"
          />
          {errors.confirmPassword && (
            <span className="register-form__error">{errors.confirmPassword}</span>
          )}
        </div>

        {/* General Error */}
        {errors.general && (
          <div className="register-form__general-error">{errors.general}</div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          fullWidth
          isLoading={isLoading}
          disabled={isLoading}
        >
          Register
        </Button>

        {/* Login Link */}
        <div className="register-form__login">
          Already have an account?{' '}
          <a href="/login" className="register-form__login-link">
            Log In
          </a>
        </div>
      </form>
    </AuthLayout>
  )
}

RegisterPage.displayName = 'RegisterPage'
