import React from "react";

export const DepthFrameWrapper = () => {
  return (
    <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto] bg-gray-50 px-6 py-4">
      <div className="flex items-center justify-between relative self-stretch w-full flex-[0_0_auto]">
        <div className="flex items-center gap-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Buscar transacciones..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              🔍
            </div>
          </div>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>Todas las cuentas</option>
            <option>Cuenta Principal</option>
            <option>Cuenta de Ahorros</option>
          </select>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>Todos los tipos</option>
            <option>Ingresos</option>
            <option>Gastos</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors">
            📊
          </button>
          <button className="px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors">
            📥
          </button>
        </div>
      </div>
    </div>
  );
}; 