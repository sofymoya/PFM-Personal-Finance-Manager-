/// <reference types="vitest" />
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';

describe('Login page', () => {
  it('renders the login form', () => {
    render(
      <MemoryRouter>
        <Login onLogin={async () => ({ success: true })} />
      </MemoryRouter>
    );
    expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email or username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log in/i })).toBeInTheDocument();
    expect(screen.getByText(/Don't have an account/i)).toBeInTheDocument();
  });

  it('calls onLogin when submitting the form', async () => {
    const onLogin = vi.fn().mockResolvedValue({ success: true });
    render(
      <MemoryRouter>
        <Login onLogin={onLogin} />
      </MemoryRouter>
    );
    await userEvent.type(screen.getByPlaceholderText('Email or username'), 'test@example.com');
    await userEvent.type(screen.getByPlaceholderText('Password'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /Log in/i }));
    expect(onLogin).toHaveBeenCalledWith('test@example.com', 'password123');
  });
}); 