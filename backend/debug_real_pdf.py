import pdfplumber
import os

def debug_real_pdf():
    """Extrae y muestra el texto del PDF real para depuración"""
    
    pdf_file = "uploaded_pdfs/2025-05-16_Estado_de_cuenta.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Error: El archivo {pdf_file} no existe")
        return
    
    print("🔍 ANALIZANDO PDF REAL...")
    print("=" * 50)
    
    with pdfplumber.open(pdf_file) as pdf:
        print(f"📄 Número de páginas: {len(pdf.pages)}")
        
        for i, page in enumerate(pdf.pages):
            print(f"\n📖 PÁGINA {i+1}:")
            print("-" * 30)
            
            text = page.extract_text()
            if text:
                print("TEXTO EXTRAÍDO:")
                print(text)
                print(f"\nLongitud del texto: {len(text)} caracteres")
                
                # Buscar patrones específicos
                print("\n🔍 ANÁLISIS DE PATRONES:")
                
                # Buscar nombres de bancos
                bancos = ["BBVA", "Santander", "Banorte", "Banamex", "HSBC", "Banregio"]
                for banco in bancos:
                    if banco.lower() in text.lower():
                        print(f"✅ Encontrado banco: {banco}")
                
                # Buscar fechas
                import re
                fechas = re.findall(r'\d{2}-[A-Za-z]{3}-\d{4}', text)
                if fechas:
                    print(f"✅ Encontradas fechas: {fechas[:5]}...")  # Mostrar solo las primeras 5
                
                # Buscar montos
                montos = re.findall(r'[\$]?[\d,]+\.\d{2}', text)
                if montos:
                    print(f"✅ Encontrados montos: {montos[:5]}...")  # Mostrar solo los primeros 5
                
                # Buscar líneas que parezcan transacciones
                lines = text.split('\n')
                print(f"\n📋 LÍNEAS CON POSIBLES TRANSACCIONES:")
                for j, line in enumerate(lines):
                    line = line.strip()
                    if line and any(char.isdigit() for char in line) and len(line) > 20:
                        print(f"Línea {j+1}: {line}")
                        if j > 10:  # Solo mostrar las primeras 10 líneas relevantes
                            break
            else:
                print("❌ No se pudo extraer texto de esta página")
    
    print("\n" + "=" * 50)
    print("🔍 ANÁLISIS COMPLETADO")

if __name__ == "__main__":
    debug_real_pdf() 