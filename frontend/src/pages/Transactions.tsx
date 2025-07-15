import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DepthFrame } from "../components/transactions/DepthFrame";
import { DepthFrameWrapper } from "../components/transactions/DepthFrameWrapper";
import { DivWrapper } from "../components/transactions/DivWrapper";
import { formatPesos } from '../utils/formatters';

export const Transactions = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="flex flex-col items-start relative bg-white">
      <div className="flex flex-col min-h-[800px] items-start relative self-stretch w-full flex-[0_0_auto] bg-white">
        <div className="flex flex-col items-start relative self-stretch w-full flex-[0_0_auto]">
          {/* Header with Navigation */}
          <div className="w-full border-b border-[#e5e8ea] px-10 py-3 flex items-center justify-between">
            <span className="font-bold text-lg text-[#111416]">FinTrack</span>
            
            {/* Navigation Buttons */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                🏠 Dashboard
              </button>
              <button
                onClick={() => navigate('/upload')}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
              >
                📄 Upload PDF
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                🚪 Logout
              </button>
            </div>
          </div>

          <DepthFrame />
          <DepthFrameWrapper />
          <DivWrapper />
        </div>
      </div>
    </div>
  );
};

export default Transactions; 