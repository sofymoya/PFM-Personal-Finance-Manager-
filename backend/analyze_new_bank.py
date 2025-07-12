import os
import sys
sys.path.append('.')

from app.main import extract_text_with_ocr_fallback

def analyze_new_bank():
    """Analiza el nuevo PDF para identificar el banco y su formato"""
    
    pdf_file = "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return
    
    print("🔍 ANALIZANDO NUEVO PDF...")
    print("=" * 50)
    
    try:
        # Extraer texto con OCR
        extracted_text = extract_text_with_ocr_fallback(pdf_file)
        
        print("📄 TEXTO COMPLETO EXTRAÍDO:")
        print("-" * 30)
        print(extracted_text)
        print("-" * 30)
        
        # Buscar nombres de bancos conocidos
        import re
        lines = extracted_text.split('\n')
        
        print("\n🔍 BUSCANDO NOMBRES DE BANCOS:")
        bank_keywords = [
            "BBVA", "Santander", "Banorte", "Banamex", "HSBC", "Banregio",
            "Banco Azteca", "Banco del Bajío", "Banco Inbursa", "Banco Afirme",
            "Banco Interacciones", "Banco Multiva", "Banco Ve por Más",
            "Scotiabank", "Citibanamex", "Bancoppel", "Banco Famsa"
        ]
        
        found_banks = []
        for i, line in enumerate(lines):
            line_upper = line.upper()
            for bank in bank_keywords:
                if bank.upper() in line_upper:
                    found_banks.append((bank, i+1, line.strip()))
        
        if found_banks:
            print("✅ BANCOS ENCONTRADOS:")
            for bank, line_num, line_text in found_banks:
                print(f"   {bank} en línea {line_num}: {line_text}")
        else:
            print("❌ No se encontraron bancos conocidos")
        
        print("\n🔍 BUSCANDO PATRONES DE FECHAS:")
        date_patterns = [
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\w{3}-\d{4}',  # DD-MMM-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # D/M/YYYY
            r'\d{2}/\d{2}/\d{2}',  # DD/MM/YY
        ]
        
        date_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in date_patterns:
                if re.search(pattern, line):
                    date_lines.append((i+1, line))
                    break
        
        if date_lines:
            print("✅ LÍNEAS CON FECHAS:")
            for line_num, line_text in date_lines[:10]:  # Mostrar solo las primeras 10
                print(f"   Línea {line_num}: {line_text}")
        else:
            print("❌ No se encontraron fechas")
        
        print("\n🔍 BUSCANDO PATRONES DE MONTOS:")
        amount_patterns = [
            r'\$[\d,]+\.\d{2}',  # $1,234.56
            r'[\d,]+\.\d{2}',    # 1,234.56
            r'[\d,]+\.\d{2}',    # 1234.56
            r'[\d,]+\.\d{2}',    # 1234.56
        ]
        
        amount_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in amount_patterns:
                if re.search(pattern, line):
                    amount_lines.append((i+1, line))
                    break
        
        if amount_lines:
            print("✅ LÍNEAS CON MONTOS:")
            for line_num, line_text in amount_lines[:10]:  # Mostrar solo las primeras 10
                print(f"   Línea {line_num}: {line_text}")
        else:
            print("❌ No se encontraron montos")
        
        print("\n🔍 ANÁLISIS DE FORMATO:")
        print(f"   Total de líneas: {len(lines)}")
        print(f"   Líneas con fechas: {len(date_lines)}")
        print(f"   Líneas con montos: {len(amount_lines)}")
        
        # Buscar patrones específicos de transacciones
        print("\n🔍 BUSCANDO PATRONES DE TRANSACCIONES:")
        transaction_keywords = [
            "COMPRA", "PAGO", "RETIRO", "DEPOSITO", "CARGO", "ABONO", 
            "COMISION", "INTERES", "SALDO", "TOTAL", "SUBTOTAL"
        ]
        
        transaction_lines = []
        for i, line in enumerate(lines):
            line_upper = line.upper()
            for keyword in transaction_keywords:
                if keyword in line_upper:
                    transaction_lines.append((i+1, line.strip()))
                    break
        
        if transaction_lines:
            print("✅ LÍNEAS CON PALABRAS CLAVE DE TRANSACCIONES:")
            for line_num, line_text in transaction_lines[:15]:  # Mostrar solo las primeras 15
                print(f"   Línea {line_num}: {line_text}")
        else:
            print("❌ No se encontraron palabras clave de transacciones")
        
    except Exception as e:
        print(f"❌ Error analizando PDF: {e}")

if __name__ == "__main__":
    analyze_new_bank() 