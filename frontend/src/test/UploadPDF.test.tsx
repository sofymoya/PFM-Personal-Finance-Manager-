import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { UploadBank } from '../pages/UploadPDF'

// Mock de fetch
global.fetch = vi.fn()

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('UploadBank', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock de localStorage
    localStorage.setItem('token', 'mock-token')
  })

  it('should render upload form', () => {
    renderWithRouter(<UploadBank />)
    expect(screen.getByText(/upload bank statement/i)).toBeInTheDocument()
    expect(screen.getByText(/drag and drop your pdf here/i)).toBeInTheDocument()
  })

  it('should show error for invalid file type', async () => {
    renderWithRouter(<UploadBank />)
    // Buscar el input por id
    const fileInput = document.getElementById('file-input') as HTMLInputElement
    const invalidFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
    fireEvent.change(fileInput, { target: { files: [invalidFile] } })
    await waitFor(() => {
      expect(screen.getByText(/solo se permiten archivos pdf/i)).toBeInTheDocument()
    })
  })

  it('should show success message after successful upload', async () => {
    const mockResponse = {
      transacciones_guardadas: [
        {
          id: 1,
          description: 'Test Transaction',
          amount: 100.0,
          date: '2025-01-01',
          category: 'Test'
        }
      ]
    }
    ;(fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })
    renderWithRouter(<UploadBank />)
    const fileInput = document.getElementById('file-input') as HTMLInputElement
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [pdfFile] } })
    // Simular click en el botón de upload
    const uploadButton = screen.getByText(/process pdf/i)
    fireEvent.click(uploadButton)
    await waitFor(() => {
      expect(screen.getByText((content) => content.includes('PDF procesado exitosamente'))).toBeInTheDocument()
    })
  })

  it('should show error message on upload failure', async () => {
    ;(fetch as any).mockRejectedValueOnce(new Error('Upload failed'))
    renderWithRouter(<UploadBank />)
    const fileInput = document.getElementById('file-input') as HTMLInputElement
    const pdfFile = new File(['pdf content'], 'test.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [pdfFile] } })
    const uploadButton = screen.getByText(/process pdf/i)
    fireEvent.click(uploadButton)
    await waitFor(() => {
      expect(screen.getByText((content) => content.includes('Error de conexión'))).toBeInTheDocument()
    })
  })
}) 