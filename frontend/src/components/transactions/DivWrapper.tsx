
export const DivWrapper = () => {
  const mockTransactions = [
    {
      id: 1,
      date: "2024-01-15",
      description: "Supermercado Local",
      category: "Alimentación",
      amount: -85.50,
      type: "expense",
      account: "Cuenta Principal"
    },
    {
      id: 2,
      date: "2024-01-14",
      description: "Salario Enero",
      category: "Ingresos",
      amount: 2500.00,
      type: "income",
      account: "Cuenta Principal"
    },
    {
      id: 3,
      date: "2024-01-13",
      description: "Gasolina",
      category: "Transporte",
      amount: -45.00,
      type: "expense",
      account: "Cuenta Principal"
    },
    {
      id: 4,
      date: "2024-01-12",
      description: "Netflix",
      category: "Entretenimiento",
      amount: -15.99,
      type: "expense",
      account: "Cuenta Principal"
    },
    {
      id: 5,
      date: "2024-01-11",
      description: "Freelance Diseño",
      category: "Ingresos",
      amount: 300.00,
      type: "income",
      account: "Cuenta de Ahorros"
    }
  ];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto] bg-white px-6 py-4">
      <div className="relative self-stretch w-full flex-[0_0_auto]">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Fecha</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Descripción</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Categoría</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Cuenta</th>
                <th className="text-right py-3 px-4 font-medium text-gray-700">Monto</th>
                <th className="text-center py-3 px-4 font-medium text-gray-700">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {mockTransactions.map((transaction) => (
                <tr key={transaction.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {formatDate(transaction.date)}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                    {transaction.description}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {transaction.category}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {transaction.account}
                  </td>
                  <td className={`py-3 px-4 text-sm font-medium text-right ${
                    transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.type === 'income' ? '+' : '-'} {Math.abs(transaction.amount).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' })}
                  </td>
                  <td className="py-3 px-4 text-sm text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button className="text-blue-600 hover:text-blue-800 transition-colors">
                        ✏️
                      </button>
                      <button className="text-red-600 hover:text-red-800 transition-colors">
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="flex items-center justify-between w-full mt-6">
        <div className="text-sm text-gray-600">
          Mostrando 1-5 de 5 transacciones
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
            Anterior
          </button>
          <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded">
            1
          </button>
          <button className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50">
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}; 