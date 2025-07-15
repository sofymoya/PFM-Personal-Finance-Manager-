import React, { useState, useEffect } from 'react';
import { formatCurrency, formatPesos } from '../utils/formatters';
import TransactionTable from '../components/TransactionTable';
import type { Transaction } from '../components/TransactionTable';

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

const Dashboard: React.FC<DashboardProps> = ({ userId }) => {
  const [saldoGlobal, setSaldoGlobal] = useState<SaldoGlobal | null>(null);
  const [metas, setMetas] = useState<Meta[]>([]);
  const [transacciones, setTransacciones] = useState<Transaction[]>([]);
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            📊 Dashboard Financiero
          </h1>
          <p className="text-lg text-gray-600">
            Resumen completo de tu situación financiera
          </p>
        </div>

        {/* Saldo Global Cards */}
        {saldoGlobal && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">💰 Saldo Global</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Saldo Neto */}
              <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-2xl shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90">Saldo Neto</p>
                    <p className="text-3xl font-bold">{formatPesos(saldoGlobal.saldo_neto)}</p>
                  </div>
                  <div className="text-4xl">💰</div>
                </div>
              </div>

              {/* Ahorro */}
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-2xl shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90">Ahorro</p>
                    <p className="text-2xl font-bold">{formatPesos(saldoGlobal.total_ahorro)}</p>
                  </div>
                  <div className="text-4xl">🏦</div>
                </div>
              </div>

              {/* Corriente */}
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6 rounded-2xl shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90">Corriente</p>
                    <p className="text-2xl font-bold">{formatPesos(saldoGlobal.total_corriente)}</p>
                  </div>
                  <div className="text-4xl">💳</div>
                </div>
              </div>

              {/* Inversión */}
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-6 rounded-2xl shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90">Inversión</p>
                    <p className="text-2xl font-bold">{formatPesos(saldoGlobal.total_inversion)}</p>
                  </div>
                  <div className="text-4xl">📈</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Cuentas */}
        {saldoGlobal && saldoGlobal.cuentas.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🏦 Mis Cuentas</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {saldoGlobal.cuentas.map(cuenta => (
                <div key={cuenta.id} className="bg-white rounded-2xl shadow-lg p-6 border-l-4" style={{ borderLeftColor: cuenta.color }}>
                  <div className="flex items-center mb-4">
                    <span className="text-3xl mr-3">{cuenta.icono}</span>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">{cuenta.nombre}</h3>
                      <p className="text-sm text-gray-500 capitalize">{cuenta.tipo}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-sm text-gray-600">Saldo Actual</p>
                      <p className="text-lg font-bold text-gray-900">{formatPesos(cuenta.saldo_actual)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Disponible</p>
                      <p className="text-lg font-semibold text-green-600">{formatPesos(cuenta.saldo_disponible)}</p>
                    </div>
                    {cuenta.limite_credito && (
                      <div>
                        <p className="text-sm text-gray-600">Límite de Crédito</p>
                        <p className="text-lg font-semibold text-blue-600">{formatPesos(cuenta.limite_credito)}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metas */}
        {metas.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">🎯 Mis Metas</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {metas.map(meta => {
                const progress = getProgressPercentage(meta.monto_actual, meta.monto_objetivo);
                const daysLeft = meta.fecha_objetivo ? getDaysUntilGoal(meta.fecha_objetivo) : null;
                
                return (
                  <div key={meta.id} className="bg-white rounded-2xl shadow-lg p-6 border-l-4" style={{ borderLeftColor: meta.color }}>
                    <div className="flex items-center mb-4">
                      <span className="text-3xl mr-3">{meta.icono}</span>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">{meta.nombre}</h3>
                        {meta.descripcion && (
                          <p className="text-sm text-gray-500">{meta.descripcion}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>Progreso</span>
                          <span>{progress.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div 
                            className="h-3 rounded-full transition-all duration-300" 
                            style={{ 
                              width: `${progress}%`, 
                              backgroundColor: meta.color 
                            }}
                          ></div>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-sm text-gray-600">Actual</p>
                          <p className="text-lg font-bold text-gray-900">{formatPesos(meta.monto_actual)}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Objetivo</p>
                          <p className="text-lg font-bold" style={{ color: meta.color }}>{formatPesos(meta.monto_objetivo)}</p>
                        </div>
                      </div>
                      
                      {daysLeft !== null && (
                        <div className="text-center">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            daysLeft < 0 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {daysLeft < 0 
                              ? `${Math.abs(daysLeft)} días de retraso` 
                              : `${daysLeft} días restantes`
                            }
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Transacciones Recientes */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">📋 Transacciones Recientes</h2>
          <TransactionTable 
            transactions={transacciones} 
            showActions={false}
          />
          {transacciones.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No hay transacciones recientes para mostrar.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 