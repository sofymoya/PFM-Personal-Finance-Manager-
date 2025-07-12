from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import crud, schemas, models, deps, auth
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import File, UploadFile
import PyPDF2
import io
import re
from datetime import datetime
from .auth import extract_transactions_with_ai
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import tempfile
import os

router = APIRouter()

# Usuario
@router.post('/usuarios/', response_model=schemas.User)
def crear_usuario(usuario: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    db_usuario = crud.get_user_by_email(db, usuario.email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    return crud.create_user(db, usuario)

@router.get('/usuarios/', response_model=List[schemas.User])
def listar_usuarios(db: Session = Depends(deps.get_db)):
    return crud.get_users(db)

# Categoría
# @router.get('/categorias/', response_model=List[schemas.Category])
# def listar_categorias(db: Session = Depends(deps.get_db)):
#     return crud.get_categories(db)

# @router.post('/categorias/', response_model=schemas.Category)
# def crear_categoria(categoria: schemas.CategoryCreate, db: Session = Depends(deps.get_db)):
#     return crud.create_category(db, categoria)

# Transacción
@router.get('/usuarios/{usuario_id}/transacciones/', response_model=List[schemas.Transaction])
def listar_transacciones(usuario_id: int, db: Session = Depends(deps.get_db)):
    return crud.get_transactions(db, usuario_id)

@router.post('/usuarios/{usuario_id}/transacciones/', response_model=schemas.Transaction)
def crear_transaccion(usuario_id: int, transaccion: schemas.TransactionCreate, db: Session = Depends(deps.get_db)):
    return crud.create_transaction(db, transaccion, usuario_id)

@router.put('/usuarios/{usuario_id}/transacciones/{transaccion_id}', response_model=schemas.Transaction)
def actualizar_transaccion(usuario_id: int, transaccion_id: int, transaccion: schemas.TransactionCreate, db: Session = Depends(deps.get_db)):
    return crud.update_transaction(db, transaccion_id, usuario_id, transaccion)

# @router.patch('/usuarios/{usuario_id}/transacciones/{transaccion_id}/categoria', response_model=schemas.Transaction)
# def actualizar_categoria_transaccion(usuario_id: int, transaccion_id: int, categoria: schemas.TransactionUpdateCategory, db: Session = Depends(deps.get_db)):
#     return crud.update_transaction_category(db, transaccion_id, usuario_id, categoria.category)

@router.delete('/usuarios/{usuario_id}/transacciones/{transaccion_id}')
def eliminar_transaccion(usuario_id: int, transaccion_id: int, db: Session = Depends(deps.get_db)):
    crud.delete_transaction(db, transaccion_id, usuario_id)
    return {"message": "Transacción eliminada"}

# Login
@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
    usuario = crud.get_user_by_email(db, form_data.username)
    if not usuario or not auth.verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    access_token = auth.create_access_token({"sub": str(usuario.id)})
    return {"access_token": access_token, "token_type": "bearer", "user_id": usuario.id}

@router.post('/usuarios/{usuario_id}/upload-pdf/')
async def upload_pdf(usuario_id: int, file: UploadFile = File(...), db: Session = Depends(deps.get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    try:
        # Leer el contenido del PDF
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        # Intentar extraer texto del PDF usando pdfplumber
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Si el texto está vacío o es muy corto, usar OCR
        if not text or len(text.strip()) < 100:
            print("Texto extraído muy corto o vacío, usando OCR...")
            text = extract_text_with_ocr(content)
        
        # Detectar texto ilegible (códigos como (cid:xxx), caracteres extraños)
        elif any(pattern in text for pattern in ['(cid:', 'ææł', 'ıæ', 'øı', 'łł', 'ææıı']):
            print("Texto extraído contiene códigos ilegibles, usando OCR...")
            text = extract_text_with_ocr(content)
        
        # Si aún no hay texto, devolver error
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF")
        
        # Limitar el texto para la AI - aumentado para capturar más transacciones
        max_length = 25000  # Aumentado de 10,000 a 25,000 caracteres
        short_text = text[:max_length]
        
        print(f"Texto extraído: {len(text)} caracteres")
        print(f"Texto enviado a AI: {len(short_text)} caracteres")
        
        # Extraer transacciones con AI
        transactions = extract_transactions_with_ai(short_text)
        
        # Si no se encontraron transacciones y el texto es largo, intentar con chunks
        if not transactions and len(text) > 25000:
            print("No se encontraron transacciones, intentando con chunks del texto...")
            chunks = [text[i:i+25000] for i in range(0, len(text), 20000)]  # Overlap de 5000 caracteres
            all_transactions = []
            
            for i, chunk in enumerate(chunks):
                print(f"Procesando chunk {i+1}/{len(chunks)}...")
                chunk_transactions = extract_transactions_with_ai(chunk)
                all_transactions.extend(chunk_transactions)
            
            # Eliminar duplicados basados en descripción y monto
            seen = set()
            unique_transactions = []
            for txn in all_transactions:
                key = (txn.get('descripcion', ''), txn.get('monto', 0))
                if key not in seen:
                    seen.add(key)
                    unique_transactions.append(txn)
            
            transactions = unique_transactions
            print(f"Transacciones encontradas con chunks: {len(transactions)}")
        
        return {
            "message": "PDF procesado exitosamente",
            "text": short_text,
            "total_pages": len(pdf.pages) if 'pdf' in locals() else "N/A",
            "transactions": transactions,
            "method": "OCR" if not text or len(text.strip()) < 100 else "PDF Text"
        }
        
    except Exception as e:
        print(f"Error procesando PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando PDF: {str(e)}")

def extract_text_with_ocr(pdf_content: bytes) -> str:
    """Extrae texto de un PDF usando OCR con Tesseract"""
    try:
        # Convertir PDF a imágenes
        images = convert_from_bytes(pdf_content)
        text = ""
        
        for i, image in enumerate(images):
            print(f"Procesando página {i+1} con OCR...")
            
            # Configurar Tesseract para español
            custom_config = r'--oem 3 --psm 6 -l spa'
            
            # Extraer texto de la imagen
            page_text = pytesseract.image_to_string(image, config=custom_config)
            text += page_text + "\n"
        
        return text
    except Exception as e:
        print(f"Error en OCR: {str(e)}")
        return ""