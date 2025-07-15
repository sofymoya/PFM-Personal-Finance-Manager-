import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'
import { MemoryRouter } from 'react-router-dom'
import { act } from 'react-dom/test-utils'

// Mock de authApi
vi.mock('../auth/authApi', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
  },
}))

describe('App', () => {
  beforeEach(() => {
    // Limpiar localStorage antes de cada test
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should render login page when user is not authenticated', () => {
    render(<App />)
    
    // Debería mostrar la página de login
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument()
  })

  it('should render dashboard when user is authenticated', async () => {
    // Simular token en localStorage con payload válido base64
    // {"email":"test@example.com","name":"Test User","iat":1516239022}
    const mockPayload = btoa(JSON.stringify({ email: 'test@example.com', name: 'Test User', iat: 1516239022 }))
    const mockToken = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.${mockPayload}.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`
    localStorage.setItem('token', mockToken)
    await act(async () => {
      render(
        <App routerComponent={({ children }) => <MemoryRouter initialEntries={["/dashboard"]}>{children}</MemoryRouter>} />
      )
    })
    
    // Esperar a que se renderice el dashboard (texto visible)
    expect(await screen.findByText('FinTrack')).toBeInTheDocument()
  })
}) 