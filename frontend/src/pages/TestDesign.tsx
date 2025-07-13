import React from 'react';

const TestDesign: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header de la página */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Prueba del Layout General
        </h1>
        <p className="text-gray-600">
          Esta página verifica que el layout con sidebar y header esté funcionando correctamente.
        </p>
      </div>

      {/* Cards de prueba */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1 - Sidebar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-sidebar rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">S</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Sidebar</h3>
              <p className="text-sm text-gray-500">Navegación lateral</p>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✅ Logo "PFM" como texto</li>
            <li>✅ Íconos de Heroicons</li>
            <li>✅ Colapsable en móvil</li>
            <li>✅ Navegación activa</li>
            <li>✅ Footer con usuario</li>
          </ul>
        </div>

        {/* Card 2 - Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">H</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Header</h3>
              <p className="text-sm text-gray-500">Barra superior</p>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✅ Título de la aplicación</li>
            <li>✅ Botón de menú móvil</li>
            <li>✅ Notificaciones</li>
            <li>✅ Avatar de usuario</li>
            <li>✅ Información del usuario</li>
          </ul>
        </div>

        {/* Card 3 - Layout */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">L</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Layout</h3>
              <p className="text-sm text-gray-500">Estructura general</p>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✅ Sidebar + Header + Content</li>
            <li>✅ Responsive design</li>
            <li>✅ Transiciones suaves</li>
            <li>✅ Colores del Figma</li>
            <li>✅ Tipografía Inter</li>
          </ul>
        </div>
      </div>

      {/* Sección de colores */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Paleta de Colores (Figma)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-primary rounded-lg mx-auto mb-2"></div>
            <p className="text-sm font-medium text-gray-900">Primary</p>
            <p className="text-xs text-gray-500">#2563eb</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-sidebar rounded-lg mx-auto mb-2"></div>
            <p className="text-sm font-medium text-gray-900">Sidebar</p>
            <p className="text-xs text-gray-500">#111827</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-background rounded-lg mx-auto mb-2 border border-gray-200"></div>
            <p className="text-sm font-medium text-gray-900">Background</p>
            <p className="text-xs text-gray-500">#f8fafc</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-accent rounded-lg mx-auto mb-2"></div>
            <p className="text-sm font-medium text-gray-900">Accent</p>
            <p className="text-xs text-gray-500">#fbbf24</p>
          </div>
        </div>
      </div>

      {/* Instrucciones */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">🎉 ¡Layout Implementado!</h3>
        <p className="text-blue-800 mb-4">
          El layout general está funcionando correctamente. Ahora puedes:
        </p>
        <ul className="space-y-1 text-blue-700 text-sm">
          <li>• Navegar entre páginas usando el sidebar</li>
          <li>• Ver el header con información del usuario</li>
          <li>• Probar la responsividad en diferentes tamaños</li>
          <li>• Verificar que los colores coincidan con el Figma</li>
        </ul>
      </div>
    </div>
  );
};

export default TestDesign; 