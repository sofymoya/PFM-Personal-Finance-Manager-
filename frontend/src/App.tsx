import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import UploadPDF from './pages/UploadPDF';

function LandingPage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f3f4f6', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '2rem', 
        borderRadius: '0.5rem', 
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        textAlign: 'center'
      }}>
        <h1 style={{ 
          fontSize: '2rem', 
          fontWeight: 'bold', 
          color: '#111827', 
          marginBottom: '1rem' 
        }}>
          🎉 ¡Funciona!
        </h1>
        <p style={{ color: '#6b7280', marginBottom: '2rem', fontSize: '1.1rem' }}>
          El frontend está funcionando correctamente
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button 
            onClick={() => alert('¡Botón funcionando!')}
            style={{ 
              backgroundColor: '#2563eb', 
              color: 'white', 
              padding: '0.75rem 1.5rem', 
              borderRadius: '0.25rem', 
              border: 'none',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            Probar Botón
          </button>
          <Link 
            to="/register" 
            style={{ 
              backgroundColor: '#16a34a', 
              color: 'white', 
              padding: '0.75rem 1.5rem', 
              borderRadius: '0.25rem', 
              border: 'none',
              cursor: 'pointer',
              textDecoration: 'none',
              fontSize: '1rem',
              display: 'block'
            }}
          >
            Ir a Registro
          </Link>
          <Link 
            to="/login" 
            style={{ 
              backgroundColor: '#dc2626', 
              color: 'white', 
              padding: '0.75rem 1.5rem', 
              borderRadius: '0.25rem', 
              border: 'none',
              cursor: 'pointer',
              textDecoration: 'none',
              fontSize: '1rem',
              display: 'block'
            }}
          >
            Ir a Login
          </Link>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <nav className="p-4 bg-gray-100 flex gap-4">
        <Link to="/" className="text-blue-600 hover:underline">Inicio</Link>
        <Link to="/register" className="text-blue-600 hover:underline">Registro</Link>
        <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
        <Link to="/dashboard" className="text-blue-600 hover:underline">Dashboard</Link>
        <Link to="/upload" className="text-blue-600 hover:underline">Subir PDF</Link>
      </nav>
      <div className="App">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<UploadPDF />} />
          <Route path="/" element={<LandingPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;