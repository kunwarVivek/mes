import { useState, FormEvent } from 'react'
import { useNavigate, Link } from '@tanstack/react-router'
import { AuthLayout } from '../../../design-system/templates/AuthLayout'
import { Input } from '../../../design-system/atoms/Input'
import { Button } from '../../../design-system/atoms/Button'
import { Checkbox } from '../../../design-system/atoms/Checkbox'
import { useAuth } from '../hooks/useAuth'
import './LoginPage.css'

/**
 * LoginPage Component
 *
 * Login form with validation:
 * - Single Responsibility: User login
 * - Email + password form
 * - "Remember me" checkbox
 * - Form validation
 * - Error message display
 * - Loading state during submission
 * - Redirect to dashboard on success
 */

export interface LoginFormData {
  email: string
  password: string
  rememberMe?: boolean
}

interface FormErrors {
  email?: string
  password?: string
  general?: string
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export const LoginPage = () => {
  const navigate = useNavigate()
  const { login, isLoading } = useAuth()

  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false,
  })

  const [errors, setErrors] = useState<FormErrors>({})

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
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
      await login(formData.email, formData.password)
      navigate({ to: '/' })
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Invalid credentials',
      })
    }
  }

  return (
    <AuthLayout
      title="Log In"
      subtitle="Welcome back! Please enter your credentials."
    >
      <form onSubmit={handleSubmit} className="login-form" noValidate>
        {/* Email Field */}
        <div className="login-form__field">
          <label htmlFor="email" className="login-form__label">
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
            <span className="login-form__error">{errors.email}</span>
          )}
        </div>

        {/* Password Field */}
        <div className="login-form__field">
          <label htmlFor="password" className="login-form__label">
            Password
          </label>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            error={!!errors.password}
            fullWidth
            placeholder="Enter your password"
            disabled={isLoading}
            autoComplete="current-password"
          />
          {errors.password && (
            <span className="login-form__error">{errors.password}</span>
          )}
        </div>

        {/* Remember Me & Forgot Password */}
        <div className="login-form__options">
          <Checkbox
            checked={formData.rememberMe || false}
            onChange={(checked) => setFormData({ ...formData, rememberMe: checked })}
            label="Remember me"
            disabled={isLoading}
          />
          <Link to="/forgot-password" className="login-form__forgot-link">
            Forgot password?
          </Link>
        </div>

        {/* General Error */}
        {errors.general && (
          <div className="login-form__general-error">{errors.general}</div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          fullWidth
          isLoading={isLoading}
          disabled={isLoading}
        >
          Log In
        </Button>

        {/* Register Link */}
        <div className="login-form__register">
          Don't have an account?{' '}
          <Link to="/register" className="login-form__register-link">
            Register
          </Link>
        </div>
      </form>
    </AuthLayout>
  )
}

LoginPage.displayName = 'LoginPage'
