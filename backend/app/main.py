from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
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
from .agentic_extractor import AgenticDocumentExtractor

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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
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
    usa OCR mejorado como fallback para obtener texto legible.
    """
    print(f"📄 Iniciando extracción de texto de: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 PDF abierto correctamente. Páginas: {len(pdf.pages)}")
            
            # Intentar extracción normal primero
    extracted_text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
                    print(f"✅ Página {i+1}: {len(page_text)} caracteres extraídos")
                else:
                    print(f"⚠️ Página {i+1}: No se pudo extraer texto")
            
            # Verificar si el texto contiene códigos (cid:XXX) que indican texto ilegible
            if not extracted_text.strip():
                print("❌ No se pudo extraer texto del PDF. Usando OCR...")
                return _extract_with_ocr(pdf)
            elif "(cid:" in extracted_text:
                print("🔍 Texto extraído contiene códigos (cid:XXX). Usando OCR mejorado como fallback...")
                return _extract_with_ocr(pdf)
            else:
                print(f"✅ Texto extraído exitosamente: {len(extracted_text)} caracteres")
                # Debug: mostrar primeras líneas
                lines = extracted_text.split('\n')[:5]
                print("📄 Primeras líneas del texto extraído:")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"   {i+1}: {line.strip()}")
                return extracted_text
                
    except Exception as e:
        print(f"❌ Error abriendo PDF: {e}")
        return ""

def _extract_with_ocr(pdf):
    """
    Extrae texto usando OCR cuando la extracción normal falla.
    """
    ocr_text = ""
    
    for page_num, page in enumerate(pdf.pages):
        print(f"🔍 Procesando página {page_num + 1} con OCR...")
        
        try:
            # Convertir página a imagen con mejor resolución
            img = page.to_image(resolution=300)  # Aumentar resolución
            img_bytes = img.original.convert('RGB')
            
            # Preprocesar imagen para mejorar OCR
            processed_img = preprocess_image_for_ocr(img_bytes)
            
            # Usar OCR mejorado para extraer texto
            custom_config = r'--oem 3 --psm 6 -l spa+eng --dpi 300'
            page_text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            # Limpiar y mejorar el texto extraído
            cleaned_text = clean_ocr_text(page_text)
            ocr_text += cleaned_text + "\n"
            print(f"✅ OCR completado para página {page_num + 1}: {len(cleaned_text)} caracteres")
            
            # Debug: mostrar primeras líneas del texto extraído
            lines = cleaned_text.split('\n')[:3]
            print(f"📄 Primeras líneas página {page_num + 1}:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"   {i+1}: {line.strip()}")
                    
        except Exception as e:
            print(f"❌ Error en OCR para página {page_num + 1}: {e}")
            # Si OCR falla, mantener el texto original de esa página
            page_original = page.extract_text() or ""
            ocr_text += page_original + "\n"
    
    print(f"🔍 OCR completado. Total: {len(ocr_text)} caracteres")
    return ocr_text

def preprocess_image_for_ocr(image):
    """
    Preprocesa la imagen para mejorar la calidad del OCR.
    """
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
    import cv2
    
    # Convertir PIL Image a numpy array para OpenCV
    img_array = np.array(image)
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Aplicar filtro bilateral para reducir ruido manteniendo bordes
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Aplicar umbral adaptativo para mejorar contraste
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Aplicar morfología para limpiar el texto
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Convertir de vuelta a PIL Image
    processed_img = Image.fromarray(cleaned)
    
    # Aplicar mejoras adicionales con PIL
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(processed_img)
    processed_img = enhancer.enhance(1.5)
    
    # Aumentar nitidez
    enhancer = ImageEnhance.Sharpness(processed_img)
    processed_img = enhancer.enhance(1.2)
    
    return processed_img

def clean_ocr_text(text):
    """
    Limpia y mejora el texto extraído por OCR.
    """
    import re
    
    # Dividir en líneas
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Limpiar caracteres extraños comunes en OCR
        cleaned = line.strip()
        
        # Corregir errores comunes de OCR
        cleaned = re.sub(r'[|]{2,}', '|', cleaned)  # Múltiples pipes
        cleaned = re.sub(r'[0]{3,}', '000', cleaned)  # Múltiples ceros
        cleaned = re.sub(r'[l]{2,}', 'll', cleaned)  # Múltiples l's
        cleaned = re.sub(r'[I]{2,}', 'II', cleaned)  # Múltiples I's
        
        # Corregir caracteres mal interpretados específicos que vemos en los logs
        char_replacements = {
            '0': '0', 'O': '0', 'o': '0',  # Normalizar ceros
            'l': '1', 'I': '1', '|': '1',  # Normalizar unos
            'S': '5', 's': '5',  # Normalizar cincos
            'G': '6', 'g': '6',  # Normalizar seises
            'B': '8', 'b': '8',  # Normalizar ochos
            '1': '1',  # Mantener unos
            '2': '2',  # Mantener doses
            '3': '3',  # Mantener treses
            '4': '4',  # Mantener cuatros
            '5': '5',  # Mantener cincos
            '6': '6',  # Mantener seises
            '7': '7',  # Mantener sietes
            '8': '8',  # Mantener ochos
            '9': '9',  # Mantener nueves
        }
        
        # Corregir caracteres específicos que vemos en los logs
        # Ejemplo: "1a5e5oria1@1condu5ef1.1gob1.1mx1" -> "asesoria@condufef.gob.mx"
        cleaned = re.sub(r'1a5e5oria1@1condu5ef1\.1gob1\.1mx1', 'asesoria@condufef.gob.mx', cleaned)
        cleaned = re.sub(r'5UPAG0', 'SUPAGO', cleaned)
        cleaned = re.sub(r'5PE1', 'SPEI', cleaned)
        cleaned = re.sub(r'5PE1A', 'SPEIA', cleaned)
        cleaned = re.sub(r'M00H680201JG0', 'MOOH680201JGO', cleaned)
        cleaned = re.sub(r'V1VAAER0BU5', 'VIVAAEROBUS', cleaned)
        cleaned = re.sub(r'RE5T', 'REST', cleaned)
        cleaned = re.sub(r'ARB0_', 'ARBO', cleaned)
        cleaned = re.sub(r'51H', 'SIH', cleaned)
        cleaned = re.sub(r'V1VA', 'VIVA', cleaned)
        cleaned = re.sub(r'C1B', 'CIB', cleaned)
        
        # Corregir patrones de caracteres repetidos
        cleaned = re.sub(r'1{2,}', '11', cleaned)  # Múltiples unos
        cleaned = re.sub(r'5{2,}', '55', cleaned)  # Múltiples cincos
        
        # Eliminar líneas muy cortas o que parezcan ruido
        if len(cleaned) > 2 and not re.match(r'^[^\w]*$', cleaned):
            cleaned_lines.append(cleaned)
    
    return '\n'.join(cleaned_lines)

def ocr_region_with_multiple_methods(image):
    """
    Ejecuta OCR en una imagen usando varios modos PSM de Tesseract y EasyOCR.
    Devuelve un diccionario con los resultados.
    """
    import pytesseract
    import easyocr
    import numpy as np
    from PIL import Image
    
    results = {}
    # Tesseract PSM modes
    psm_modes = [4, 6, 11]
    for psm in psm_modes:
        config = f'--oem 3 --psm {psm} -l spa+eng --dpi 300'
        text = pytesseract.image_to_string(image, config=config)
        results[f'tesseract_psm_{psm}'] = text
    
    # EasyOCR
    try:
        reader = easyocr.Reader(['es', 'en'], gpu=False)
        # Convert PIL image to numpy array
        img_np = np.array(image)
        easyocr_result = reader.readtext(img_np, detail=0, paragraph=True)
        easyocr_text = '\n'.join(easyocr_result)
        results['easyocr'] = easyocr_text
    except Exception as e:
        results['easyocr'] = f"[EasyOCR error: {e}]"
    return results

def extract_transaction_regions(pdf_path: str):
    """
    Extrae texto específicamente de regiones que probablemente contengan transacciones.
    Para cada región, ejecuta OCR con varios métodos y muestra los resultados.
    """
    with pdfplumber.open(pdf_path) as pdf:
        transaction_text = ""
        
        for page_num, page in enumerate(pdf.pages):
            print(f"🔍 Analizando página {page_num + 1} para regiones de transacciones...")
            width = page.width
            height = page.height
            center_region = page.crop((width * 0.1, height * 0.3, width * 0.9, height * 0.8))
            bottom_region = page.crop((width * 0.1, height * 0.7, width * 0.9, height * 0.95))
            regions_to_check = [
                ("central", center_region),
                ("inferior", bottom_region)
            ]
            for region_name, region in regions_to_check:
                try:
                    region_text = region.extract_text()
                    if not region_text or "(cid:" in region_text:
                        img = region.to_image(resolution=300)
                        img_bytes = img.original.convert('RGB')
                        processed_img = preprocess_image_for_ocr(img_bytes)
                        # Multi-PSM + EasyOCR
                        ocr_results = ocr_region_with_multiple_methods(processed_img)
                        for method, text in ocr_results.items():
                            print(f"\n--- {method.upper()} {region_name.upper()} PÁGINA {page_num + 1} ---")
                            lines = text.split('\n')[:10]
                            for i, line in enumerate(lines):
                                if line.strip():
                                    print(f"   {i+1}: {line.strip()}")
                        # Use the best result (for now, just pick Tesseract PSM 6)
                        region_text = ocr_results.get('tesseract_psm_6', '')
                    if region_text and region_text.strip():
                        transaction_text += f"\n--- REGIÓN {region_name.upper()} PÁGINA {page_num + 1} ---\n"
                        transaction_text += region_text + "\n"
                        print(f"✅ Texto extraído de región {region_name} en página {page_num + 1}")
                except Exception as e:
                    print(f"❌ Error procesando región {region_name} en página {page_num + 1}: {e}")
                    continue
        return transaction_text

def process_bank_statement_pdf(file_path: str, api_key: str) -> Dict[str, Any]:
    """
    Process a bank statement PDF and extract transactions using agentic extraction.
    """
    print(f"📄 Procesando PDF: {file_path}")
    
    # Extract text from PDF
    extracted_text = extract_text_with_ocr_fallback(file_path)

    # Guardar el texto extraído para depuración
    debug_txt_path = file_path + ".ocr.txt"
    with open(debug_txt_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    print(f"📝 Texto extraído guardado en: {debug_txt_path}")
    print(f"--- INICIO TEXTO EXTRAÍDO ---\n{extracted_text[:1000]}\n--- FIN TEXTO EXTRAÍDO ---")
    
    if not extracted_text.strip():
        print("❌ No se pudo extraer texto del PDF")
        return {
            "banco": "Desconocido",
            "transacciones": [],
            "texto_extraido": ""
        }
    
    # Detect bank
    banco = detect_bank(extracted_text)
    print(f"🏦 Banco detectado: {banco}")
    
    # Use agentic extraction as primary method
    print("🤖 Usando extractor agéntico para extracción inteligente...")
    try:
        extractor = AgenticDocumentExtractor(api_key)
        transactions = extractor.extract_transactions(extracted_text, banco)
        
        if transactions:
            print(f"✅ Extractor agéntico encontró {len(transactions)} transacciones")
            return {
                "banco": banco,
                "transacciones": transactions,
                "texto_extraido": extracted_text
            }
        else:
            print("⚠️ Extractor agéntico no encontró transacciones, intentando métodos alternativos...")
            
    except Exception as e:
        print(f"❌ Error con extractor agéntico: {e}")
        print("🔄 Fallback a métodos tradicionales...")
    
    # Fallback to traditional methods if agentic extraction fails
    return _fallback_extraction(extracted_text, banco, api_key)

def _fallback_extraction(extracted_text: str, banco: str, api_key: str) -> Dict[str, Any]:
    """
    Fallback extraction using traditional methods.
    """
    # Try specific bank parsers first
    if banco == "HSBC":
        print("🏦 Usando parser específico para HSBC...")
        transactions = extract_hsbc_transactions(extracted_text)
        if transactions:
            return {
                "banco": banco,
                "transacciones": transactions,
                "texto_extraido": extracted_text
            }
    elif banco == "Santander":
        print("🏦 Usando parser específico para Santander...")
        transactions = extract_santander_transactions(extracted_text)
        if transactions:
            return {
                "banco": banco,
                "transacciones": transactions,
                "texto_extraido": extracted_text
            }
    
    # Try standard parser
    print("🏦 Usando parser estándar...")
    transactions = extract_standard_transactions(extracted_text)
    
    if transactions:
        return {
            "banco": banco,
            "transacciones": transactions,
            "texto_extraido": extracted_text
        }
    
    # Final fallback: AI method with better token management
    print("🤖 Usando AI fallback con mejor manejo de tokens...")
    try:
        from .auth import extract_transactions_with_ai
        ai_transactions = extract_transactions_with_ai(extracted_text)
        if ai_transactions:
            print(f"🤖 AI mejorado encontró {len(ai_transactions)} transacciones")
            return {
                "banco": banco,
                "transacciones": ai_transactions,
                "texto_extraido": extracted_text
            }
    except Exception as e:
        print(f"❌ Error con AI fallback mejorado: {e}")
    
    print("❌ No se pudieron extraer transacciones con ningún método")
    return {
        "banco": banco,
        "transacciones": [],
        "texto_extraido": extracted_text
    }

def _deduplicate_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina transacciones duplicadas basándose en fecha, descripción y monto.
    """
    seen = set()
    unique_transactions = []
    
    for transaction in transactions:
        # Crear una clave única para cada transacción
        key = (
            transaction.get('fecha_operacion', ''),
            transaction.get('descripcion', ''),
            transaction.get('monto', 0)
        )
        
        if key not in seen:
            seen.add(key)
            unique_transactions.append(transaction)
    
    return unique_transactions

# Función para categorizar transacciones usando OpenAI

def categorize_transaction_openai(descripcion: str, api_key: str):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    prompt = f"""
    Categoriza la siguiente transacción bancaria en una sola palabra (por ejemplo: supermercado, transporte, restaurante, ingreso, etc.):\n\n"{descripcion}"\n\nCategoría: """
        response = client.chat.completions.create(
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
    transactions = result.get("transacciones", [])
    banco = result.get("banco", "Desconocido")
    transacciones_guardadas = []
    
    for t in transactions:
        # Validar que t sea un diccionario válido
        if not isinstance(t, dict):
            print(f"❌ Transacción no es un diccionario: {type(t)} - {t}")
            continue
            
        # Validar campos requeridos
        if not all(key in t for key in ['descripcion', 'monto', 'fecha_operacion', 'categoria']):
            print(f"❌ Transacción faltan campos requeridos: {t}")
            continue
            
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
            print(f"Error guardando transacción: {e}")
            print(f"Transacción problemática: {t}")
            continue  # Si alguna transacción falla, sigue con las demás
    
    return {
        "filename": file.filename,
        "banco": banco,
        "transacciones_guardadas": [
            {"id": tr.id, "description": tr.description, "amount": tr.amount, "date": tr.date.isoformat(), "category": tr.category}
            for tr in transacciones_guardadas
        ],
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
    transactions = process_bank_statement_pdf(file_location, api_key)
    
    # Detectar banco del texto extraído
    extracted_text = ""
    try:
        with open(file_location, "rb") as f:
            import pdfplumber
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
    except Exception as e:
        print(f"Error extrayendo texto para detección de banco: {e}")
    
    # Detectar banco
    banco = detect_bank(extracted_text)
    
    # Simular transacciones guardadas (sin guardar en BD)
    transacciones_simuladas = []
    for t in transactions:
        transacciones_simuladas.append({
            "id": len(transacciones_simuladas) + 1,
            "description": t["descripcion"],
            "amount": t["monto"],
            "date": t["fecha_operacion"],
            "category": t["categoria"]
        })
    
    return {
        "filename": file.filename,
        "banco": banco,
        "transacciones_extraidas": transacciones_simuladas,
        "texto_extraido": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
        "message": f"Archivo procesado exitosamente. {len(transacciones_simuladas)} transacciones extraídas"
    }



def _parse_date(date_str: str):
    # Convierte '04-Jun-2025' o '04-ABR-2025' a objeto date
    try:
        # Primero intentar con el formato original
    return datetime.strptime(date_str, "%d-%b-%Y").date()
    except ValueError:
        # Si falla, intentar con formato en mayúsculas (como ABR, ENE, FEB, etc.)
        # Mapear abreviaciones en mayúsculas a formato estándar
        month_mapping = {
            'ENE': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'ABR': 'Apr',
            'MAY': 'May', 'JUN': 'Jun', 'JUL': 'Jul', 'AGO': 'Aug',
            'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DIC': 'Dec'
        }
        
        for esp_month, eng_month in month_mapping.items():
            if esp_month in date_str:
                date_str_fixed = date_str.replace(esp_month, eng_month)
                return datetime.strptime(date_str_fixed, "%d-%b-%Y").date()
        
        # Si aún falla, intentar con formato numérico DD-MM-YYYY
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except ValueError:
            # Último intento: formato DD/MM/YYYY
            return datetime.strptime(date_str, "%d/%m/%Y").date()

def detect_bank(text: str) -> str:
    """
    Detecta el banco a partir del texto extraído, priorizando coincidencias exactas y robustas.
    """
    text_upper = text.upper()
    # Prioridad: Santander > BBVA > HSBC > Banorte > Banamex > Banregio
    if "SANTANDER" in text_upper:
        return "Santander"
    elif "BBVA" in text_upper:
        return "BBVA"
    elif "HSBC" in text_upper:
        return "HSBC"
    elif "BANORTE" in text_upper:
        return "Banorte"
    elif "BANAMEX" in text_upper or "CITIBANAMEX" in text_upper:
        return "Banamex"
    elif "BANREGIO" in text_upper:
        return "Banregio"
    else:
        return "Desconocido"

def extract_standard_transactions(text: str) -> List[Dict[str, Any]]:
    """
    Extract transactions using standard patterns.
    """
    transactions = []
    lines = text.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Multiple patterns for different transaction formats
        patterns = [
            # Original pattern: 04-Jun-2025  04-Jun-2025  SU PAGO...  + $9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+\d{2}-[A-Za-z]{3}-\d{4}\s+(.+?)\s+([+-])\s*\\$([\d,]+\.\d{2})",
            # Simplified pattern: 04-Jun-2025  SU PAGO...  + $9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([+-])\s*\\$([\d,]+\.\d{2})",
            # Pattern with variable spaces: 04-Jun-2025  SU PAGO...  +$9,153.00
            r"(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([+-])\\$([\d,]+\.\d{2})",
            # Pattern without peso symbol: 04-Jun-2025  SU PAGO...  + 9,153.00
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
                    
                    transactions.append({
                        "fecha_operacion": fecha_operacion,
                        "descripcion": descripcion,
                        "monto": monto,
                        "tipo": tipo,
                        "categoria": "sin_categoria"
                    })
                    break  # If we found a match, don't try more patterns
                except (ValueError, IndexError) as e:
                    print(f"Error procesando línea: {line}, Error: {e}")
                    continue
                    
    return transactions

def extract_hsbc_transactions(extracted_text: str) -> List[dict]:
    """
    Extrae transacciones de HSBC de líneas OCR, ultra-tolerante a errores de OCR.
    """
    import re
    transactions = []
    
    # Validar que el texto no sea None o vacío
    if not extracted_text or not isinstance(extracted_text, str):
        print("❌ Texto extraído es None o no es string")
        return transactions
    
    lines = extracted_text.split('\n')
    
    print("🔍 Buscando transacciones en texto HSBC...")
    
    # Limpiar y normalizar el texto
    cleaned_lines = []
    for line in lines:
        # Validar que la línea no sea None
        if line is None:
            continue
            
        # Normalizar caracteres comunes de OCR
        cleaned = line.strip()
        if cleaned:  # Solo agregar líneas no vacías
            cleaned = cleaned.replace('O', '0').replace('l', '1').replace('I', '1')
            cleaned = cleaned.replace('|', '').replace('[', '').replace(']', '')
            cleaned = cleaned.replace('S', '5').replace('s', '5')
            cleaned_lines.append(cleaned)
    
    # Estrategia 1: Buscar patrones de transacciones HSBC específicos
    # Patrón: fecha + descripción + monto (más flexible)
    patterns = [
        # Patrón original HSBC: dos fechas + descripción + monto
        r"(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})\s+(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})\s+(.+?)\s*([+-])?\$?([\d,\.]+)",
        # Patrón con una sola fecha + descripción + monto
        r"(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})\s+(.+?)\s*([+-])?\$?([\d,\.]+)",
        # Patrón más flexible: cualquier línea con fecha y monto
        r"(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4}).*?([+-])?\$?([\d,\.]+)",
        # Buscar montos con signo en cualquier parte de la línea
        r".*?([+-])\$?([\d,\.]+).*?(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})",
    ]
    
    for pattern in patterns:
        for i, line in enumerate(cleaned_lines):
            match = re.search(pattern, line)
            if match:
                try:
                    if len(match.groups()) >= 4:  # Patrón con dos fechas
                        fecha_operacion = match.group(1).replace('O', '0') if match.group(1) else None
                        fecha_cargo = match.group(2).replace('O', '0') if match.group(2) else None
                        descripcion = match.group(3).strip() if match.group(3) else ""
                        signo = match.group(4) or '+'
                        monto_str = match.group(5).replace(',', '').replace('O', '0') if match.group(5) else "0"
                    elif len(match.groups()) == 4:  # Patrón con una fecha
                        fecha_operacion = match.group(1).replace('O', '0') if match.group(1) else None
                        fecha_cargo = fecha_operacion
                        descripcion = match.group(2).strip() if match.group(2) else ""
                        signo = match.group(3) or '+'
                        monto_str = match.group(4).replace(',', '').replace('O', '0') if match.group(4) else "0"
                    elif len(match.groups()) == 3:  # Patrón flexible
                        if 'fecha' in pattern:
                            fecha_operacion = match.group(1).replace('O', '0') if match.group(1) else None
                            fecha_cargo = fecha_operacion
                            signo = match.group(2) or '+'
                            monto_str = match.group(3).replace(',', '').replace('O', '0') if match.group(3) else "0"
                            descripcion = line[:match.start()].strip() if line else ""
                        else:  # Monto primero
                            signo = match.group(1) if match.group(1) else '+'
                            monto_str = match.group(2).replace(',', '').replace('O', '0') if match.group(2) else "0"
                            fecha_operacion = match.group(3).replace('O', '0') if match.group(3) else None
                            fecha_cargo = fecha_operacion
                            descripcion = line[:match.start()].strip() if line else ""
                    
                    # Validar que todos los campos necesarios estén presentes
                    if not fecha_operacion or not monto_str or monto_str == "0":
                        continue
                        
                    try:
                        monto = float(monto_str)
                    except ValueError:
                        continue
                        
                    tipo = "abono" if signo == '+' else "cargo"
                    if tipo == "cargo":
                        monto = -monto
                    
                    # Validar que la descripción no esté vacía
                    if descripcion and len(descripcion.strip()) > 2:
                        transactions.append({
                            "fecha_operacion": fecha_operacion,
                            "fecha_cargo": fecha_cargo,
                            "descripcion": descripcion,
                            "monto": monto,
                            "tipo": tipo,
                            "categoria": "Sin categorizar"
                        })
                        print(f"✅ Transacción encontrada: {fecha_operacion} - {descripcion[:40]} - {signo}${monto_str}")
                except Exception as e:
                    print(f"❌ Error procesando línea: {line} - {e}")
                    continue
    
    # Estrategia 2: Buscar líneas que contengan montos y fechas por separado
    if not transactions:
        print("🔍 Estrategia 2: Buscando montos y fechas por separado...")
        for i, line in enumerate(cleaned_lines):
            # Buscar montos con signo - más específico para evitar falsos positivos
            monto_match = re.search(r'([+-])\$?([\d,]+\.\d{2})', line)  # Solo montos con decimales
            if monto_match:
                signo = monto_match.group(1)
                monto_str = monto_match.group(2).replace(',', '').replace('O', '0')
                
                # Validar que el monto sea razonable (entre 1 y 1,000,000)
                try:
                    monto = float(monto_str)
                    if monto < 1 or monto > 1000000:
                        continue  # Saltar montos irrazonables
                except:
                    continue
                
                # Buscar fecha en la misma línea o líneas cercanas
                fecha_encontrada = None
                descripcion = line.replace(monto_match.group(0), '').strip()
                
                # Buscar fecha en la línea actual
                fecha_match = re.search(r'(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})', line)
                if fecha_match:
                    fecha_encontrada = fecha_match.group(1).replace('O', '0')
                    descripcion = descripcion.replace(fecha_match.group(0), '').strip()
                
                # Si no hay fecha en esta línea, buscar en líneas anteriores
                if not fecha_encontrada and i > 0:
                    for j in range(max(0, i-3), i):
                        fecha_match = re.search(r'(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})', cleaned_lines[j])
                        if fecha_match:
                            fecha_encontrada = fecha_match.group(1).replace('O', '0')
                            break
                
                try:
                    tipo = "abono" if signo == '+' else "cargo"
                    if tipo == "cargo":
                        monto = -monto
                    
                    # Validaciones adicionales
                    if (fecha_encontrada and 
                        descripcion and 
                        len(descripcion.strip()) > 2 and
                        not descripcion.strip().isdigit() and  # No solo números
                        not re.match(r'^\d+$', descripcion.strip())):  # No solo dígitos
                        
                        transactions.append({
                            "fecha_operacion": fecha_encontrada,
                            "fecha_cargo": fecha_encontrada,
                            "descripcion": descripcion,
                            "monto": monto,
                            "tipo": tipo,
                            "categoria": "Sin categorizar"
                        })
                        print(f"✅ Transacción encontrada (estrategia 2): {fecha_encontrada} - {descripcion[:40]} - {signo}${monto_str}")
                except Exception as e:
                    print(f"❌ Error procesando monto: {line} - {e}")
                    continue
    
    # Estrategia 3: Buscar patrones específicos de HSBC en el texto
    if not transactions:
        print("🔍 Estrategia 3: Buscando patrones específicos de HSBC...")
        
        # Buscar secciones que contengan transacciones
        text_lower = extracted_text.lower()
        
        # Buscar en secciones específicas del estado de cuenta
        sections = [
            "cargos, abonos y compras regulares",
            "desglose de movimientos", 
            "compras y cargos diferidos",
            "distribución de tu saldo"
        ]
        
        for section in sections:
            if section in text_lower:
                print(f"📋 Encontrada sección: {section}")
                # Buscar líneas después de esta sección que contengan montos
                lines = extracted_text.split('\n')
                section_found = False
                for i, line in enumerate(lines):
                    if section in line.lower():
                        section_found = True
                        print(f"📍 Sección encontrada en línea {i+1}")
                        # Buscar las siguientes líneas por montos
                        for j in range(i+1, min(i+20, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and len(next_line) > 5:
                                # Buscar montos con decimales
                                monto_match = re.search(r'([+-])\$?([\d,]+\.\d{2})', next_line)
                                if monto_match:
                                    print(f"💰 Monto encontrado en línea {j+1}: {next_line}")
                                    # Intentar extraer fecha y descripción
                                    fecha_match = re.search(r'(\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4})', next_line)
                                    if fecha_match:
                                        fecha = fecha_match.group(1).replace('O', '0')
                                        descripcion = next_line.replace(monto_match.group(0), '').replace(fecha_match.group(0), '').strip()
                                        if descripcion and len(descripcion) > 2:
                                            try:
                                                monto = float(monto_match.group(2).replace(',', ''))
                                                if 1 <= monto <= 1000000:
                                                    signo = monto_match.group(1)
                                                    tipo = "abono" if signo == '+' else "cargo"
                                                    if tipo == "cargo":
                                                        monto = -monto
                                                    
                                                    transactions.append({
                                                        "fecha_operacion": fecha,
                                                        "fecha_cargo": fecha,
                                                        "descripcion": descripcion,
                                                        "monto": monto,
                                                        "tipo": tipo,
                                                        "categoria": "Sin categorizar"
                                                    })
                                                    print(f"✅ Transacción encontrada (estrategia 3): {fecha} - {descripcion[:40]} - {signo}${monto_match.group(2)}")
                                            except Exception as e:
                                                print(f"❌ Error procesando línea {j+1}: {e}")
                break
    
    print(f"📊 Total de transacciones HSBC encontradas: {len(transactions)}")
    return transactions

def extract_santander_transactions(extracted_text: str) -> list:
    """
    Extrae transacciones de Santander del texto OCR.
    Limpia descripciones, normaliza montos y fechas, y filtra duplicados y líneas basura.
    """
    import re
    from datetime import datetime
    transactions = []
    seen = set()
    if not extracted_text or not isinstance(extracted_text, str):
        print("❌ Texto extraído es None o no es string")
        return transactions
    lines = extracted_text.split('\n')
    print("🔍 Buscando transacciones en texto Santander (limpieza avanzada)...")
    # Patrón: fecha, folio, descripción, monto
    pattern = re.compile(r"(\d{2}-[A-Z]{3}-\d{4})[^\d]*(.+?)([\d,]+\.\d{2})")
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        match = pattern.search(line)
        if match:
            fecha_raw, desc_raw, monto_raw = match.groups()
            # Limpiar fecha
            try:
                fecha = fecha_raw.upper()
                # Normalizar mes español a inglés si aplica
                meses = {'ENE':'Jan','FEB':'Feb','MAR':'Mar','ABR':'Apr','MAY':'May','JUN':'Jun','JUL':'Jul','AGO':'Aug','SEP':'Sep','OCT':'Oct','NOV':'Nov','DIC':'Dec'}
                for esp, eng in meses.items():
                    if esp in fecha:
                        fecha = fecha.replace(esp, eng)
                fecha_dt = datetime.strptime(fecha, "%d-%b-%Y").date()
            except Exception:
                continue
            # Limpiar descripción
            desc = re.sub(r"[\[\]\|]+", " ", desc_raw)
            desc = re.sub(r"\s+", " ", desc).strip()
            # Limpiar monto
            monto = float(monto_raw.replace(",", ""))
            # Heurística: si la palabra 'abono' o 'deposito' está en la descripción, es abono
            tipo = 'abono' if re.search(r"abono|deposito|ingreso", desc, re.I) else 'cargo'
            # Firmar monto según tipo
            monto = abs(monto) if tipo == 'abono' else -abs(monto)
            # Evitar duplicados
            key = (fecha_dt, desc, monto)
            if key in seen:
                continue
            seen.add(key)
            transactions.append({
                'fecha_operacion': fecha_raw,  # Mantener formato original "01-ABR-2025"
                'fecha_cargo': fecha_raw,      # Mantener formato original "01-ABR-2025"
                'descripcion': desc,
                'monto': monto,
                'tipo': tipo,
                'categoria': 'Sin categorizar'
            })
    print(f"📊 Total de transacciones Santander limpias encontradas: {len(transactions)}")
    return transactions

def _process_chunk_with_ai(chunk: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Procesa un chunk de texto con AI.
    """
    try:
        # Limpiar cualquier configuración global de OpenAI
        import openai
        if hasattr(openai, 'api_key'):
            delattr(openai, 'api_key')
        if hasattr(openai, '_client'):
            delattr(openai, '_client')
        
        # Configurar OpenAI sin proxies usando el cliente
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Extrae todas las transacciones bancarias del siguiente texto. 
        Para cada transacción, identifica:
        - fecha_operacion: fecha de la transacción (formato DD-MMM-YYYY)
        - descripcion: descripción de la transacción
        - monto: monto de la transacción (número con decimales)
        - categoria: categoría de la transacción (supermercado, transporte, restaurante, etc.)

        Responde SOLO con un JSON válido en este formato:
        [
            {{
                "fecha_operacion": "DD-MMM-YYYY",
                "descripcion": "descripción",
                "monto": 123.45,
                "categoria": "categoría"
            }}
        ]

        Texto a analizar:
        {chunk}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en extracción de transacciones bancarias. Responde SOLO con JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Intentar parsear JSON
        try:
            import json
            transactions = json.loads(content)
            if isinstance(transactions, list):
                return transactions
            else:
                print(f"❌ Respuesta no es una lista: {type(transactions)}")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"🔎 Respuesta cruda: {content}")
            return []
            
    except Exception as e:
        print(f"❌ Error procesando chunk: {e}")
        return []

# Ruta de prueba
@app.get("/")
def read_root():
    return {"message": "PFM API is running!"}
