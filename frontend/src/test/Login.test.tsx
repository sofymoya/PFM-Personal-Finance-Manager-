import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'

// Mock de authApi
vi.mock('../auth/authApi', () => ({
  authApi: {
    login: vi.fn(),
  },
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('Login', () => {
  let mockOnLogin: any

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnLogin = vi.fn().mockResolvedValue({ success: true })
  })

  it('should render login form', () => {
    renderWithRouter(<Login onLogin={mockOnLogin} />)
    expect(screen.getByPlaceholderText(/email or username/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('should call onLogin when form is submitted', async () => {
    renderWithRouter(<Login onLogin={mockOnLogin} />)
    const emailInput = screen.getByPlaceholderText(/email or username/i)
    const passwordInput = screen.getByPlaceholderText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)
    await waitFor(() => {
      expect(mockOnLogin).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('should show error message when login fails', async () => {
    mockOnLogin.mockResolvedValueOnce({ success: false, error: 'Invalid credentials' })
    renderWithRouter(<Login onLogin={mockOnLogin} />)
    const emailInput = screen.getByPlaceholderText(/email or username/i)
    const passwordInput = screen.getByPlaceholderText(/password/i)
    const submitButton = screen.getByRole('button', { name: /log in/i })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })
}) 