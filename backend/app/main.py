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
    with pdfplumber.open(pdf_path) as pdf:
        extracted_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
        # Verificar si el texto contiene códigos (cid:XXX) que indican texto ilegible
        if "(cid:" in extracted_text:
            print("🔍 Texto extraído contiene códigos (cid:XXX). Usando OCR mejorado como fallback...")
            ocr_text = ""
            
            for page_num, page in enumerate(pdf.pages):
                # Convertir página a imagen con mejor resolución
                img = page.to_image(resolution=300)  # Aumentar resolución
                img_bytes = img.original.convert('RGB')
                
                # Preprocesar imagen para mejorar OCR
                processed_img = preprocess_image_for_ocr(img_bytes)
                
                # Usar OCR mejorado para extraer texto
                try:
                    # Configuración optimizada para estados de cuenta bancarios
                    custom_config = r'--oem 3 --psm 6 -l spa+eng --dpi 300'
                    page_text = pytesseract.image_to_string(processed_img, config=custom_config)
                    
                    # Limpiar y mejorar el texto extraído
                    cleaned_text = clean_ocr_text(page_text)
                    ocr_text += cleaned_text + "\n"
                    print(f"✅ OCR mejorado completado para página {page_num + 1}")
                    
                    # Debug: mostrar primeras líneas del texto extraído
                    lines = cleaned_text.split('\n')[:5]
                    print(f"📄 Primeras líneas página {page_num + 1}:")
                    for i, line in enumerate(lines):
                        if line.strip():
                            print(f"   {i+1}: {line.strip()}")
                    
                except Exception as e:
                    print(f"❌ Error en OCR para página {page_num + 1}: {e}")
                    # Si OCR falla, mantener el texto original de esa página
                    page_original = page.extract_text() or ""
                    ocr_text += page_original + "\n"
            
            print("🔍 OCR mejorado completado. Usando texto extraído con OCR.")
            return ocr_text
        else:
            print("✅ Texto extraído es legible. No se necesita OCR.")
            return extracted_text

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
        
        # Corregir caracteres mal interpretados
        char_replacements = {
            '0': '0', 'O': '0', 'o': '0',  # Normalizar ceros
            'l': '1', 'I': '1', '|': '1',  # Normalizar unos
            'S': '5', 's': '5',  # Normalizar cincos
            'G': '6', 'g': '6',  # Normalizar seises
            'B': '8', 'b': '8',  # Normalizar ochos
        }
        
        for old_char, new_char in char_replacements.items():
            # Solo reemplazar en contextos numéricos
            cleaned = re.sub(rf'\b{old_char}\b', new_char, cleaned)
        
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

def process_bank_statement_pdf(file_path: str, api_key: str):
    """
    Procesa un estado de cuenta bancario en PDF y extrae transacciones.
    Retorna una lista de transacciones con los campos requeridos.
    """
    transactions = []
    banco = None
    
    # Extraer texto con OCR mejorado como fallback si es necesario
    extracted_text = extract_text_with_ocr_fallback(file_path)
    
    # Si es HSBC, también intentar extraer de regiones específicas
    if "HSBC" in extracted_text:
        print("🏦 Detectado HSBC. Extrayendo texto de regiones específicas...")
        region_text = extract_transaction_regions(file_path)
        if region_text and region_text.strip():
            # Combinar texto completo con texto de regiones
            extracted_text += "\n\n--- TEXTO DE REGIONES ESPECÍFICAS ---\n"
            extracted_text += region_text
            print("✅ Texto de regiones específicas agregado")
        else:
            print("⚠️ No se pudo extraer texto de regiones específicas")
    
    print("\n--- TEXTO EXTRAÍDO DEL PDF ---\n")
    print(extracted_text)
    print("\n--- FIN DEL TEXTO EXTRAÍDO ---\n")
    
    # Debug: Mostrar líneas que contienen montos o fechas
    lines = extracted_text.split('\n')
    print("🔍 Líneas que contienen montos o fechas:")
    for i, line in enumerate(lines):
        if re.search(r'[\d,\.]+', line) or re.search(r'\d{2}[-/\s][A-Za-z0-9]{3}[-/\s]\d{4}', line):
            print(f"Línea {i+1}: {line.strip()}")
    print("--- FIN DEBUG ---\n")
    
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
    
    # Usar parser específico según el banco
    if banco == "HSBC":
        print("🏦 Usando parser específico para HSBC...")
        transactions = extract_hsbc_transactions(extracted_text)
        
        # Si no se encontraron transacciones, usar AI como fallback
        if not transactions:
            print("🤖 No se encontraron transacciones con parser regex. Usando AI como fallback...")
            try:
                from .auth import extract_transactions_with_ai
                ai_transactions = extract_transactions_with_ai(extracted_text)
                if ai_transactions:
                    print(f"🤖 AI encontró {len(ai_transactions)} transacciones")
                    # Convertir formato AI al formato esperado
                    for ai_txn in ai_transactions:
                        transactions.append({
                            "fecha_operacion": ai_txn.get("fecha_operacion", ""),
                            "fecha_cargo": ai_txn.get("fecha_cargo", ai_txn.get("fecha_operacion", "")),
                            "descripcion": ai_txn.get("descripcion", ""),
                            "monto": ai_txn.get("monto", 0),
                            "tipo": "abono" if ai_txn.get("monto", 0) > 0 else "cargo",
                            "categoria": "Sin categorizar"
                        })
                else:
                    print("🤖 AI tampoco encontró transacciones")
            except Exception as e:
                print(f"❌ Error usando AI fallback: {e}")
        
        # Categorizar transacciones encontradas
        for transaction in transactions:
            if transaction["categoria"] == "Sin categorizar":
                try:
                    transaction["categoria"] = categorize_transaction_openai(transaction["descripcion"], api_key)
                except Exception as e:
                    print(f"Error categorizando transacción HSBC: {e}")
                    transaction["categoria"] = "sin_categoria"
    else:
        # Parser original para otros bancos
        print("🏦 Usando parser estándar...")
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

# Ruta de prueba
@app.get("/")
def read_root():
    return {"message": "PFM API is running!"}
