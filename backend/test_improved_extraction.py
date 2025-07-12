#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras en la extracción de PDF.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
sys.path.append(str(Path(__file__).parent))

from app.main import extract_text_with_ocr_fallback
from app.auth import extract_transactions_with_ai
from dotenv import load_dotenv

load_dotenv()

def test_pdf_extraction():
    """Prueba la extracción de texto de un PDF."""
    
    # Buscar PDFs en el directorio uploaded_pdfs
    pdf_dir = Path("uploaded_pdfs")
    if not pdf_dir.exists():
        print("❌ Directorio uploaded_pdfs no encontrado")
        return
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No se encontraron archivos PDF en uploaded_pdfs")
        return
    
    print(f"📄 Encontrados {len(pdf_files)} archivos PDF")
    
    # Probar con el primer PDF
    pdf_path = str(pdf_files[0])
    print(f"🧪 Probando con: {pdf_path}")
    
    # Extraer texto
    print("\n" + "="*50)
    print("EXTRACCIÓN DE TEXTO")
    print("="*50)
    
    extracted_text = extract_text_with_ocr_fallback(pdf_path)
    
    if not extracted_text.strip():
        print("❌ No se pudo extraer texto del PDF")
        return
    
    print(f"\n✅ Texto extraído exitosamente: {len(extracted_text)} caracteres")
    
    # Mostrar primeras líneas
    lines = extracted_text.split('\n')[:10]
    print("\n📄 Primeras 10 líneas del texto extraído:")
    for i, line in enumerate(lines):
        if line.strip():
            print(f"   {i+1}: {line.strip()}")
    
    # Probar extracción con AI
    print("\n" + "="*50)
    print("EXTRACCIÓN CON AI")
    print("="*50)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No se encontró OPENAI_API_KEY en el archivo .env")
        return
    
    try:
        transactions = extract_transactions_with_ai(extracted_text)
        
        if transactions:
            print(f"\n✅ AI encontró {len(transactions)} transacciones:")
            for i, transaction in enumerate(transactions[:5]):  # Mostrar solo las primeras 5
                print(f"   {i+1}. {transaction.get('fecha_operacion', 'N/A')} - {transaction.get('descripcion', 'N/A')} - ${transaction.get('monto', 0)}")
            if len(transactions) > 5:
                print(f"   ... y {len(transactions) - 5} más")
        else:
            print("❌ AI no encontró transacciones")
            
    except Exception as e:
        print(f"❌ Error en extracción con AI: {e}")

if __name__ == "__main__":
    test_pdf_extraction() 