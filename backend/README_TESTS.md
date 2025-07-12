# Scripts de Prueba - PFM Backend

Este directorio contiene scripts para probar y validar la funcionalidad del backend de extracción de transacciones bancarias.

## 📋 Scripts Disponibles

### 1. `limpiar_db.py`
**Propósito:** Limpia todas las transacciones de la base de datos.

**Uso:**
```bash
source venv/bin/activate && python limpiar_db.py
```

**Funcionalidad:**
- Muestra el total de transacciones antes de limpiar
- Lista todos los usuarios en la base de datos
- Elimina todas las transacciones
- Verifica que la limpieza fue exitosa

### 2. `test_date_fix.py`
**Propósito:** Prueba específica para validar el fix de formato de fechas en Santander.

**Uso:**
```bash
source venv/bin/activate && python test_date_fix.py
```

**Funcionalidad:**
- Login con usuario de prueba
- Subida del PDF de Santander
- Validación de extracción y guardado de transacciones
- Verificación de que las fechas se procesan correctamente

### 3. `test_multi_bank.py`
**Propósito:** Script avanzado para probar múltiples bancos y PDFs.

**Uso:**
```bash
source venv/bin/activate && python test_multi_bank.py
```

**Funcionalidad:**
- Clase `TestMultiBank` para manejo de pruebas
- Soporte para múltiples casos de prueba
- Validación de banco detectado vs esperado
- Generación de reportes JSON con resultados
- Manejo robusto de errores

**Configuración de casos de prueba:**
```python
test_cases = [
    {
        "name": "Santander - Estado de cuenta abril 2025-2.pdf",
        "email": "prueba_front@correo.com",
        "password": "claveFront123",
        "pdf_path": "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf",
        "expected_bank": "Santander"
    },
    # Agregar más casos aquí...
]
```

### 4. `setup_test_environment.py`
**Propósito:** Script completo para configurar y ejecutar todo el entorno de pruebas.

**Uso:**
```bash
source venv/bin/activate && python setup_test_environment.py
```

**Funcionalidad:**
- Limpia la base de datos automáticamente
- Crea usuarios de prueba
- Verifica/inicia el backend si es necesario
- Ejecuta las pruebas
- Genera reportes completos

## 🚀 Flujo de Trabajo Recomendado

### Para desarrollo diario:
1. **Limpieza rápida:**
   ```bash
   python limpiar_db.py
   ```

2. **Prueba específica:**
   ```bash
   python test_date_fix.py
   ```

### Para validación completa:
1. **Configuración automática:**
   ```bash
   python setup_test_environment.py
   ```

### Para agregar nuevos bancos:
1. **Modificar `test_multi_bank.py`:**
   - Agregar nuevo caso de prueba
   - Especificar PDF y banco esperado
   - Ejecutar con `python test_multi_bank.py`

## 📊 Resultados y Logs

### Archivos generados:
- `test_results.json`: Resultados detallados de las pruebas
- Logs en consola con emojis para fácil identificación

### Métricas incluidas:
- Total de pruebas ejecutadas
- Pruebas exitosas vs fallidas
- Tasa de éxito
- Detalles por banco y PDF

## 🔧 Configuración

### Requisitos:
- Backend corriendo en `http://localhost:8000`
- Entorno virtual activado
- PDFs de prueba en `uploaded_pdfs/`
- Usuarios de prueba creados

### Variables de entorno:
- `BACKEND_URL`: URL del backend (default: `http://localhost:8000`)
- `TEST_USER_EMAIL`: Email del usuario de prueba
- `TEST_USER_PASSWORD`: Contraseña del usuario de prueba

## 🐛 Troubleshooting

### Backend no responde:
```bash
# Verificar si está corriendo
curl http://localhost:8000/

# Reiniciar si es necesario
pkill -f uvicorn
source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Error de autenticación:
- Verificar que el usuario de prueba existe
- Ejecutar `python create_user.py` si es necesario

### PDF no encontrado:
- Verificar que el archivo existe en `uploaded_pdfs/`
- Revisar permisos del archivo

## 📝 Notas de Desarrollo

### Agregar nuevos bancos:
1. Crear parser específico en `app/main.py`
2. Agregar caso de prueba en `test_multi_bank.py`
3. Probar con PDF real del banco
4. Validar extracción y guardado

### Mejorar logs:
- Usar emojis para identificación rápida
- Incluir timestamps en logs importantes
- Separar logs por nivel (INFO, ERROR, DEBUG)

### Optimizar rendimiento:
- Paralelizar pruebas cuando sea posible
- Cachear resultados de login
- Reutilizar sesiones HTTP 