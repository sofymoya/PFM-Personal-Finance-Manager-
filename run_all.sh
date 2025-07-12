#!/bin/bash

# Script para levantar backend y frontend en paralelo
# Uso: bash run_all.sh

set -e

# Ruta absoluta del proyecto
ROOT_DIR="$(cd "$(dirname "$0")"; pwd)"

# Función para levantar el backend
run_backend() {
  echo "\n🚀 Levantando backend..."
  cd "$ROOT_DIR/backend"
  # Detectar entorno virtual
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d ".venv" ]; then
    source .venv/bin/activate
  else
    echo "❌ No se encontró entorno virtual en backend. Ejecuta 'python3 -m venv venv' y 'pip install -r requirements.txt' primero."
    exit 1
  fi
  exec python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Función para levantar el frontend
run_frontend() {
  echo "\n🚀 Levantando frontend..."
  cd "$ROOT_DIR/frontend"
  if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias de frontend..."
    npm install
  fi
  exec npm run dev
}

# Lanzar ambos en paralelo con logs separados
(run_backend 2>&1 | sed 's/^/[BACKEND] /') &
(run_frontend 2>&1 | sed 's/^/[FRONTEND] /') &

# Esperar a que ambos terminen
wait 