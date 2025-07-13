import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  user?: {
    name: string;
    email: string;
  };
  onLogout?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle, user, onLogout }) => {
  const location = useLocation();

  const navigation = [
    { 
      name: 'Dashboard', 
      href: '/dashboard', 
      symbol: '📊',
      description: 'Vista general de tus finanzas'
    },
    { 
      name: 'Transacciones', 
      href: '/transactions', 
      symbol: '📝',
      description: 'Gestiona tus transacciones'
    },
    { 
      name: 'Subir PDF', 
      href: '/upload', 
      symbol: '📤',
      description: 'Importa estados de cuenta'
    },
    { 
      name: 'Reportes', 
      href: '/reports', 
      symbol: '📈',
      description: 'Análisis y reportes'
    },
  ];

  const isActive = (href: string) => location.pathname === href;

  return (
    <>
      {/* Overlay para móvil */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white/80 backdrop-blur-xl border-r border-gray-200/50 z-50 transition-all duration-300 ease-in-out shadow-xl
        ${isOpen ? 'w-72' : 'w-20'} 
        lg:relative lg:translate-x-0
        ${!isOpen && 'lg:w-72'}
      `}>
        
        {/* Header del Sidebar */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200/50">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            {isOpen && (
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  PFM
                </span>
                <p className="text-xs text-gray-500">Finance Manager</p>
              </div>
            )}
          </div>

          {/* Botón de cerrar (móvil) */}
          <button
            onClick={onToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <span className="text-gray-600 font-bold text-lg">×</span>
          </button>
        </div>

        {/* Navegación */}
        <nav className="mt-6 px-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    group flex items-center px-3 py-3 rounded-xl transition-all duration-200 relative overflow-hidden
                    ${isActive(item.href) 
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' 
                      : 'text-gray-700 hover:bg-gray-50 hover:text-blue-600'
                    }
                  `}
                >
                  {/* Background gradient for active state */}
                  {isActive(item.href) && (
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 opacity-90"></div>
                  )}
                  
                  <div className="relative flex items-center w-full">
                    <span className={`text-lg flex-shrink-0 ${isActive(item.href) ? 'text-white' : 'text-gray-500 group-hover:text-blue-600'}`}>
                      {item.symbol}
                    </span>
                    {isOpen && (
                      <div className="ml-3 flex-1">
                        <span className={`font-medium ${isActive(item.href) ? 'text-white' : 'text-gray-900'}`}>
                          {item.name}
                        </span>
                        <p className={`text-xs ${isActive(item.href) ? 'text-blue-100' : 'text-gray-500'}`}>
                          {item.description}
                        </p>
                      </div>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        </nav>

        {/* User Profile Section */}
        {isOpen && user && (
          <div className="absolute bottom-20 left-0 right-0 p-4">
            <div className="bg-gray-50/50 rounded-xl p-4 border border-gray-200/50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">👤</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">
                    {user.name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {user.email}
                  </p>
                </div>
              </div>
              
              {/* Quick Actions */}
              <div className="mt-3 flex space-x-2">
                <button className="flex-1 flex items-center justify-center px-3 py-2 text-xs font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                  <span className="mr-1">⚙️</span>
                  Config
                </button>
                {onLogout && (
                  <button 
                    onClick={onLogout}
                    className="flex-1 flex items-center justify-center px-3 py-2 text-xs font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <span className="mr-1">🚪</span>
                    Salir
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Collapsed User Info */}
        {!isOpen && user && (
          <div className="absolute bottom-6 left-0 right-0 flex justify-center">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
              <span className="text-white font-bold text-sm">👤</span>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar; 