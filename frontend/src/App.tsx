import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import UploadPDF from './pages/UploadPDF';
import TestDesign from './pages/TestDesign';
import SimpleTest from './pages/SimpleTest';
import { authApi } from './auth/authApi';

interface User {
  id?: number;
  username?: string;
  email?: string;
  name?: string;
}

interface AppProps {
  routerComponent?: typeof BrowserRouter;
}

function App({ routerComponent: RouterComponent = BrowserRouter }: AppProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // Decodificar el token JWT para obtener información básica
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({
          name: payload.name || payload.email?.split('@')[0] || 'Usuario',
          email: payload.email || 'usuario@example.com',
        });
      } catch (e) {
        localStorage.removeItem('token');
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  }, []);

  // handleLogin debe coincidir con la firma esperada por Login
  const handleLogin = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setUser(response.user);
        return { success: true };
      }
      return { success: false, error: 'Credenciales inválidas' };
    } catch (error: unknown) {
      return { success: false, error: error instanceof Error ? error.message : 'Error al iniciar sesión' };
    }
  };

  const handleRegister = async (name: string, email: string, password: string) => {
    try {
      const response = await authApi.register(name, email, password);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setUser({ id: 1, username: name, email, name });
        return { success: true };
      }
      return { success: false, error: 'Error al registrarse' };
    } catch (error: unknown) {
      return { success: false, error: error instanceof Error ? error.message : 'Error al registrarse' };
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Cargando...</div>;
  }

  return (
    <RouterComponent>
      <AppRoutes user={user} setUser={setUser} loading={loading} />
    </RouterComponent>
  );
}

function AppRoutes({ user, setUser, loading }: { user: User | null, setUser: React.Dispatch<React.SetStateAction<User | null>>, loading: boolean }) {
  const navigate = useNavigate();

  // handleLogin debe coincidir con la firma esperada por Login
  const handleLogin = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setUser(response.user);
        navigate('/dashboard');
        return { success: true };
      }
      return { success: false, error: 'Credenciales inválidas' };
    } catch (error: unknown) {
      return { success: false, error: error instanceof Error ? error.message : 'Error al iniciar sesión' };
    }
  };

  const handleRegister = async (name: string, email: string, password: string) => {
    try {
      const response = await authApi.register(name, email, password);
      if (response.token) {
        localStorage.setItem('token', response.token);
        setUser({ id: 1, username: name, email, name });
        return { success: true };
      }
      return { success: false, error: 'Error al registrarse' };
    } catch (error: unknown) {
      return { success: false, error: error instanceof Error ? error.message : 'Error al registrarse' };
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Cargando...</div>;
  }

  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/login" element={
        <ErrorBoundary fallback={<div className="text-red-500 p-8 text-center">Ocurrió un error al cargar la pantalla de login.</div>}>
          <Login onLogin={handleLogin} />
        </ErrorBoundary>
      } />
      <Route path="/register" element={<Register onRegister={handleRegister} />} />
      {/* Redirección explícita para la raíz */}
      <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />
      {/* Rutas privadas */}
      {user ? (
        <>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/upload-pdf" element={<UploadPDF />} />
          <Route path="/reports" element={<div className="p-6"><h1 className="text-2xl font-bold">Reportes</h1><p className="text-gray-600">Página de reportes en desarrollo...</p></div>} />
          <Route path="/test-design" element={<TestDesign />} />
          <Route path="/simple-test" element={<SimpleTest />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </>
      ) : (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
}

// ErrorBoundary para capturar errores de renderizado
class ErrorBoundary extends React.Component<{ fallback: ReactNode, children: ReactNode }, { hasError: boolean }> {
  constructor(props: { fallback: ReactNode, children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: unknown, errorInfo: unknown) {
    // Puedes loguear el error aquí si quieres
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export default App;