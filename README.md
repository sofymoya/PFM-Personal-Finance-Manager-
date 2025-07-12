# PFM - Personal Finance Manager

Sistema de gestión financiera personal que permite extraer y analizar transacciones bancarias desde estados de cuenta en PDF.

## 🚀 Inicio Rápido

### Opción 1: Script Automatizado (Recomendado)
```bash
# Desde la raíz del proyecto
./run_all.sh
```

Este comando levanta automáticamente:
- **Backend**: Puerto 8000 (con entorno virtual detectado automáticamente)
- **Frontend**: Puerto 5173 (o el siguiente disponible)

### Opción 2: Manual
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # o source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

## 📋 Características

- **Extracción automática** de transacciones desde PDFs bancarios
- **Soporte multi-banco**: Santander, HSBC, BBVA, Banorte
- **OCR inteligente** para PDFs escaneados
- **Categorización automática** de transacciones
- **Interfaz web moderna** con React + TypeScript
- **API REST** con FastAPI
- **Base de datos SQLite** con SQLAlchemy

## 🏗️ Estructura del Proyecto

```
PFM Cursor/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py         # Endpoints principales
│   │   ├── models.py       # Modelos de base de datos
│   │   ├── auth.py         # Autenticación
│   │   └── ...
│   ├── requirements.txt    # Dependencias Python
│   ├── test_*.py          # Scripts de prueba
│   └── README_TESTS.md    # Documentación de pruebas
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── pages/         # Componentes de página
│   │   ├── services/      # Servicios API
│   │   └── ...
│   └── package.json       # Dependencias Node.js
├── run_all.sh             # Script de automatización
└── README.md              # Este archivo
```

## 🛠️ Instalación

### Prerrequisitos
- Python 3.8+
- Node.js 16+
- npm o yarn

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## 🧪 Pruebas

### Scripts de Prueba Disponibles
```bash
cd backend

# Limpiar base de datos de pruebas
python limpiar_db.py

# Probar extracción de múltiples bancos
python test_multi_bank.py

# Probar configuración completa
python setup_test_environment.py
```

Ver `backend/README_TESTS.md` para documentación detallada.

## 🔧 Configuración

### Variables de Entorno
Crear archivo `.env` en `backend/`:
```env
OPENAI_API_KEY=tu_api_key_aqui
SECRET_KEY=tu_secret_key_aqui
```

### Base de Datos
La base de datos SQLite se crea automáticamente en `backend/app.db`

## 📖 Uso

1. **Iniciar el sistema**: `./run_all.sh`
2. **Abrir navegador**: `http://localhost:5173`
3. **Registrarse/Iniciar sesión**
4. **Subir PDF** de estado de cuenta
5. **Revisar transacciones** extraídas

## 🏦 Bancos Soportados

- **Santander**: Extracción completa con OCR
- **HSBC**: Parser específico + AI fallback
- **BBVA**: Parser estándar
- **Banorte**: Parser estándar
- **Otros**: AI fallback universal

## 🔍 Troubleshooting

### Error: "Address already in use"
```bash
pkill -f "uvicorn"
./run_all.sh
```

### Error: "No module named uvicorn"
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "npm run dev not found"
```bash
cd frontend
npm install
npm run dev
```

## 📝 Logs

Los logs se muestran con prefijos:
- `[BACKEND]` - Servidor FastAPI
- `[FRONTEND]` - Servidor Vite

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles. 