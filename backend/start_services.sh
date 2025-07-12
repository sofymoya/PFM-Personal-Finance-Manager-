#!/bin/bash
# Script para arrancar backend y frontend de PFM Cursor en background

# Navegar al directorio del script
cd "$(dirname "$0")/.."

# Matar procesos previos
pkill -f "uvicorn" 2>/dev/null

# Arrancar backend
cd backend
if [ ! -d "venv" ]; then
  echo "No existe el entorno virtual 'venv'. Por favor crea uno con 'python3 -m venv venv' y ejecuta 'pip install -r requirements.txt'"
  exit 1
fi
source venv/bin/activate
nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend iniciado (PID $BACKEND_PID) en http://localhost:8000/"
cd ..

# Arrancar frontend
cd frontend
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend iniciado (PID $FRONTEND_PID) en http://localhost:5173/ (o el puerto que indique Vite)"

cd ..

echo "Ambos servicios corriendo en background. Logs: backend/backend.log y frontend/frontend.log" 