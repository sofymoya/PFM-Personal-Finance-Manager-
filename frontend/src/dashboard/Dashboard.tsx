import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';

interface DashboardProps {
  userId: number;
}

interface SaldoGlobal {
  total_ahorro: number;
  total_corriente: number;
  total_inversion: number;
  total_credito: number;
  saldo_neto: number;
  cuentas: Cuenta[];
}

interface Cuenta {
  id: number;
  nombre: string;
  tipo: string;
  saldo_actual: number;
  saldo_disponible: number;
  limite_credito?: number;
  color: string;
  icono: string;
  fecha_actualizacion: string;
}

interface Meta {
  id: number;
  nombre: string;
  descripcion?: string;
  monto_objetivo: number;
  monto_actual: number;
  fecha_objetivo?: string;
  color: string;
  icono: string;
  completada: boolean;
}

interface Transaccion {
  id: number;
  fecha: string;
  descripcion: string;
  monto: number;
  categoria?: {
    nombre: string;
    color: string;
  };
}

const Dashboard: React.FC<DashboardProps> = ({ userId }) => {
  const [saldoGlobal, setSaldoGlobal] = useState<SaldoGlobal | null>(null);
  const [metas, setMetas] = useState<Meta[]>([]);
  const [transacciones, setTransacciones] = useState<Transaccion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [userId]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Obtener saldo global
      const saldoResponse = await fetch(`http://localhost:8000/usuarios/${userId}/saldo-global/`, { headers });
      const saldoData = await saldoResponse.json();
      setSaldoGlobal(saldoData);

      // Obtener metas
      const metasResponse = await fetch(`http://localhost:8000/usuarios/${userId}/metas/`, { headers });
      const metasData = await metasResponse.json();
      setMetas(metasData);

      // Obtener transacciones recientes (últimas 5)
      const transaccionesResponse = await fetch(`http://localhost:8000/usuarios/${userId}/transacciones/`, { headers });
      const transaccionesData = await transaccionesResponse.json();
      setTransacciones(transaccionesData.slice(0, 5));

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercentage = (actual: number, objetivo: number) => {
    return Math.min((actual / objetivo) * 100, 100);
  };

  const getDaysUntilGoal = (fechaObjetivo: string) => {
    const today = new Date();
    const objetivo = new Date(fechaObjetivo);
    const diffTime = objetivo.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div>Cargando dashboard...</div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ color: '#2c3e50', marginBottom: '2rem' }}>📊 Dashboard Financiero</h1>

      {/* Saldo Global */}
      {saldoGlobal && (
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ color: '#34495e', marginBottom: '1rem' }}>💰 Saldo Global</h2>
          <div style={{
            backgroundColor: '#ecf0f1',
            padding: '1.5rem',
            borderRadius: '12px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#27ae60' }}>
                {formatCurrency(saldoGlobal.saldo_neto)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Saldo Neto</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#3498db' }}>
                {formatCurrency(saldoGlobal.total_ahorro)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Ahorro</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#e67e22' }}>
                {formatCurrency(saldoGlobal.total_corriente)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Corriente</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#9b59b6' }}>
                {formatCurrency(saldoGlobal.total_inversion)}
              </div>
              <div style={{ color: '#7f8c8d' }}>Inversión</div>
            </div>
          </div>
        </div>
      )}

      {/* Cuentas */}
      {saldoGlobal && saldoGlobal.cuentas.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ color: '#34495e', marginBottom: '1rem' }}>🏦 Mis Cuentas</h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1rem'
          }}>
            {saldoGlobal.cuentas.map(cuenta => (
              <div key={cuenta.id} style={{
                backgroundColor: 'white',
                border: `2px solid ${cuenta.color}`,
                borderRadius: '12px',
                padding: '1rem',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>{cuenta.icono}</span>
                  <h3 style={{ margin: 0, color: cuenta.color }}>{cuenta.nombre}</h3>
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                  {formatCurrency(cuenta.saldo_actual)}
                </div>
                <div style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                  Disponible: {formatCurrency(cuenta.saldo_disponible)}
                </div>
                {cuenta.limite_credito && (
                  <div style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                    Límite: {formatCurrency(cuenta.limite_credito)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metas */}
      {metas.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ color: '#34495e', marginBottom: '1rem' }}>🎯 Mis Metas</h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1rem'
          }}>
            {metas.map(meta => {
              const progress = getProgressPercentage(meta.monto_actual, meta.monto_objetivo);
              const daysLeft = meta.fecha_objetivo ? getDaysUntilGoal(meta.fecha_objetivo) : null;
              
              return (
                <div key={meta.id} style={{
                  backgroundColor: 'white',
                  border: `2px solid ${meta.color}`,
                  borderRadius: '12px',
                  padding: '1rem',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>{meta.icono}</span>
                    <h3 style={{ margin: 0, color: meta.color }}>{meta.nombre}</h3>
                  </div>
                  {meta.descripcion && (
                    <div style={{ color: '#7f8c8d', marginBottom: '0.5rem' }}>
                      {meta.descripcion}
                    </div>
                  )}
                  <div style={{ marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span>{formatCurrency(meta.monto_actual)}</span>
                      <span>{formatCurrency(meta.monto_objetivo)}</span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      backgroundColor: '#ecf0f1',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${progress}%`,
                        height: '100%',
                        backgroundColor: meta.color,
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <div style={{ textAlign: 'center', fontSize: '0.9rem', color: '#7f8c8d', marginTop: '0.25rem' }}>
                      {progress.toFixed(1)}% completado
                    </div>
                  </div>
                  {daysLeft !== null && (
                    <div style={{ fontSize: '0.9rem', color: daysLeft < 0 ? '#e74c3c' : '#7f8c8d' }}>
                      {daysLeft < 0 ? `${Math.abs(daysLeft)} días de retraso` : `${daysLeft} días restantes`}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Transacciones Recientes */}
      {transacciones.length > 0 && (
        <div>
          <h2 style={{ color: '#34495e', marginBottom: '1rem' }}>📝 Transacciones Recientes</h2>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '1rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            {transacciones.map(transaccion => (
              <div key={transaccion.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 0',
                borderBottom: '1px solid #ecf0f1'
              }}>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{transaccion.descripcion}</div>
                  <div style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                    {new Date(transaccion.fecha).toLocaleDateString()}
                    {transaccion.categoria && (
                      <span style={{
                        backgroundColor: transaccion.categoria.color,
                        color: 'white',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '12px',
                        fontSize: '0.8rem',
                        marginLeft: '0.5rem'
                      }}>
                        {transaccion.categoria.nombre}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{
                  fontWeight: 'bold',
                  color: transaccion.monto < 0 ? '#e74c3c' : '#27ae60'
                }}>
                  {formatCurrency(transaccion.monto)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!saldoGlobal && metas.length === 0 && transacciones.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎉</div>
          <h2>¡Bienvenido a tu Dashboard Financiero!</h2>
          <p style={{ color: '#7f8c8d' }}>
            Comienza agregando cuentas, metas y transacciones para ver tu resumen financiero aquí.
          </p>
        </div>
      )}
    </div>
  );
};

export default Dashboard; 