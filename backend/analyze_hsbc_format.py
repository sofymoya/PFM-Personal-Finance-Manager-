import os
import sys
sys.path.append('.')

from app.main import extract_text_with_ocr_fallback

def analyze_hsbc_format():
    """Analiza el formato del PDF de HSBC para encontrar patrones de transacciones"""
    
    pdf_file = "uploaded_pdfs/2025-05-16_Estado_de_cuenta.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return
    
    print("🔍 ANALIZANDO FORMATO HSBC...")
    print("=" * 50)
    
    try:
        # Extraer texto con OCR
        extracted_text = extract_text_with_ocr_fallback(pdf_file)
        
        print("📄 TEXTO COMPLETO EXTRAÍDO:")
        print("-" * 30)
        print(extracted_text)
        print("-" * 30)
        
        # Buscar líneas que contengan fechas
        import re
        lines = extracted_text.split('\n')
        
        print("\n🔍 BUSCANDO PATRONES DE FECHAS:")
        date_patterns = [
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\w{3}-\d{4}',  # DD-MMM-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in date_patterns:
                if re.search(pattern, line):
                    print(f"Línea {i+1}: {line}")
                    break
        
        print("\n🔍 BUSCANDO PATRONES DE MONTOS:")
        amount_patterns = [
            r'\$[\d,]+\.\d{2}',  # $1,234.56
            r'[\d,]+\.\d{2}',    # 1,234.56
            r'[\d,]+\.\d{2}',    # 1234.56
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in amount_patterns:
                if re.search(pattern, line):
                    print(f"Línea {i+1}: {line}")
                    break
        
        print("\n🔍 BUSCANDO LÍNEAS CON POSIBLES TRANSACCIONES:")
        # Buscar líneas que contengan tanto fechas como montos
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 20:
                continue
                
            has_date = any(re.search(pattern, line) for pattern in date_patterns)
            has_amount = any(re.search(pattern, line) for pattern in amount_patterns)
            
            if has_date and has_amount:
                print(f"Línea {i+1}: {line}")
        
        print("\n🔍 BUSCANDO PALABRAS CLAVE DE TRANSACCIONES:")
        keywords = ['compra', 'retiro', 'deposito', 'transferencia', 'pago', 'cargo', 'abono', 'spei']
        for i, line in enumerate(lines):
            line = line.strip().lower()
            if not line:
                continue
                
            if any(keyword in line for keyword in keywords):
                print(f"Línea {i+1}: {line}")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_hsbc_format() 