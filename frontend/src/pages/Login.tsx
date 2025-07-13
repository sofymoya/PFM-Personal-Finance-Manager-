import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface LoginProps {
  onLogin: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const result = await onLogin(email, password);
    if (!result.success) {
      setError(result.error || 'Error al iniciar sesión');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header con logo */}
      <header className="w-full flex items-center border-b border-gray-200 h-14 px-8">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-black rounded-sm" />
          <span className="font-bold text-lg text-gray-900 select-none">FinTrack</span>
        </div>
      </header>
      {/* Formulario centrado */}
      <main className="flex-1 flex flex-col items-center justify-center">
        <div className="w-full flex justify-center">
          <form onSubmit={handleSubmit} className="w-full max-w-sm px-8 flex flex-col items-center gap-6 mt-2">
            <h1 className="text-3xl font-bold text-gray-900 mb-2 mt-2 text-center">Welcome back</h1>
            {error && (
              <div className="w-full bg-red-100 text-red-700 rounded-md px-4 py-2 text-sm text-center mb-2">{error}</div>
            )}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Email or username"
              className="w-full h-12 px-4 bg-gray-100 rounded-xl text-base text-gray-700 placeholder-gray-400 outline-none border-none"
              style={{ fontWeight: 500 }}
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Password"
              className="w-full h-12 px-4 bg-gray-100 rounded-xl text-base text-gray-700 placeholder-gray-400 outline-none border-none"
              style={{ fontWeight: 500 }}
            />
            <div className="w-full text-right text-gray-400 text-sm -mt-4 mb-2">
              Forgot password?
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-[#60a0c9] hover:bg-[#4a8bb8] text-white font-bold rounded-xl transition-colors text-base disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? 'Logging in...' : 'Log in'}
            </button>
            <div className="w-full text-center text-gray-400 text-base mt-1">
              Don't have an account?{' '}
              <Link to="/register" className="text-[#60a0c9] hover:underline font-medium">Sign up</Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default Login; 