export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Formatea un monto como pesos mexicanos sin el símbolo de moneda
 * @param amount - El monto a formatear (number)
 * @returns String formateado como 1,000.00
 */
export const formatAmount = (amount: number): string => {
  return new Intl.NumberFormat('es-MX', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Formatea un monto como pesos mexicanos con el símbolo $ personalizado
 * @param amount - El monto a formatear (number)
 * @returns String formateado como $1,000.00
 */
export const formatPesos = (amount: number): string => {
  return amount.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

export const formatDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export const formatShortDate = (date: string | Date): string => {
  return new Date(date).toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}; 