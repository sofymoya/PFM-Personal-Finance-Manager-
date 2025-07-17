import React, { useState, useEffect, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import Select from 'react-select';
import { formatPesos } from '../utils/formatters';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// Definir la interfaz localmente para evitar problemas de importación
interface Transaction {
  id: number;
  fecha: string;
  descripcion: string;
  monto: number;
  categoria?: {
    id: number;
    nombre: string;
  };
}

// 1. Definir tipo explícito para las transacciones extraídas del PDF
interface ExtractedTransaction {
  fecha_operacion?: string;
  fecha_cargo?: string;
  descripcion: string;
  monto: number | string;
}

const API_BASE_URL = 'http://localhost:8000';

// Función para obtener el token
const getToken = (): string | null => {
  return localStorage.getItem('token');
};

// Función para cargar transacciones
const loadTransactions = async (userId: number): Promise<Transaction[]> => {
  const token = getToken();
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const response = await fetch(`${API_BASE_URL}/usuarios/${userId}/transacciones/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Error al cargar transacciones');
  }

  return response.json();
};

// Función para crear nueva transacción
const createTransaction = async (userId: number, transaction: {
  fecha: string;
  descripcion: string;
  monto: number;
  categoria?: string;
}): Promise<Transaction> => {
  const token = getToken();
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const response = await fetch(`${API_BASE_URL}/usuarios/${userId}/transacciones/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(transaction),
  });

  if (!response.ok) {
    throw new Error('Error al crear transacción');
  }

  return response.json();
};

// Función para actualizar transacción
const updateTransaction = async (userId: number, transactionId: number, transaction: {
  fecha: string;
  descripcion: string;
  monto: number;
}): Promise<Transaction> => {
  const token = getToken();
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const response = await fetch(`${API_BASE_URL}/usuarios/${userId}/transacciones/${transactionId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(transaction),
  });

  if (!response.ok) {
    throw new Error('Error al actualizar transacción');
  }

  return response.json();
};

// Función para eliminar transacción
const deleteTransaction = async (userId: number, transactionId: number): Promise<void> => {
  const token = getToken();
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const response = await fetch(`${API_BASE_URL}/usuarios/${userId}/transacciones/${transactionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Error al eliminar transacción');
  }
};

// Función para subir PDF
const uploadPDF = async (
  userId: number,
  file: File
): Promise<{ method?: string; total_pages?: number; text?: string; transactions?: ExtractedTransaction[] }> => {
  const token = getToken();
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/usuarios/${userId}/upload-pdf/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Error al subir PDF');
  }

  return response.json();
};

interface TransactionsProps { userId?: number }

const Transactions: React.FC<TransactionsProps> = ({ userId }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    descripcion: '',
    monto: '',
    categoria: ''
  });
  const [showPdfUpload, setShowPdfUpload] = useState(false);
  // 2. Tipar correctamente pdfResult y estados relacionados
  const [pdfResult, setPdfResult] = useState<{
    method?: string;
    total_pages?: number;
    text?: string;
    transactions?: ExtractedTransaction[];
  } | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [savingTransactions, setSavingTransactions] = useState(false);

  // Filtros de búsqueda
  const [filter, setFilter] = useState<{
    fechaInicio: string;
    fechaFin: string;
    categoria: string;
    montoMin: string;
    montoMax: string;
    descripcion: string;
  }>({
    fechaInicio: '',
    fechaFin: '',
    categoria: '',
    montoMin: '',
    montoMax: '',
    descripcion: ''
  });

  // Estados para edición rápida de categoría
  const [editingCategory, setEditingCategory] = useState<number | null>(null);
  const [categoryOptions, setCategoryOptions] = useState<{ value: string; label: string }[]>([]);
  
  // Estado para pestañas por mes
  const [selectedMonth, setSelectedMonth] = useState<string>('all');

  // 1. Define explicit types for grouping and stats objects
  interface TransactionsByMonth {
    [month: string]: {
      name: string;
      transactions: Transaction[];
    };
  }

  interface CategoryStats {
    [category: string]: {
      gastos: number;
      ingresos: number;
      total: number;
    };
  }

  interface MonthStats {
    [month: string]: {
      nombre: string;
      gastos: number;
      ingresos: number;
      total: number;
    };
  }

  // Obtener lista de categorías únicas
  const categoriasUnicas = Array.from(new Set(transactions.map(t => t.categoria ? (typeof t.categoria === 'string' ? t.categoria : t.categoria?.nombre) : 'Sin categoría')));

  // 2. Update groupTransactionsByMonth to use TransactionsByMonth type
  const groupTransactionsByMonth = (): TransactionsByMonth => {
    const grouped = transactions.reduce((acc: TransactionsByMonth, transaction: Transaction) => {
      const date = new Date(transaction.fecha);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const monthName = date.toLocaleDateString('es-ES', { year: 'numeric', month: 'long' });
      if (!acc[monthKey]) {
        acc[monthKey] = {
          name: monthName,
          transactions: []
        };
      }
      acc[monthKey].transactions.push(transaction);
      return acc;
    }, {} as TransactionsByMonth);
    // Ordenar meses del más reciente al más antiguo
    return Object.entries(grouped)
      .sort(([a], [b]) => b.localeCompare(a))
      .reduce((acc: TransactionsByMonth, [key, value]: [string, { name: string; transactions: Transaction[] }]) => {
        acc[key] = value;
        return acc;
      }, {} as TransactionsByMonth);
  };

  const transactionsByMonth = groupTransactionsByMonth();
  const monthTabs = Object.keys(transactionsByMonth);

  // Filtrar transacciones según filtros y pestaña seleccionada
  const getFilteredTransactions = () => {
    let transactionsToFilter = transactions;
    
    // Si hay una pestaña seleccionada, filtrar por ese mes
    if (selectedMonth !== 'all' && transactionsByMonth[selectedMonth]) {
      transactionsToFilter = transactionsByMonth[selectedMonth].transactions;
    }
    
    return transactionsToFilter
      .filter((t: Transaction) => {
        // Fecha
        if (filter.fechaInicio && new Date(t.fecha) < new Date(filter.fechaInicio)) return false;
        if (filter.fechaFin && new Date(t.fecha) > new Date(filter.fechaFin)) return false;
        // Categoría
        const cat = t.categoria ? (typeof t.categoria === 'string' ? t.categoria : t.categoria?.nombre) : 'Sin categoría';
        if (filter.categoria && filter.categoria !== cat) return false;
        // Monto
        if (filter.montoMin && t.monto < parseFloat(filter.montoMin)) return false;
        if (filter.montoMax && t.monto > parseFloat(filter.montoMax)) return false;
        // Descripción
        if (filter.descripcion && !t.descripcion.toLowerCase().includes(filter.descripcion.toLowerCase())) return false;
        return true;
      })
      .sort((a: Transaction, b: Transaction) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime()); // Ordenar del más reciente al más antiguo
  };

  const filteredTransactions = getFilteredTransactions();

  const fetchTransactions = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loadTransactions(userId!);
      setTransactions(data);
    } catch (err) {
      setError('Error al cargar transacciones');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.descripcion || !formData.monto) {
      alert('Por favor completa todos los campos');
      return;
    }

    // Sugerir categoría automáticamente si no se seleccionó
    let categoria = formData.categoria;
    if (!categoria) {
      categoria = categorizeTransaction(formData.descripcion);
    }

    try {
      if (editingTransaction) {
        // Actualizar transacción existente
        const updatedTransaction = await updateTransaction(userId!, editingTransaction.id, {
          fecha: formData.fecha,
          descripcion: formData.descripcion,
          monto: parseFloat(formData.monto)
        });

        // Actualizar la lista
        setTransactions(transactions.map(t => 
          t.id === editingTransaction.id ? updatedTransaction : t
        ));
        setEditingTransaction(null);
      } else {
        // Crear nueva transacción
        const newTransaction = await createTransaction(userId!, {
          fecha: formData.fecha,
          descripcion: formData.descripcion,
          monto: parseFloat(formData.monto),
          categoria: categoria
        });

        // Agregar la nueva transacción a la lista
        setTransactions([newTransaction, ...transactions]);
      }

      // Limpiar el formulario
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        descripcion: '',
        monto: '',
        categoria: ''
      });
      
      // Ocultar el formulario
      setShowForm(false);
    } catch (err) {
      alert('Error al guardar la transacción');
      console.error('Error:', err);
    }
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      fecha: transaction.fecha,
      descripcion: transaction.descripcion,
      monto: transaction.monto.toString(),
      categoria: transaction.categoria ? transaction.categoria.nombre : ''
    });
    setShowForm(true);
  };

  const handleDelete = async (transactionId: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta transacción?')) {
      return;
    }

    try {
      await deleteTransaction(userId!, transactionId);
      // Remover la transacción de la lista
      setTransactions(transactions.filter(t => t.id !== transactionId));
    } catch (err) {
      alert('Error al eliminar la transacción');
      console.error('Error:', err);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingTransaction(null);
    setFormData({
      fecha: new Date().toISOString().split('T')[0],
      descripcion: '',
      monto: '',
      categoria: ''
    });
  };

  const handlePdfUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      alert('Solo se permiten archivos PDF');
      return;
    }

    try {
      setUploadingPdf(true);
      const result = await uploadPDF(userId!, file);
      setPdfResult(result);
      setShowPdfUpload(true);
    } catch (err) {
      alert('Error al procesar el PDF');
      console.error('Error:', err);
    } finally {
      setUploadingPdf(false);
    }
  };

  // Función para categorizar automáticamente una transacción
  const categorizeTransaction = (description: string): string => {
    const desc = description.toLowerCase();
    
    // Categorías basadas en palabras clave
    if (desc.includes('rest') || desc.includes('cafe') || desc.includes('taqueria') || desc.includes('comida')) {
      return 'Comida y Restaurantes';
    }
    if (desc.includes('viva') || desc.includes('aerobus') || desc.includes('greyhound') || desc.includes('vuelo')) {
      return 'Transporte y Viajes';
    }
    if (desc.includes('heb') || desc.includes('super') || desc.includes('mercado') || desc.includes('oxxo')) {
      return 'Compras y Supermercado';
    }
    if (desc.includes('pago') || desc.includes('spei') || desc.includes('transferencia')) {
      return 'Pagos y Transferencias';
    }
    if (desc.includes('interes') || desc.includes('comision')) {
      return 'Intereses y Comisiones';
    }
    if (desc.includes('hotel') || desc.includes('alojamiento')) {
      return 'Hospedaje';
    }
    if (desc.includes('gasolina') || desc.includes('combustible')) {
      return 'Transporte';
    }
    if (desc.includes('entretenimiento') || desc.includes('cine') || desc.includes('evento')) {
      return 'Entretenimiento';
    }
    
    return 'Otros';
  };

  // Función para convertir fecha del formato AI al formato del backend
  const convertDate = (dateStr: string): string => {
    try {
      // Si la fecha ya está en formato YYYY-MM-DD, la devolvemos tal como está
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return dateStr;
      }
      
      // Convertir formato "DD-MMM-YYYY" a "YYYY-MM-DD"
      const months: { [key: string]: string } = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
      };
      
      // Patrón para fechas como "04-Jun-2025"
      const match = dateStr.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
      if (match) {
        const [, day, month, year] = match;
        const monthNum = months[month];
        if (monthNum) {
          return `${year}-${monthNum}-${day.padStart(2, '0')}`;
        }
      }
      
      // Si no podemos convertir, usar fecha actual
      console.warn(`No se pudo convertir la fecha: ${dateStr}, usando fecha actual`);
      return new Date().toISOString().split('T')[0];
    } catch (error) {
      console.error('Error convirtiendo fecha:', error);
      return new Date().toISOString().split('T')[0];
    }
  };

  // Función para guardar transacciones extraídas del PDF
  const handleSaveTransactions = async (extractedTransactions: ExtractedTransaction[]) => {
    try {
      setSavingTransactions(true);
      
      // Convertir transacciones del formato AI al formato de la base de datos
      const transactionsToSave = extractedTransactions.map(txn => {
        // Asegurar que los montos sean negativos (cargos)
        let monto = parseFloat(txn.monto.toString().replace(/[^0-9.-]/g, ''));
        if (monto > 0) {
          monto = -monto; // Convertir a negativo si es positivo
        }
        
        // Categorizar automáticamente
        const categoria = categorizeTransaction(txn.descripcion);
        
        return {
          fecha: convertDate(txn.fecha_operacion ?? txn.fecha_cargo ?? ''),
          descripcion: txn.descripcion,
          monto: monto,
          categoria: categoria
        };
      });

      console.log('Transacciones a guardar:', transactionsToSave);

      // Guardar cada transacción
      const savedTransactions = [];
      for (const txn of transactionsToSave) {
        try {
          const savedTxn = await createTransaction(userId!, txn);
          savedTransactions.push(savedTxn);
        } catch (error) {
          console.error(`Error guardando transacción: ${txn.descripcion}`, error);
        }
      }

      // Actualizar la lista de transacciones
      setTransactions([...savedTransactions, ...transactions]);
      
      // Mostrar mensaje de éxito
      alert(`✅ Se guardaron ${savedTransactions.length} transacciones exitosamente`);
      
      // Cerrar el modal del PDF
      setShowPdfUpload(false);
      setPdfResult(null);
      
    } catch (error) {
      console.error('Error guardando transacciones:', error);
      alert('❌ Error al guardar las transacciones');
    } finally {
      setSavingTransactions(false);
    }
  };

  // Función para obtener el color de una categoría
  const getCategoryColor = (category: string): string => {
    const colors: { [key: string]: string } = {
      'Comida y Restaurantes': '#ff6b6b',
      'Transporte y Viajes': '#4ecdc4',
      'Compras y Supermercado': '#45b7d1',
      'Pagos y Transferencias': '#96ceb4',
      'Intereses y Comisiones': '#feca57',
      'Hospedaje': '#ff9ff3',
      'Transporte': '#54a0ff',
      'Entretenimiento': '#5f27cd',
      'Sin categoría': '#8395a7'
    };
    return colors[category] || colors['Sin categoría'];
  };

  // Función para obtener el nombre de la categoría
  const getCategoryName = (category: string | { id: number; nombre: string } | undefined): string => {
    if (typeof category === 'string') {
      return category;
    }
    if (category && typeof category === 'object' && category.nombre) {
      return category.nombre;
    }
    return 'Sin categoría';
  };

  // Función para formatear números con comas
  const formatCurrency = (amount: number): string => {
    return formatPesos(amount);
  };

  // 3. Update calcularEstadisticas to use CategoryStats and MonthStats
  const calcularEstadisticas = () => {
    const totalGastado = transactions
      .filter((t: Transaction) => t.monto < 0)
      .reduce((sum: number, t: Transaction) => sum + Math.abs(t.monto), 0);
    
    const totalIngresado = transactions
      .filter((t: Transaction) => t.monto > 0)
      .reduce((sum: number, t: Transaction) => sum + t.monto, 0);
    
    const balance = totalIngresado - totalGastado;
    
    // Estadísticas por categoría
    const statsPorCategoria = transactions.reduce((acc: CategoryStats, t: Transaction) => {
      const categoria = getCategoryName(t.categoria);
      if (!acc[categoria]) {
        acc[categoria] = { gastos: 0, ingresos: 0, total: 0 };
      }
      if (t.monto < 0) {
        acc[categoria].gastos += Math.abs(t.monto);
      } else {
        acc[categoria].ingresos += t.monto;
      }
      acc[categoria].total += t.monto;
      return acc;
    }, {} as CategoryStats);
    
    // Estadísticas por mes
    const statsPorMes = transactions.reduce((acc: MonthStats, t: Transaction) => {
      const fecha = new Date(t.fecha);
      const mesKey = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}`;
      const mesNombre = fecha.toLocaleDateString('es-ES', { year: 'numeric', month: 'long' });
      
      if (!acc[mesKey]) {
        acc[mesKey] = { nombre: mesNombre, gastos: 0, ingresos: 0, total: 0 };
      }
      if (t.monto < 0) {
        acc[mesKey].gastos += Math.abs(t.monto);
      } else {
        acc[mesKey].ingresos += t.monto;
      }
      acc[mesKey].total += t.monto;
      return acc;
    }, {} as MonthStats);
    
    return {
      totalGastado,
      totalIngresado,
      balance,
      statsPorCategoria,
      statsPorMes
    };
  };

  // Preparar datos para gráfica de barras por mes
  const prepararDatosGraficaBarras = () => {
    const stats = calcularEstadisticas();
    
    // Convertir a array y ordenar por fecha real
    const meses = Object.entries(stats.statsPorMes).map(([key, data]: [string, { nombre: string; gastos: number; ingresos: number; total: number }]) => ({
      key,
      ...data
    })).sort((a, b) => {
      // Ordenar por la key que contiene YYYY-MM
      return a.key.localeCompare(b.key);
    });
    
    return {
      labels: meses.map((m) => m.nombre),
      datasets: [
        {
          label: 'Gastos',
          data: meses.map((m) => m.gastos),
          backgroundColor: 'rgba(220, 53, 69, 0.8)',
          borderColor: 'rgba(220, 53, 69, 1)',
          borderWidth: 1,
        },
        {
          label: 'Ingresos',
          data: meses.map((m) => m.ingresos),
          backgroundColor: 'rgba(40, 167, 69, 0.8)',
          borderColor: 'rgba(40, 167, 69, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  // Preparar datos para gráfica de pastel por categoría
  const prepararDatosGraficaPastel = () => {
    const stats = calcularEstadisticas();
    const categorias = Object.entries(stats.statsPorCategoria)
      .filter(([, data]) => data.gastos > 0)
      .sort(([, a], [, b]) => b.gastos - a.gastos);
    
    const colors = [
      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
      '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43'
    ];
    
    return {
      labels: categorias.map(([cat, ]) => cat),
      datasets: [
        {
          data: categorias.map(([, data]: [string, { gastos: number; ingresos: number; total: number }]) => data.gastos),
          backgroundColor: colors.slice(0, categorias.length),
          borderWidth: 2,
          borderColor: '#fff',
        },
      ],
    };
  };

  // Función para actualizar categoría rápidamente
  const updateCategoryQuickly = async (transactionId: number, newCategoryName: string) => {
    console.log('Actualizando categoría:', { transactionId, newCategoryName });
    try {
      const response = await fetch(`http://localhost:8000/usuarios/${userId}/transacciones/${transactionId}/categoria`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          categoria: newCategoryName
        }),
      });

      console.log('Respuesta del servidor:', response.status);
      
      if (response.ok) {
        const updatedTransaction = await response.json();
        console.log('Transacción actualizada:', updatedTransaction);
        
        // Actualizar la transacción localmente
        setTransactions(prev => prev.map(t => 
          t.id === transactionId 
            ? { ...t, categoria: { id: updatedTransaction.categoria?.id || 0, nombre: newCategoryName } }
            : t
        ));
        setEditingCategory(null);
        console.log('Categoría actualizada exitosamente');
      } else {
        const errorData = await response.text();
        console.error('Error al actualizar categoría:', response.status, errorData);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const stats = calcularEstadisticas();

  // 1. Limpieza de callbacks: reemplaza (t: any) => ... por (t: Transaction) => ...
  //    y (a: any, b: any) => ... por (a: Transaction, b: Transaction) => ...
  //    Elimina variables _, __ no usadas en reduce/map/sort.
  // 2. Para useEffect principal:
  // Preparar opciones de categorías para el dropdown
  useEffect(() => {
    const uniqueCategories = [...new Set(transactions.map(t => getCategoryName(t.categoria)))];
    const options = uniqueCategories.map(cat => ({
      value: cat,
      label: cat
    }));
    setCategoryOptions(options);
  }, [transactions]);

  if (loading) return <div style={{ padding: 20 }}>Cargando transacciones...</div>;
  if (error) return <div style={{ padding: 20, color: 'red' }}>Error: {error}</div>;

  return (
    <div style={{ padding: 20 }}>
      <h2>Mis Transacciones</h2>
      
      <div style={{ marginBottom: 20 }}>
        <button 
          onClick={() => setShowForm(!showForm)}
          style={{ marginRight: 10 }}
        >
          {showForm ? 'Cancelar' : 'Agregar Transacción'}
        </button>
        <button onClick={() => document.getElementById('pdf-upload')?.click()}>
          {uploadingPdf ? 'Procesando PDF...' : 'Cargar PDF'}
        </button>
        <input
          id="pdf-upload"
          type="file"
          accept=".pdf"
          onChange={handlePdfUpload}
          style={{ display: 'none' }}
        />
        <button onClick={fetchTransactions} style={{ marginLeft: 10 }}>
          Actualizar
        </button>
      </div>

      {/* Filtros arriba de la tabla */}
      <div style={{
        display: 'flex',
        gap: 16,
        marginBottom: 20,
        flexWrap: 'wrap',
        alignItems: 'flex-end'
      }}>
        <div>
          <label>Fecha inicio<br/>
            <input type="date" value={filter.fechaInicio} onChange={e => setFilter(f => ({...f, fechaInicio: e.target.value}))} />
          </label>
        </div>
        <div>
          <label>Fecha fin<br/>
            <input type="date" value={filter.fechaFin} onChange={e => setFilter(f => ({...f, fechaFin: e.target.value}))} />
          </label>
        </div>
        <div>
          <label>Categoría<br/>
            <select value={filter.categoria} onChange={e => setFilter(f => ({...f, categoria: e.target.value}))}>
              <option value="">Todas</option>
              {categoriasUnicas.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </label>
        </div>
        <div>
          <label>Monto mínimo<br/>
            <input type="number" value={filter.montoMin} onChange={e => setFilter(f => ({...f, montoMin: e.target.value}))} style={{width: 90}} />
          </label>
        </div>
        <div>
          <label>Monto máximo<br/>
            <input type="number" value={filter.montoMax} onChange={e => setFilter(f => ({...f, montoMax: e.target.value}))} style={{width: 90}} />
          </label>
        </div>
        <div style={{flex: 1}}>
          <label>Descripción<br/>
            <input type="text" value={filter.descripcion} onChange={e => setFilter(f => ({...f, descripcion: e.target.value}))} style={{width: '100%'}} placeholder="Buscar..." />
          </label>
        </div>
        <button onClick={() => setFilter({fechaInicio:'',fechaFin:'',categoria:'',montoMin:'',montoMax:'',descripcion:''})} style={{height: 36}}>Limpiar</button>
      </div>

      {/* Estadísticas y Gráficas */}
      <div style={{ marginBottom: 30 }}>
        <h3>📊 Estadísticas Financieras</h3>
        
        {/* Tarjetas de resumen */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: 16, 
          marginBottom: 24 
        }}>
          <div style={{
            backgroundColor: '#dc3545',
            color: 'white',
            padding: 20,
            borderRadius: 8,
            textAlign: 'center'
          }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 16 }}>💰 Total Gastado</h4>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>
              {formatCurrency(stats.totalGastado)}
            </div>
          </div>
          
          <div style={{
            backgroundColor: '#28a745',
            color: 'white',
            padding: 20,
            borderRadius: 8,
            textAlign: 'center'
          }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 16 }}>💵 Total Ingresado</h4>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>
              {formatCurrency(stats.totalIngresado)}
            </div>
          </div>
          
          <div style={{
            backgroundColor: stats.balance >= 0 ? '#17a2b8' : '#ffc107',
            color: 'white',
            padding: 20,
            borderRadius: 8,
            textAlign: 'center'
          }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 16 }}>⚖️ Balance</h4>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>
              {formatCurrency(stats.balance)}
            </div>
          </div>
          
          <div style={{
            backgroundColor: '#6c757d',
            color: 'white',
            padding: 20,
            borderRadius: 8,
            textAlign: 'center'
          }}>
            <h4 style={{ margin: '0 0 8px 0', fontSize: 16 }}>📈 Total Transacciones</h4>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>
              {transactions.length}
            </div>
          </div>
        </div>

        {/* Gráficas */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
          gap: 24 
        }}>
          {/* Gráfica de barras por mes */}
          <div style={{
            backgroundColor: 'white',
            padding: 20,
            borderRadius: 8,
            border: '1px solid #ddd',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ margin: '0 0 16px 0', textAlign: 'center' }}>📊 Gastos e Ingresos por Mes</h4>
            <Bar 
              data={prepararDatosGraficaBarras()} 
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'top' as const,
                  },
                  title: {
                    display: false,
                  },
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      callback: function(value) {
                        return formatCurrency(value as number);
                      }
                    }
                  }
                }
              }} 
            />
          </div>

          {/* Gráfica de pastel por categoría */}
          <div style={{
            backgroundColor: 'white',
            padding: 20,
            borderRadius: 8,
            border: '1px solid #ddd',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ margin: '0 0 16px 0', textAlign: 'center' }}>🥧 Gastos por Categoría</h4>
            <Pie 
              data={prepararDatosGraficaPastel()} 
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'bottom' as const,
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed;
                        const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                      }
                    }
                  }
                }
              }} 
            />
          </div>
        </div>

        {/* Tabla de estadísticas por categoría */}
        <div style={{ marginTop: 24 }}>
          <h4>📋 Resumen por Categoría</h4>
          <div style={{
            backgroundColor: 'white',
            borderRadius: 8,
            border: '1px solid #ddd',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '1px solid #ddd' }}>Categoría</th>
                  <th style={{ padding: 12, textAlign: 'right', borderBottom: '1px solid #ddd' }}>Gastos</th>
                  <th style={{ padding: 12, textAlign: 'right', borderBottom: '1px solid #ddd' }}>Ingresos</th>
                  <th style={{ padding: 12, textAlign: 'right', borderBottom: '1px solid #ddd' }}>Balance</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.statsPorCategoria)
                  .sort(([, a]: [string, { gastos: number; ingresos: number; total: number }], [, b]: [string, { gastos: number; ingresos: number; total: number }]) => Math.abs(b.total) - Math.abs(a.total))
                  .map(([categoria, data]: [string, { gastos: number; ingresos: number; total: number }]) => (
                    <tr key={categoria}>
                      <td style={{ padding: 12, borderBottom: '1px solid #eee' }}>
                        <span style={{
                          backgroundColor: getCategoryColor(categoria),
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}>
                          {categoria}
                        </span>
                      </td>
                      <td style={{ 
                        padding: 12, 
                        textAlign: 'right', 
                        borderBottom: '1px solid #eee',
                        color: '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        {formatCurrency(data.gastos)}
                      </td>
                      <td style={{ 
                        padding: 12, 
                        textAlign: 'right', 
                        borderBottom: '1px solid #eee',
                        color: '#28a745',
                        fontWeight: 'bold'
                      }}>
                        {formatCurrency(data.ingresos)}
                      </td>
                      <td style={{ 
                        padding: 12, 
                        textAlign: 'right', 
                        borderBottom: '1px solid #eee',
                        color: data.total >= 0 ? '#28a745' : '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        {formatCurrency(data.total)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Formulario para nueva/editar transacción */}
      {showForm && (
        <div style={{ 
          border: '1px solid #ddd', 
          padding: 20, 
          marginBottom: 20, 
          borderRadius: 5,
          backgroundColor: '#f9f9f9'
        }}>
          <h3>{editingTransaction ? 'Editar Transacción' : 'Nueva Transacción'}</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', marginBottom: 5 }}>
                Fecha:
              </label>
              <input
                type="date"
                value={formData.fecha}
                onChange={(e) => setFormData({...formData, fecha: e.target.value})}
                style={{ width: '100%', padding: 8 }}
                required
              />
            </div>
            
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', marginBottom: 5 }}>
                Descripción:
              </label>
              <input
                type="text"
                value={formData.descripcion}
                onChange={(e) => {
                  const desc = e.target.value;
                  setFormData({
                    ...formData,
                    descripcion: desc,
                    categoria: categorizeTransaction(desc)
                  });
                }}
                placeholder="Ej: Comida en restaurante"
                style={{ width: '100%', padding: 8 }}
                required
              />
            </div>
            
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', marginBottom: 5 }}>
                Monto:
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.monto}
                onChange={(e) => setFormData({...formData, monto: e.target.value})}
                placeholder="Ej: -25.50 (negativo para gastos)"
                style={{ width: '100%', padding: 8 }}
                required
              />
              <small style={{ color: '#666' }}>
                Usa números negativos para gastos, positivos para ingresos
              </small>
            </div>
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', marginBottom: 5 }}>
                Categoría sugerida:
              </label>
              <input
                type="text"
                value={formData.categoria}
                onChange={(e) => setFormData({...formData, categoria: e.target.value})}
                placeholder="Ej: Comida y Restaurantes"
                style={{ width: '100%', padding: 8 }}
              />
              <small style={{ color: '#666' }}>
                Puedes modificar la categoría sugerida
              </small>
            </div>
            <div>
              <button type="submit" style={{ marginRight: 10 }}>
                {editingTransaction ? 'Actualizar' : 'Guardar'} Transacción
              </button>
              <button 
                type="button" 
                onClick={handleCancel}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

{showPdfUpload && pdfResult && (
  <div style={{ 
    border: '1px solid #ddd', 
    padding: 20, 
    marginBottom: 20, 
    borderRadius: 5,
    backgroundColor: '#f9f9f9'
  }}>
    <h3>PDF Procesado Exitosamente ✅</h3>
    {/* Información del método usado */}
    <div style={{ 
      backgroundColor: pdfResult.method === 'OCR' ? '#e8f5e8' : '#e8f4fd', 
      padding: 10, 
      borderRadius: 5, 
      marginBottom: 15,
      border: `2px solid ${pdfResult.method === 'OCR' ? '#4caf50' : '#2196f3'}`
    }}>
      <strong>Método usado:</strong> {pdfResult.method === 'OCR' ? '🖼️ OCR (Reconocimiento de imagen)' : '📄 Extracción de texto PDF'}
      {pdfResult.method === 'OCR' && (
        <div style={{ fontSize: 12, marginTop: 5, color: '#2e7d32' }}>
          El PDF contenía texto no legible, por lo que se usó OCR para extraer el contenido.
        </div>
      )}
    </div>
    <p><strong>Páginas procesadas:</strong> {pdfResult.total_pages}</p>
    <details style={{ marginBottom: 15 }}>
      <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
        Ver texto extraído (primeros 500 caracteres)
      </summary>
      <div style={{ 
        backgroundColor: 'white', 
        padding: 10, 
        border: '1px solid #ccc',
        maxHeight: 200,
        overflow: 'auto',
        fontFamily: 'monospace',
        fontSize: 12,
        marginTop: 10
      }}>
        {pdfResult.text}
      </div>
    </details>
    <h4 style={{ marginTop: 20 }}>Transacciones detectadas por AI:</h4>
    {Array.isArray(pdfResult.transactions) && pdfResult.transactions.length > 0 ? (
      <div>
        <p style={{ color: '#666', fontSize: 14 }}>
          Se encontraron {pdfResult.transactions.length} transacciones en el PDF.
        </p>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 10 }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: 8, border: '1px solid #ddd' }}>Fecha operación</th>
              <th style={{ padding: 8, border: '1px solid #ddd' }}>Fecha cargo</th>
              <th style={{ padding: 8, border: '1px solid #ddd' }}>Descripción</th>
              <th style={{ padding: 8, border: '1px solid #ddd' }}>Monto</th>
            </tr>
          </thead>
          <tbody>
            {pdfResult.transactions.map((txn: ExtractedTransaction, idx: number) => (
              <tr key={idx}>
                <td style={{ padding: 8, border: '1px solid #ddd' }}>{txn.fecha_operacion}</td>
                <td style={{ padding: 8, border: '1px solid #ddd' }}>{txn.fecha_cargo}</td>
                <td style={{ padding: 8, border: '1px solid #ddd' }}>{txn.descripcion}</td>
                <td style={{ padding: 8, border: '1px solid #ddd', color: (() => { const montoNum = typeof txn.monto === 'number' ? txn.monto : parseFloat(txn.monto.toString()); return montoNum < 0 ? 'red' : 'green'; })() }}>
                  {formatCurrency(Math.abs(typeof txn.monto === 'number' ? txn.monto : parseFloat(txn.monto.toString())))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div style={{ 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffeaa7', 
        padding: 15, 
        borderRadius: 5,
        color: '#856404'
      }}>
        <strong>⚠️ No se detectaron transacciones</strong>
        <p style={{ margin: '5px 0 0 0', fontSize: 14 }}>
          Esto puede deberse a:
        </p>
        <ul style={{ margin: '5px 0 0 20px', fontSize: 14 }}>
          <li>El PDF no contiene un estado de cuenta bancario</li>
          <li>El formato del PDF es muy diferente al esperado</li>
          <li>La calidad del texto extraído no es suficiente</li>
        </ul>
      </div>
    )}
    <div style={{ marginTop: 20 }}>
      <button 
        onClick={() => setShowPdfUpload(false)}
        style={{ 
          backgroundColor: '#6c757d', 
          color: 'white', 
          border: 'none', 
          padding: '10px 20px', 
          borderRadius: 5,
          cursor: 'pointer',
          marginRight: 10
        }}
      >
        Cerrar
      </button>
      {Array.isArray(pdfResult.transactions) && pdfResult.transactions.length > 0 && (
        <button 
          onClick={() => handleSaveTransactions(pdfResult.transactions!)}
          disabled={savingTransactions}
          style={{ 
            backgroundColor: savingTransactions ? '#6c757d' : '#28a745', 
            color: 'white', 
            border: 'none', 
            padding: '10px 20px', 
            borderRadius: 5,
            cursor: savingTransactions ? 'not-allowed' : 'pointer'
          }}
        >
          {savingTransactions ? '⏳ Guardando...' : `💾 Guardar ${pdfResult.transactions.length} Transacciones`}
        </button>
      )}
    </div>
  </div>
)}

      {/* Pestañas por mes */}
      <div style={{ marginBottom: 20 }}>
        {/* Resumen del mes seleccionado */}
        {selectedMonth !== 'all' && transactionsByMonth[selectedMonth] && (
          <div style={{
            backgroundColor: '#e3f2fd',
            border: '1px solid #2196f3',
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <strong style={{ color: '#1976d2' }}>
                📊 Resumen de {transactionsByMonth[selectedMonth].name}
              </strong>
              <div style={{ fontSize: 14, color: '#424242', marginTop: 4 }}>
                {transactionsByMonth[selectedMonth].transactions.length} transacciones
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 14, color: '#d32f2f' }}>
                Gastos: {formatCurrency(
                  transactionsByMonth[selectedMonth].transactions
                    .filter((t: Transaction) => t.monto < 0)
                    .reduce((sum: number, t: Transaction) => sum + Math.abs(t.monto), 0)
                )}
              </div>
              <div style={{ fontSize: 14, color: '#388e3c' }}>
                Ingresos: {formatCurrency(
                  transactionsByMonth[selectedMonth].transactions
                    .filter((t: Transaction) => t.monto > 0)
                    .reduce((sum: number, t: Transaction) => sum + t.monto, 0)
                )}
              </div>
            </div>
          </div>
        )}
        
        <div style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          borderBottom: '2px solid #e9ecef',
          paddingBottom: 10
        }}>
          {/* Pestaña "Todas" */}
          <button
            onClick={() => setSelectedMonth('all')}
            style={{
              padding: '10px 16px',
              border: 'none',
              borderRadius: '8px 8px 0 0',
              backgroundColor: selectedMonth === 'all' ? '#007bff' : '#f8f9fa',
              color: selectedMonth === 'all' ? 'white' : '#495057',
              cursor: 'pointer',
              fontWeight: selectedMonth === 'all' ? 'bold' : 'normal',
              transition: 'all 0.2s ease',
              borderBottom: selectedMonth === 'all' ? '2px solid #007bff' : '2px solid transparent'
            }}
            onMouseEnter={(e) => {
              if (selectedMonth !== 'all') {
                e.currentTarget.style.backgroundColor = '#e9ecef';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedMonth !== 'all') {
                e.currentTarget.style.backgroundColor = '#f8f9fa';
              }
            }}
          >
            📅 Todas ({transactions.length})
          </button>
          
          {/* Pestañas por mes */}
          {monthTabs.map(monthKey => (
            <button
              key={monthKey}
              onClick={() => setSelectedMonth(monthKey)}
              style={{
                padding: '10px 16px',
                border: 'none',
                borderRadius: '8px 8px 0 0',
                backgroundColor: selectedMonth === monthKey ? '#007bff' : '#f8f9fa',
                color: selectedMonth === monthKey ? 'white' : '#495057',
                cursor: 'pointer',
                fontWeight: selectedMonth === monthKey ? 'bold' : 'normal',
                transition: 'all 0.2s ease',
                borderBottom: selectedMonth === monthKey ? '2px solid #007bff' : '2px solid transparent'
              }}
              onMouseEnter={(e) => {
                if (selectedMonth !== monthKey) {
                  e.currentTarget.style.backgroundColor = '#e9ecef';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedMonth !== monthKey) {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                }
              }}
            >
              📅 {transactionsByMonth[monthKey].name} ({transactionsByMonth[monthKey].transactions.length})
            </button>
          ))}
        </div>
      </div>

      {filteredTransactions.length === 0 ? (
        <div style={{
          padding: 20,
          textAlign: 'center',
          color: '#6c757d',
          backgroundColor: '#f8f9fa',
          borderRadius: 8,
          border: '1px solid #dee2e6'
        }}>
          {selectedMonth === 'all' 
            ? 'No hay transacciones que coincidan con los filtros.'
            : `No hay transacciones en ${transactionsByMonth[selectedMonth]?.name || 'este mes'} que coincidan con los filtros.`
          }
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: 10, textAlign: 'left', border: '1px solid #ddd' }}>Fecha</th>
              <th style={{ padding: 10, textAlign: 'left', border: '1px solid #ddd' }}>Descripción</th>
              <th style={{ padding: 10, textAlign: 'right', border: '1px solid #ddd' }}>Monto</th>
              <th style={{ padding: 10, textAlign: 'left', border: '1px solid #ddd' }}>Categoría</th>
              <th style={{ padding: 10, textAlign: 'center', border: '1px solid #ddd' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.map((transaction) => (
              <tr key={transaction.id}>
                <td style={{ padding: 10, border: '1px solid #ddd' }}>
                  {new Date(transaction.fecha).toLocaleDateString('es-ES')}
                </td>
                <td style={{ padding: 10, border: '1px solid #ddd' }}>
                  {transaction.descripcion}
                </td>
                <td style={{ 
                  padding: 10, 
                  textAlign: 'right',
                  border: '1px solid #ddd',
                  color: transaction.monto < 0 ? '#dc3545' : '#28a745',
                  fontWeight: 'bold'
                }}>
                  {formatCurrency(Math.abs(transaction.monto))}
                </td>
                <td style={{ padding: 10, border: '1px solid #ddd' }}>
                  {editingCategory === transaction.id ? (
                    <div style={{ minWidth: 150 }}>
                      <Select
                        value={{ value: getCategoryName(transaction.categoria), label: getCategoryName(transaction.categoria) }}
                        options={categoryOptions}
                        onChange={(option) => {
                          if (option) {
                            updateCategoryQuickly(transaction.id, option.value);
                          }
                        }}
                        onBlur={() => setEditingCategory(null)}
                        autoFocus
                        menuIsOpen
                        styles={{
                          control: (base) => ({
                            ...base,
                            minHeight: '32px',
                            fontSize: '12px',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            boxShadow: 'none',
                            '&:hover': {
                              borderColor: '#007bff'
                            }
                          }),
                          option: (base, state) => ({
                            ...base,
                            fontSize: '12px',
                            backgroundColor: state.isSelected ? '#007bff' : state.isFocused ? '#f8f9fa' : 'white',
                            color: state.isSelected ? 'white' : '#333',
                            '&:hover': {
                              backgroundColor: state.isSelected ? '#007bff' : '#e9ecef'
                            }
                          }),
                          menu: (base) => ({
                            ...base,
                            fontSize: '12px',
                            zIndex: 9999
                          }),
                          singleValue: (base) => ({
                            ...base,
                            fontSize: '12px'
                          })
                        }}
                      />
                    </div>
                  ) : (
                    <span 
                      style={{
                        backgroundColor: getCategoryColor(getCategoryName(transaction.categoria)),
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        display: 'inline-block'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                      onClick={() => setEditingCategory(transaction.id)}
                      title="Haz clic para editar categoría"
                    >
                      {getCategoryName(transaction.categoria)} ✏️
                    </span>
                  )}
                </td>
                <td style={{ padding: 10, textAlign: 'center', border: '1px solid #ddd' }}>
                  <button 
                    onClick={() => handleEdit(transaction)}
                    style={{ marginRight: 5, padding: '5px 10px', fontSize: '12px' }}
                  >
                    ✏️ Editar
                  </button>
                  <button 
                    onClick={() => handleDelete(transaction.id)}
                    style={{ 
                      backgroundColor: '#dc3545', 
                      color: 'white', 
                      border: 'none', 
                      padding: '5px 10px', 
                      borderRadius: 3,
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    🗑️ Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default Transactions;