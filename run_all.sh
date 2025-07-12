#!/bin/bash

echo "🚀 Iniciando PFM - Personal Finance Manager"
echo "=========================================="

# Función para limpiar procesos al salir
cleanup() {
    echo "🛑 Deteniendo todos los procesos..."
    pkill -f "uvicorn" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Verificar si estamos en el directorio correcto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Debes ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Iniciar backend
echo "🔧 Iniciando backend..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Esperar un momento para que el backend se inicie
sleep 3

# Verificar que el backend esté funcionando
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend iniciado correctamente en http://localhost:8000"
else
    echo "❌ Error: El backend no se pudo iniciar"
    exit 1
fi

# Iniciar frontend
echo "🎨 Iniciando frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Esperar un momento para que el frontend se inicie
sleep 5

# Verificar que el frontend esté funcionando
if curl -s http://localhost:5173/ > /dev/null 2>&1 || curl -s http://localhost:5174/ > /dev/null 2>&1 || curl -s http://localhost:5175/ > /dev/null 2>&1; then
    echo "✅ Frontend iniciado correctamente"
else
    echo "⚠️ Frontend puede estar iniciándose..."
fi

echo ""
echo "🎉 ¡PFM está listo!"
echo "📊 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173 (o 5174, 5175)"
echo ""
echo "Presiona Ctrl+C para detener todos los servicios"

# Mantener el script ejecutándose
wait 