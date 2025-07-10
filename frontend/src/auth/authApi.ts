export async function registerUser(data: { email: string; nombre: string; password: string }) {
  const response = await fetch('http://localhost:8000/usuarios/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Error al registrar');
  }
  return response.json();
}

export async function loginUser(data: { email: string; password: string }) {
  const params = new URLSearchParams();
  params.append('username', data.email);
  params.append('password', data.password);

  const response = await fetch('http://localhost:8000/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params,
  });

  if (!response.ok) {
    throw new Error('Credenciales incorrectas');
  }
  return response.json();
}