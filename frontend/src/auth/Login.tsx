import React, { useState } from "react";
import { Link } from "react-router-dom";

interface LoginProps {
  onLogin: (userId: number) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        body: formData,
      });
      let data = null;
      try {
        data = await response.json();
      } catch (jsonErr) {
        setError("Error: respuesta del servidor no es JSON válida.");
        setLoading(false);
        return;
      }
      if (response.ok) {
        if (data.access_token && data.user_id) {
          onLogin(data.user_id);
        } else {
          setError("Respuesta inesperada del servidor");
        }
      } else {
        setError(data.detail || `Error de login (${response.status})`);
      }
    } catch (err) {
      setError("Error de conexión");
    }
    setLoading(false);
  };

  return (
    <div className="login-container">
      <h2>Iniciar sesión</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Email:</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Contraseña:</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? "Cargando..." : "Entrar"}
        </button>
      </form>
      <div style={{ marginTop: "1rem" }}>
        ¿No tienes cuenta? <Link to="/register">Regístrate aquí</Link>
      </div>
    </div>
  );
};

export default Login; 