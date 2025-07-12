import pdfplumber
import os
import pytesseract
from PIL import Image
import io

def debug_new_pdf():
    """Debug detallado del nuevo PDF"""
    
    pdf_file = "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return
    
    print("🔍 DEBUG DETALLADO DEL NUEVO PDF...")
    print("=" * 50)
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            print(f"📄 Número de páginas: {len(pdf.pages)}")
            
            for i, page in enumerate(pdf.pages):
                print(f"\n📖 PÁGINA {i+1}:")
                print("-" * 30)
                
                # Intentar extracción de texto normal
                text = page.extract_text()
                print(f"Texto extraído (longitud: {len(text) if text else 0}):")
                if text:
                    print(text[:500] + "..." if len(text) > 500 else text)
                else:
                    print("❌ No se pudo extraer texto")
                
                # Verificar si hay códigos ilegibles
                if text and "(cid:" in text:
                    print("⚠️ Se detectaron códigos ilegibles (cid:XXX)")
                
                # Intentar OCR si no hay texto o hay códigos ilegibles
                if not text or "(cid:" in text:
                    print("🔄 Intentando OCR...")
                    try:
                        # Convertir página a imagen
                        img = page.to_image(resolution=300)
                        img_bytes = img.original.convert('RGB')
                        
                        # Configuración OCR
                        custom_config = r'--oem 3 --psm 6 -l spa+eng --dpi 300'
                        ocr_text = pytesseract.image_to_string(img_bytes, config=custom_config)
                        
                        print(f"OCR completado (longitud: {len(ocr_text)}):")
                        print(ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text)
                        
                    except Exception as e:
                        print(f"❌ Error en OCR: {e}")
                
                # Mostrar información de la página
                print(f"Dimensiones: {page.width} x {page.height}")
                print(f"Rotación: {page.rotation}")
                
                # Buscar tablas
                tables = page.extract_tables()
                if tables:
                    print(f"📊 Encontradas {len(tables)} tablas")
                    for j, table in enumerate(tables):
                        print(f"   Tabla {j+1}: {len(table)} filas")
                        if table and len(table) > 0:
                            print(f"   Primera fila: {table[0]}")
                else:
                    print("📊 No se encontraron tablas")
                
                # Solo procesar las primeras 3 páginas para evitar output muy largo
                if i >= 2:
                    print("... (limitado a las primeras 3 páginas)")
                    break
                    
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")

if __name__ == "__main__":
    debug_new_pdf() 