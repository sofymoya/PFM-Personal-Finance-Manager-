from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from .schemas import TokenData
import os

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui_cambiala_en_produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de la contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verifica y decodifica el token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError:
        return None

# ----------- AI para extraer transacciones del texto del PDF -----------
def extract_transactions_with_ai(pdf_text: str) -> list:
    import openai
    from openai import OpenAI
    import json
    import re

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Dividir el texto en chunks más pequeños para evitar el límite de contexto
    def split_text_into_chunks(text: str, max_chunk_size: int = 8000) -> list:
        """Divide el texto en chunks más pequeños, respetando líneas completas"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > max_chunk_size and current_chunk:
                # Finalizar chunk actual
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Agregar el último chunk si no está vacío
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    # Dividir el texto en chunks
    text_chunks = split_text_into_chunks(pdf_text)
    print(f"📄 Texto dividido en {len(text_chunks)} chunks para procesamiento AI")

    all_transactions = []
    
    for i, chunk in enumerate(text_chunks):
        print(f"🤖 Procesando chunk {i+1}/{len(text_chunks)}...")
        
        prompt = (
            "Eres un experto en análisis de estados de cuenta bancarios MEXICANOS. Extrae SOLO transacciones REALES del texto proporcionado.\n\n"
            "INSTRUCCIONES:\n"
            "1. SOLO extrae transacciones con montos REALES (mínimo $5.00)\n"
            "2. NO extraigas encabezados, resúmenes, o texto promocional\n"
            "3. Busca transacciones con fechas, descripciones y montos claros\n"
            "4. Los cargos deben ser NEGATIVOS, los abonos POSITIVOS\n"
            "5. Busca patrones de bancos mexicanos: 'SU PAGO', 'COMPRA', 'RETIRO', 'DEPOSITO', etc.\n"
            "6. Para HSBC busca códigos como 'ME 010517AEA', fechas 'DD-MMM-YYYY', montos '$XXX.XX'\n\n"
            "FORMATO: Lista JSON con transacciones:\n"
            "[\n"
            "  {\n"
            "    \"fecha_operacion\": \"DD-MMM-YYYY\",\n"
            "    \"fecha_cargo\": \"DD-MMM-YYYY\",\n"
            "    \"descripcion\": \"Descripción de la transacción\",\n"
            "    \"monto\": -1234.56\n"
            "  }\n"
            "]\n\n"
            "TEXTO:\n"
            f"{chunk}\n\n"
            "Extrae SOLO transacciones REALES:"
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"✅ Chunk {i+1}: {len(result)} transacciones encontradas")
            
            # Filtrar transacciones válidas
            for transaction in result:
                try:
                    monto = transaction.get('monto', 0)
                    descripcion = transaction.get('descripcion', '').lower()
                    
                    # Validaciones para evitar falsos positivos
                    if (abs(monto) >= 5.0 and  # Monto mínimo $5
                        monto != 0 and  # No montos de $0
                        'interes' not in descripcion and  # No tasas de interés
                        'saldo' not in descripcion and  # No saldos
                        'tasa' not in descripcion and  # No tasas
                        'pago minimo' not in descripcion and  # No pagos mínimos
                        '0%' not in descripcion and  # No porcentajes 0%
                        len(descripcion.strip()) > 3):  # Descripción válida
                        
                        all_transactions.append(transaction)
                        print(f"✅ Transacción válida: {transaction.get('fecha_operacion', '')} - {transaction.get('descripcion', '')[:40]} - ${monto}")
                except Exception as e:
                    print(f"❌ Error validando transacción en chunk {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error procesando chunk {i+1}: {e}")
            continue
    
    print(f"📊 Total de transacciones válidas encontradas: {len(all_transactions)}")
    return all_transactions