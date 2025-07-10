import React, { useState } from "react";

interface RegisterProps {
  onRegister: (userId: number) => void;
}

const Register: React.FC<RegisterProps> = ({ onRegister }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://localhost:8000/usuarios/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
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
        if (data.id) {
          onRegister(data.id);
        } else {
          setError("Respuesta inesperada del servidor");
        }
      } else {
        setError(data.detail || `Error de registro (${response.status})`);
      }
    } catch (err) {
      setError("Error de conexión");
    }
    setLoading(false);
  };

  return (
    <div className="register-container">
      <h2>Registrarse</h2>
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
          {loading ? "Cargando..." : "Registrarse"}
        </button>
      </form>
    </div>
  );
};

export default Register; 