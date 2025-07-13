import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import UploadPDF from './pages/UploadPDF';
import Transactions from './pages/Transactions';
import TestDesign from './pages/TestDesign';
import SimpleTest from './pages/SimpleTest';
import { authApi } from './auth/authApi';

interface User {
  id: number;
  username: string;
  email: string;
  name: string;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      authApi.verifyToken()
        .then((userData: any) => {
          setUser({
            id: userData.id || 1,
            username: userData.username || userData.email,
            email: userData.email,
            name: userData.name || userData.username || 'Usuario'
          });
        })
        .catch(() => {
          localStorage.removeItem('token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = async (email: string, password: string) => {
    try {
      const response: any = await authApi.login(email, password);
      if (response.token || response.access_token) {
        const token = response.token || response.access_token;
        localStorage.setItem('token', token);
        setUser({ 
          id: 1, 
          username: email, 
          email,
          name: email.split('@')[0] // Usar parte del email como nombre
        });
        return { success: true };
      }
      return { success: false, error: 'Credenciales inválidas' };
    } catch (error) {
      return { success: false, error: 'Error al iniciar sesión' };
    }
  };

  const handleRegister = async (name: string, email: string, password: string) => {
    try {
      const response: any = await authApi.register(name, email, password);
      if (response.token || response.access_token) {
        const token = response.token || response.access_token;
        localStorage.setItem('token', token);
        setUser({ id: 1, username: name, email, name });
        return { success: true };
      }
      return { success: false, error: 'Error al registrarse' };
    } catch (error) {
      return { success: false, error: 'Error al registrarse' };
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        {user ? (
          // Rutas autenticadas con Layout
          <Layout user={user} onLogout={handleLogout}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/upload" element={<UploadPDF />} />
              <Route path="/reports" element={<div className="p-6"><h1 className="text-2xl font-bold">Reportes</h1><p className="text-gray-600">Página de reportes en desarrollo...</p></div>} />
              <Route path="/test-design" element={<TestDesign />} />
              <Route path="/simple-test" element={<SimpleTest />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Layout>
        ) : (
          // Rutas públicas sin Layout
          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="/register" element={<Register onRegister={handleRegister} />} />
            <Route path="/test-design" element={<TestDesign />} />
            <Route path="/simple-test" element={<SimpleTest />} />
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        )}
      </div>
    </Router>
  );
}

export default App;