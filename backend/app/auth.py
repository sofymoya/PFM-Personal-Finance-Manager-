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

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    prompt = (
        "Eres un experto en análisis de estados de cuenta bancarios MEXICANOS. Tu tarea es extraer TODAS las transacciones del texto proporcionado.\n\n"
        "INSTRUCCIONES IMPORTANTES:\n"
        "1. Busca TODAS las transacciones, no solo las primeras que encuentres\n"
        "2. Identifica diferentes formatos de fechas: DD/MM/YYYY, DD-MMM-YYYY, DD-MM-YYYY, etc.\n"
        "3. Busca montos en diferentes formatos: $1,234.56, 1234.56, -1234.56, etc.\n"
        "4. Los cargos (gastos) deben ser NEGATIVOS, los abonos (ingresos) deben ser POSITIVOS\n"
        "5. Incluye transacciones de diferentes tipos: compras, retiros, depósitos, transferencias, comisiones, intereses\n"
        "6. Busca patrones específicos de bancos mexicanos:\n"
        "   - 'SU PAGO GRACIAS SPEI', 'SU PAGO', 'PAGO SPEI'\n"
        "   - 'COMPRA TARJETA', 'COMPRA EN', 'COMPRA CON TARJETA'\n"
        "   - 'RETIRO CAJERO', 'RETIRO ATM', 'RETIRO SIN TARJETA'\n"
        "   - 'DEPOSITO', 'DEPOSITO EFECTIVO', 'DEPOSITO CHEQUE'\n"
        "   - 'COMISION', 'COMISION POR SERVICIO', 'COMISION MANTENIMIENTO'\n"
        "   - 'INTERES', 'INTERES GANADO', 'INTERES CREDITO'\n"
        "   - 'TRANSFERENCIA', 'TRANSFERENCIA SPEI', 'TRANSFERENCIA INTERBANCARIA'\n"
        "   - 'PAGO SERVICIOS', 'PAGO TELEFONO', 'PAGO LUZ', 'PAGO AGUA'\n"
        "   - 'NETFLIX', 'SPOTIFY', 'AMAZON', 'UBER', 'DIDI', 'RAPPI'\n"
        "   - 'OXXO', 'SEVEN ELEVEN', 'FARMACIA', 'GASOLINERA'\n"
        "7. Si hay múltiples páginas, revisa TODO el contenido\n"
        "8. No ignores transacciones pequeñas o que parezcan insignificantes\n"
        "9. Busca en tablas, listas y cualquier formato de presentación\n"
        "10. Incluye transacciones de todas las fechas del período del estado de cuenta\n"
        "11. ATENCIÓN ESPECIAL: Busca transacciones en formato HSBC que incluyen:\n"
        "    - Códigos como 'ME 010517AEA', 'CA OLO1112061Y2', 'VPS 100716CK9', etc.\n"
        "    - Descripciones como 'VINOTECA SAN JERONIMO MON', 'IAPPLE.COMIBILL', 'OPLINEA*PUEBLOSERENA'\n"
        "    - Montos en formato '$XXX.XX' o números decimales\n"
        "    - Fechas en formato 'DD-MMM-YYYY' como '07-May-2025', '21-Abr-2025'\n"
        "12. Busca en la sección 'DESGLOSE DE MOVIMIENTOS' y 'CARGOS, ABONOS Y COMPRAS REGULARES'\n\n"
        "FORMATO DE SALIDA:\n"
        "Devuelve una lista JSON con cada transacción que encuentres:\n"
        "[\n"
        "  {\n"
        "    \"fecha_operacion\": \"DD-MMM-YYYY\",\n"
        "    \"fecha_cargo\": \"DD-MMM-YYYY\",\n"
        "    \"descripcion\": \"Descripción completa de la transacción\",\n"
        "    \"monto\": -1234.56\n"
        "  }\n"
        "]\n\n"
        "EJEMPLOS DE TRANSACCIONES QUE DEBES BUSCAR:\n"
        "- Fecha: 07-May-2025, Descripción: \"SU PAGO GRACIAS SPEI A CTA CLABE XXXXXXXX1179\", Monto: 20000.00 (POSITIVO por ser pago)\n"
        "- Fecha: 21-Abr-2025, Descripción: \"ME 010517AEA VINOTECA SAN JERONIMO MON\", Monto: -310.63 (NEGATIVO por ser cargo)\n"
        "- Fecha: 05-May-2025, Descripción: \"IAPPLE.COMIBILL _ 866-712-7753 CA OLO1112061Y2 OMA MTY PREPAGO\", Monto: -13450.64\n"
        "- Fecha: 05-May-2025, Descripción: \"OPLINEA*PUEBLOSERENA SAN RONY SFRESH PIZZA NEWYORK NY\", Monto: -2413.16\n"
        "- Fecha: 06-May-2025, Descripción: \"VPS 100716CK9 VS TELCEL 018001200006 MEX\", Monto: -61.20\n"
        "- Fecha: 06-May-2025, Descripción: \"SQ *DOWNTOWN MARKET GA Jamaica NY\", Monto: -830.00\n"
        "- Fecha: 06-May-2025, Descripción: \"IANA 050518RL1 VIVA AEROBUS. APO\", Monto: -1400.00\n"
        "- Fecha: 07-May-2025, Descripción: \"UBER *TRIP 8005928996 CA\", Monto: -340.00\n"
        "- Fecha: 08-May-2025, Descripción: \"REA 880909AU8 REA AUTOPISTA GPE | CAD\", Monto: -546.69\n"
        "- Fecha: 08-May-2025, Descripción: \"BBE 061123744 IPARK MTY INTERRED APO\", Monto: -125.00\n"
        "- Fecha: 08-May-2025, Descripción: \"STR*SP LUMAI JOYERIA CIUDAD DE MEX MEX\", Monto: -150.00\n"
        "- Fecha: 12-May-2025, Descripción: \"MERCADOPAGO *INSIGNIA Monterrey NLE\", Monto: -49.00\n"
        "- Fecha: 12-May-2025, Descripción: \"SIH 9511279T7 HEB GONZALITOS MON\", Monto: -680.00\n"
        "- Fecha: 12-May-2025, Descripción: \"RIM 1411069L4 VTA A BORDO VAEROBUS _CIU\", Monto: -1100.00\n"
        "- Fecha: 14-May-2025, Descripción: \"LIM 191031AU3 GLOW CAR SPA MON\", Monto: -86.00\n"
        "- Fecha: 15-May-2025, Descripción: \"OPM 150323DI1 PAYPAL*COMERCIALIZ MEX\", Monto: -35.00\n"
        "- Fecha: 29-Abr-2025, Descripción: \"ZMC 960801538 ZARA MEXICO. clu\", Monto: -949.00\n"
        "- Fecha: 29-Abr-2025, Descripción: \"ZMC 960801538 ZARA MEXICO. clu\", Monto: -1698.00\n"
        "- Fecha: 12-May-2025, Descripción: \"ANA 050518RL1 VIVA AEROBUS CIB APO\", Monto: -4147.64\n"
        "- Fecha: 12-May-2025, Descripción: \"ANA 050518RL1 VIVAAEROBUS MOBILE APO\", Monto: -4026.61\n\n"
        "REGLAS:\n"
        "- Los montos de GASTOS deben ser NEGATIVOS\n"
        "- Los montos de INGRESOS deben ser POSITIVOS\n"
        "- Incluye TODAS las transacciones que encuentres, sin importar el monto\n"
        "- Si no hay transacciones claras, devuelve []\n"
        "- Responde SOLO con el JSON, sin texto adicional\n\n"
        "TEXTO DEL ESTADO DE CUENTA:\n"
        f"{pdf_text}\n\n"
        "Extrae TODAS las transacciones encontradas:"
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,  # Aumentado para manejar más transacciones
        temperature=0
    )
    try:
        result = json.loads(response.choices[0].message.content)
        print(f"Transacciones extraídas: {len(result)}")
        return result
    except Exception as e:
        print(f"Error parsing AI response: {e}")
        print(f"Response content: {response.choices[0].message.content}")
        return []