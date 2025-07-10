import React from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    navigate('/login');
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f9fafb',
      fontFamily: 'Arial, sans-serif'
    }}>
      {/* Header */}
      <nav style={{ 
        backgroundColor: 'white', 
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        padding: '1rem 0'
      }}>
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          padding: '0 1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1 style={{ 
            fontSize: '1.25rem', 
            fontWeight: '600', 
            color: '#111827',
            margin: 0
          }}>
            PFM Dashboard
          </h1>
          <button
            onClick={handleLogout}
            style={{ 
              backgroundColor: '#dc2626', 
              color: 'white', 
              padding: '0.5rem 1rem', 
              borderRadius: '0.375rem', 
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}
          >
            Cerrar Sesión
          </button>
        </div>
      </nav>

      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        padding: '1.5rem'
      }}>
        {/* Balance Total */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '0.5rem', 
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          marginBottom: '1.5rem',
          padding: '1.5rem'
        }}>
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ 
              fontSize: '1.125rem', 
              fontWeight: '500', 
              color: '#111827',
              marginBottom: '0.5rem'
            }}>
              Balance Total
            </h3>
            <div style={{ 
              fontSize: '1.875rem', 
              fontWeight: 'bold', 
              color: '#059669'
            }}>
              $0.00
            </div>
          </div>
        </div>

        {/* Mensaje de bienvenida */}
        <div style={{ 
          backgroundColor: 'white', 
          borderRadius: '0.5rem', 
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <h2 style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: '#111827',
            marginBottom: '1rem'
          }}>
            🎉 ¡Bienvenido al Dashboard!
          </h2>
          <p style={{ 
            color: '#6b7280', 
            fontSize: '1.125rem',
            marginBottom: '1.5rem'
          }}>
            Has iniciado sesión correctamente. El dashboard está funcionando.
          </p>
          <div style={{ 
            display: 'flex', 
            gap: '1rem', 
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={() => alert('Funcionalidad de transacciones próximamente')}
              style={{ 
                backgroundColor: '#3b82f6', 
                color: 'white', 
                padding: '0.75rem 1.5rem', 
                borderRadius: '0.375rem', 
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '500'
              }}
            >
              Ver Transacciones
            </button>
            <button
              onClick={() => alert('Funcionalidad de reportes próximamente')}
              style={{ 
                backgroundColor: '#10b981', 
                color: 'white', 
                padding: '0.75rem 1.5rem', 
                borderRadius: '0.375rem', 
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '500'
              }}
            >
              Ver Reportes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 