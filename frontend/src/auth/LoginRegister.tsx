import React, { useState } from 'react';
import { registerUser, loginUser } from './authApi';

interface LoginRegisterProps {
  onLoginSuccess?: (token: string) => void;
}

const LoginRegister: React.FC<LoginRegisterProps> = ({ onLoginSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [password, setPassword] = useState('');
  const [mensaje, setMensaje] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensaje('');
    if (isRegister) {
      // Registro
      try {
        await registerUser({ email, nombre, password });
        setMensaje('¡Registro exitoso! Ahora puedes iniciar sesión.');
        setIsRegister(false);
      } catch (err) {
        setMensaje('Error al registrar. ¿El email ya existe?');
      }
    } else {
      // Login real
      try {
        const result = await loginUser({ email, password });
        setMensaje('¡Login exitoso!');
        // Llamar a la función del padre para cambiar de pantalla
        if (onLoginSuccess) {
          onLoginSuccess(result.access_token);
        }
      } catch (err) {
        setMensaje('Credenciales incorrectas');
      }
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: 'auto', padding: 20 }}>
      <h2>{isRegister ? 'Registro' : 'Login'}</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Correo"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          style={{ width: '100%', marginBottom: 8 }}
        />
        {isRegister && (
          <input
            type="text"
            placeholder="Nombre"
            value={nombre}
            onChange={e => setNombre(e.target.value)}
            style={{ width: '100%', marginBottom: 8 }}
          />
        )}
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          style={{ width: '100%', marginBottom: 8 }}
        />
        <button type="submit" style={{ width: '100%', marginBottom: 8 }}>
          {isRegister ? 'Registrarse' : 'Iniciar sesión'}
        </button>
      </form>
      <button onClick={() => setIsRegister(!isRegister)} style={{ width: '100%' }}>
        {isRegister ? '¿Ya tienes cuenta? Inicia sesión' : '¿No tienes cuenta? Regístrate'}
      </button>
      {mensaje && <div style={{ marginTop: 10, color: mensaje === '¡Login exitoso!' ? 'green' : 'red' }}>{mensaje}</div>}
    </div>
  );
};

export default LoginRegister;