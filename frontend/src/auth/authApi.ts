interface User {
  name: string;
  email: string;
  avatar?: string;
}

interface AuthResponse {
  token: string;
  user: User;
}

export const authApi = {
  async register(name: string, email: string, password: string): Promise<AuthResponse> {
    const response = await fetch('http://localhost:8000/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    
    if (!response.ok) {
      throw new Error('Error al registrar');
    }
    
    const data = await response.json();
    return {
      token: data.access_token || '',
      user: {
        name: data.name || name,
        email: data.email || email
      }
    };
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const response = await fetch('http://localhost:8000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params,
    });

    if (!response.ok) {
      throw new Error('Credenciales incorrectas');
    }
    
    const data = await response.json();
    return {
      token: data.access_token,
      user: {
        name: data.name || email.split('@')[0],
        email: data.email || email
      }
    };
  },

  async verifyToken(): Promise<User> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No token found');
    }

    // Por ahora, simplemente validamos que el token existe
    // En el futuro se puede implementar un endpoint /me en el backend
    try {
      // Decodificar el token JWT para obtener información básica
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        name: payload.name || payload.email?.split('@')[0] || 'Usuario',
        email: payload.email || 'usuario@example.com'
      };
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
};

// Legacy exports for backward compatibility
export async function registerUser(data: { email: string; nombre: string; password: string }) {
  return authApi.register(data.nombre, data.email, data.password);
}

export async function loginUser(data: { email: string; password: string }) {
  return authApi.login(data.email, data.password);
}