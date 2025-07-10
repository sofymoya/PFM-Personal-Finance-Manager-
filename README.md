# PFM - Personal Finance Manager

Una aplicación web completa para gestionar finanzas personales, construida con FastAPI (backend) y React TypeScript (frontend).

## 🚀 Características

- **Autenticación de usuarios**: Registro e inicio de sesión seguro
- **Gestión de transacciones**: Agregar, editar y eliminar transacciones
- **Dashboard intuitivo**: Vista general de finanzas personales
- **API RESTful**: Backend robusto con FastAPI
- **Interfaz moderna**: Frontend responsive con React y TypeScript

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido para Python
- **SQLAlchemy**: ORM para manejo de base de datos
- **Pydantic**: Validación de datos y serialización
- **Alembic**: Migraciones de base de datos
- **Passlib**: Hashing de contraseñas
- **JWT**: Autenticación con tokens

### Frontend
- **React 18**: Biblioteca de interfaz de usuario
- **TypeScript**: Tipado estático para JavaScript
- **Vite**: Herramienta de construcción rápida
- **React Router**: Navegación entre páginas
- **Axios**: Cliente HTTP para llamadas a la API
- **Tailwind CSS**: Framework de CSS utilitario

## 📋 Requisitos Previos

- Python 3.8+
- Node.js 16+
- npm o yarn

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio-url>
cd PFM-Cursor
```

### 2. Configurar el Backend

```bash
# Navegar al directorio del backend
cd backend

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate
# En Windows:
# venv\Scripts\activate

# Instalar dependencias
pip install fastapi uvicorn sqlalchemy passlib[bcrypt] pydantic email-validator python-multipart alembic

# Ejecutar migraciones
alembic upgrade head

# Iniciar el servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configurar el Frontend

```bash
# Navegar al directorio del frontend
cd frontend

# Instalar dependencias
npm install

# Iniciar el servidor de desarrollo
npm run dev
```

## 🌐 Acceso a la Aplicación

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📁 Estructura del Proyecto

```
PFM-Cursor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # Punto de entrada de FastAPI
│   │   ├── models.py        # Modelos de SQLAlchemy
│   │   ├── schemas.py       # Esquemas de Pydantic
│   │   ├── crud.py          # Operaciones CRUD
│   │   ├── auth.py          # Autenticación y JWT
│   │   ├── deps.py          # Dependencias
│   │   ├── database.py      # Configuración de base de datos
│   │   └── routers.py       # Rutas de la API
│   ├── alembic/             # Migraciones de base de datos
│   └── requirements.txt     # Dependencias de Python
├── frontend/
│   ├── src/
│   │   ├── pages/           # Componentes de páginas
│   │   ├── services/        # Servicios de API
│   │   ├── utils/           # Utilidades
│   │   ├── App.tsx          # Componente principal
│   │   └── main.tsx         # Punto de entrada
│   ├── package.json         # Dependencias de Node.js
│   └── vite.config.ts       # Configuración de Vite
└── README.md
```

## 🔧 Configuración de Desarrollo

### Variables de Entorno

Crea un archivo `.env` en el directorio `backend/`:

```env
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///./database.db
```

### Base de Datos

La aplicación usa SQLite por defecto. Para usar PostgreSQL o MySQL, modifica la URL de la base de datos en `backend/app/database.py`.

## 📝 Uso

1. **Registro**: Crea una nueva cuenta en la página de registro
2. **Login**: Inicia sesión con tus credenciales
3. **Dashboard**: Visualiza tu resumen financiero
4. **Transacciones**: Agrega y gestiona tus transacciones

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas o preguntas, por favor abre un issue en el repositorio.

---

**¡Disfruta gestionando tus finanzas personales! 💰** 