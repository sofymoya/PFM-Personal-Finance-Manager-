import React from "react";

export const DepthFrame = () => {
  return (
    <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto] bg-white">
      <div className="flex items-center justify-between relative self-stretch w-full flex-[0_0_auto] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-gray-900">Transacciones</div>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Nueva Transacción
          </button>
        </div>
      </div>
    </div>
  );
}; 