import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el token de autenticación
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Tipos de datos
export interface User {
  id: number;
  email: string;
  name?: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  name?: string;
}

export interface Transaction {
  id: number;
  description: string;
  amount: number;
  date: string;
  category?: string;
  user_id: number;
  created_at: string;
}

export interface TransactionCreate {
  description: string;
  amount: number;
  date: string;
  category?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
}

// Funciones de autenticación
export const authAPI = {
  register: (userData: UserCreate) => api.post<User>('/register', userData),
  login: (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post<LoginResponse>('/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Funciones de transacciones
export const transactionsAPI = {
  getAll: () => api.get<Transaction[]>('/transactions/'),
  getById: (id: number) => api.get<Transaction>(`/transactions/${id}`),
  create: (transaction: TransactionCreate) => api.post<Transaction>('/transactions/', transaction),
  update: (id: number, transaction: TransactionCreate) => 
    api.put<Transaction>(`/transactions/${id}`, transaction),
  delete: (id: number) => api.delete(`/transactions/${id}`),
};

export default api; 