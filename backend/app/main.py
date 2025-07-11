from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv
import pdfplumber
import openai
import re
from datetime import datetime
from sqlalchemy import extract, func
import pytesseract
from PIL import Image
import io

load_dotenv()

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from . import crud, models, schemas, auth
from .database import engine, get_db

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="PFM API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency para obtener el usuario actual
def get_current_user(db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth.verify_token(token)
    if token_data is None or token_data.email is None:
        raise credentials_exception
    
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# Rutas de autenticación
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Inicia sesión de un usuario"""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id
    }

# Rutas de transacciones (requieren autenticación)
@app.get("/transactions/", response_model=List[schemas.Transaction])
def read_transactions(
    skip: int = 0, 
    limit: int = 100, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las transacciones del usuario actual"""
    transactions = crud.get_transactions(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions

@app.post("/transactions/", response_model=schemas.Transaction)
def create_transaction(
    transaction: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva transacción"""
    return crud.create_transaction(db=db, transaction=transaction, user_id=current_user.id)

@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene una transacción específica"""
    transaction = crud.get_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.put("/transactions/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza una transacción"""
    updated_transaction = crud.update_transaction(
        db, transaction_id=transaction_id, user_id=current_user.id, transaction=transaction
    )
    if updated_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated_transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina una transacción"""
    success = crud.delete_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

@app.get("/transactions/filter", response_model=List[schemas.Transaction])
def filter_transactions(
    start_date: str = None,
    end_date: str = None,
    min_amount: float = None,
    max_amount: float = None,
    category: str = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene transacciones filtradas por fecha (DD-MM-YYYY), monto mínimo/máximo y categoría"""
    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    if start_date:
        start = datetime.strptime(start_date, "%d-%m-%Y").date()
        query = query.filter(models.Transaction.date >= start)
    if end_date:
        end = datetime.strptime(end_date, "%d-%m-%Y").date()
        query = query.filter(models.Transaction.date <= end)
    if min_amount is not None:
        query = query.filter(models.Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(models.Transaction.amount <= max_amount)
    if category:
        query = query.filter(models.Transaction.category == category)
    return query.order_by(models.Transaction.date.desc()).all()

@app.get("/transactions/summary/monthly")
def monthly_summary(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Devuelve totales mensuales de ingresos y gastos agrupados por mes y tipo (abono/cargo)"""
    results = db.query(
        extract('year', models.Transaction.date).label('year'),
        extract('month', models.Transaction.date).label('month'),
        func.sum(models.Transaction.amount).label('total'),
    ).filter(
        models.Transaction.user_id == current_user.id
    ).group_by('year', 'month').order_by('year', 'month').all()
    # Separar ingresos y gastos
    summary = []
    for row in results:
        summary.append({
            "year": int(row.year),
            "month": int(row.month),
            "total": float(row.total)
        })
    return summary

@app.get("/transactions/summary/category")
def category_summary(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Devuelve la proporción de gasto por categoría (solo gastos, amount negativo)"""
    results = db.query(
        models.Transaction.category,
        func.sum(models.Transaction.amount).label('total')
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.amount < 0
    ).group_by(models.Transaction.category).all()
    summary = []
    for row in results:
        summary.append({
            "category": row.category,
            "total": float(abs(row.total))  # Para gráfico de pastel, usar valor absoluto
        })
    return summary

@app.get("/transactions/summary/table")
def summary_table(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Devuelve una tabla resumen del total gastado por categoría y por mes (solo gastos)"""
    results = db.query(
        extract('year', models.Transaction.date).label('year'),
        extract('month', models.Transaction.date).label('month'),
        models.Transaction.category,
        func.sum(models.Transaction.amount).label('total')
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.amount < 0
    ).group_by('year', 'month', models.Transaction.category).order_by('year', 'month').all()
    summary = []
    for row in results:
        summary.append({
            "year": int(row.year),
            "month": int(row.month),
            "category": row.category,
            "total": float(abs(row.total))
        })
    return summary

# Función para procesar el PDF y extraer transacciones

def extract_text_with_ocr_fallback(pdf_path: str):
    """
    Extrae texto del PDF usando pdfplumber, y si el texto contiene códigos (cid:XXX),
    usa OCR como fallback para obtener texto legible.
    """
    with pdfplumber.open(pdf_path) as pdf:
        extracted_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        # Verificar si el texto contiene códigos (cid:XXX) que indican texto ilegible
        if "(cid:" in extracted_text:
            print("🔍 Texto extraído contiene códigos (cid:XXX). Usando OCR como fallback...")
            ocr_text = ""
            
            for page_num, page in enumerate(pdf.pages):
                # Convertir página a imagen
                img = page.to_image()
                img_bytes = img.original.convert('RGB')
                
                # Usar OCR para extraer texto
                try:
                    page_text = pytesseract.image_to_string(img_bytes, lang='spa')
                    ocr_text += page_text + "\n"
                    print(f"✅ OCR completado para página {page_num + 1}")
                except Exception as e:
                    print(f"❌ Error en OCR para página {page_num + 1}: {e}")
                    # Si OCR falla, mantener el texto original de esa página
                    page_original = page.extract_text() or ""
                    ocr_text += page_original + "\n"
            
            print("🔍 OCR completado. Usando texto extraído con OCR.")
            return ocr_text
        else:
            print("✅ Texto extraído es legible. No se necesita OCR.")
            return extracted_text

def process_bank_statement_pdf(file_path: str, api_key: str):
    """
    Procesa un estado de cuenta bancario en PDF y extrae transacciones.
    Retorna una lista de transacciones con los campos requeridos.
    """
    transactions = []
    banco = None
    
    # Extraer texto con OCR como fallback si es necesario
    extracted_text = extract_text_with_ocr_fallback(file_path)
    
    print("\n--- TEXTO EXTRAÍDO DEL PDF ---\n")
    print(extracted_text)
    print("\n--- FIN DEL TEXTO EXTRAÍDO ---\n")
    
    # Identificación simple del banco
    if "BBVA" in extracted_text:
        banco = "BBVA"
    elif "Santander" in extracted_text:
        banco = "Santander"
    elif "Banorte" in extracted_text:
        banco = "Banorte"
    elif "HSBC" in extracted_text:
        banco = "HSBC"
    else:
        banco = "Desconocido"
    
    # Extraer líneas de la tabla (ignorando encabezados)
    lines = extracted_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Múltiples patrones para diferentes formatos de transacciones
        patterns = [
            # Patrón original: 04-Jun-2025  04-Jun-2025  SU PAGO...  + $9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+\d{2}-[A-Za-z]{3}-\d{4}\s+(.+?)\s+([+-])\s*\$([\d,]+\.\d{2})",
            # Patrón simplificado: 04-Jun-2025  SU PAGO...  + $9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([+-])\s*\$([\d,]+\.\d{2})",
            # Patrón con espacios variables: 04-Jun-2025  SU PAGO...  +$9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([+-])\$([\d,]+\.\d{2})",
            # Patrón sin símbolo de peso: 04-Jun-2025  SU PAGO...  + 9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([+-])\s*([\d,]+\.\d{2})",
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                try:
                    fecha_operacion = match.group(1)
                    descripcion = match.group(2).strip()
                    signo = match.group(3)
                    monto_str = match.group(4).replace(",", "")
                    monto = float(monto_str)
                    tipo = "abono" if signo == "+" else "cargo"
                    if tipo == "cargo":
                        monto = -monto
                    
                    # Categorizar usando OpenAI con manejo de errores
                    try:
                        categoria = categorize_transaction_openai(descripcion, api_key)
                    except Exception as e:
                        print(f"Error categorizando transacción: {e}")
                        categoria = "sin_categoria"
                    
                    transactions.append({
                        "fecha_operacion": fecha_operacion,
                        "descripcion": descripcion,
                        "monto": monto,
                        "tipo": tipo,
                        "categoria": categoria
                    })
                    break  # Si encontramos un match, no necesitamos probar más patrones
                except (ValueError, IndexError) as e:
                    print(f"Error procesando línea: {line}, Error: {e}")
                    continue
    
    return {"banco": banco, "transacciones": transactions, "texto_extraido": extracted_text}

# Función para categorizar transacciones usando OpenAI

def categorize_transaction_openai(descripcion: str, api_key: str):
    try:
        openai.api_key = api_key
        prompt = f"""
        Categoriza la siguiente transacción bancaria en una sola palabra (por ejemplo: supermercado, transporte, restaurante, ingreso, etc.):\n\n"{descripcion}"\n\nCategoría: """
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3,
            temperature=0
        )
        categoria = response.choices[0].message.content.strip()
        return categoria
    except Exception as e:
        print(f"Error en categorización OpenAI: {e}")
        # Categorización básica basada en palabras clave
        descripcion_lower = descripcion.lower()
        if any(word in descripcion_lower for word in ['oxxo', 'seven', 'farmacia', 'gasolina', 'gas']):
            return "conveniencia"
        elif any(word in descripcion_lower for word in ['restaurante', 'pizza', 'hamburguesa', 'cafe']):
            return "restaurante"
        elif any(word in descripcion_lower for word in ['uber', 'taxi', 'transporte', 'metro']):
            return "transporte"
        elif any(word in descripcion_lower for word in ['pago', 'spei', 'transferencia', 'deposito']):
            return "ingreso"
        elif any(word in descripcion_lower for word in ['retiro', 'cajero', 'atm']):
            return "retiro"
        else:
            return "otros"

@app.post("/upload_pdf")
def upload_pdf(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sube un archivo PDF de estado de cuenta bancario y guarda las transacciones extraídas en la base de datos"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="No se encontró la API key de OpenAI")
    # Procesar el PDF y categorizar transacciones
    result = process_bank_statement_pdf(file_location, api_key)
    transacciones_guardadas = []
    for t in result["transacciones"]:
        # Mapear campos al esquema TransactionCreate
        try:
            transaction_data = schemas.TransactionCreate(
                description=t["descripcion"],
                amount=t["monto"],
                date=_parse_date(t["fecha_operacion"]),
                category=t["categoria"]
            )
            db_transaction = crud.create_transaction(db=db, transaction=transaction_data, user_id=current_user.id)
            transacciones_guardadas.append(db_transaction)
        except Exception as e:
            continue  # Si alguna transacción falla, sigue con las demás
    return {
        "filename": file.filename,
        "banco": result["banco"],
        "transacciones_guardadas": [
            {"id": tr.id, "description": tr.description, "amount": tr.amount, "date": tr.date.isoformat(), "category": tr.category}
            for tr in transacciones_guardadas
        ],
        "texto_extraido": result["texto_extraido"],
        "message": f"Archivo subido y {len(transacciones_guardadas)} transacciones guardadas en la base de datos"
    }

@app.post("/test_upload_pdf")
def test_upload_pdf(file: UploadFile = File(...)):
    """Endpoint de prueba para subir PDF sin autenticación - solo para testing"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    file_location = os.path.join(UPLOAD_DIR, f"test_{file.filename}")
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="No se encontró la API key de OpenAI")
    
    # Procesar el PDF y categorizar transacciones
    result = process_bank_statement_pdf(file_location, api_key)
    
    # Simular transacciones guardadas (sin guardar en BD)
    transacciones_simuladas = []
    for t in result["transacciones"]:
        transacciones_simuladas.append({
            "id": len(transacciones_simuladas) + 1,
            "description": t["descripcion"],
            "amount": t["monto"],
            "date": t["fecha_operacion"],
            "category": t["categoria"]
        })
    
    return {
        "filename": file.filename,
        "banco": result["banco"],
        "transacciones_extraidas": transacciones_simuladas,
        "texto_extraido": result["texto_extraido"],
        "message": f"Archivo procesado exitosamente. {len(transacciones_simuladas)} transacciones extraídas"
    }



def _parse_date(date_str: str):
    # Convierte '04-Jun-2025' a objeto date
    return datetime.strptime(date_str, "%d-%b-%Y").date()

# Ruta de prueba
@app.get("/")
def read_root():
    return {"message": "PFM API is running!"}
