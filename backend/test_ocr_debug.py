import os
import sys
sys.path.append('.')

from app.main import extract_text_with_ocr_fallback

def test_ocr_function():
    """Prueba específicamente la función OCR"""
    
    pdf_file = "uploaded_pdfs/2025-05-16_Estado_de_cuenta.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return
    
    print("🔍 PROBANDO FUNCIÓN OCR DIRECTAMENTE...")
    print("=" * 50)
    
    try:
        # Llamar directamente a la función OCR
        extracted_text = extract_text_with_ocr_fallback(pdf_file)
        
        print(f"\n📄 TEXTO EXTRAÍDO (primeros 1000 caracteres):")
        print("-" * 30)
        print(extracted_text[:1000])
        print("-" * 30)
        
        # Verificar si contiene códigos cid
        if "(cid:" in extracted_text:
            print("\n⚠️  El texto aún contiene códigos (cid:XXX)")
            print("   Esto indica que el OCR no funcionó correctamente")
            
            # Contar cuántos códigos cid hay
            cid_count = extracted_text.count("(cid:")
            print(f"   Número de códigos cid encontrados: {cid_count}")
        else:
            print("\n✅ El texto extraído es legible (sin códigos cid:XXX)")
        
        # Verificar si contiene texto legible
        legible_chars = sum(1 for c in extracted_text if c.isalpha() or c.isdigit())
        total_chars = len(extracted_text)
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Caracteres totales: {total_chars}")
        print(f"   Caracteres legibles: {legible_chars}")
        print(f"   Porcentaje legible: {(legible_chars/total_chars*100):.1f}%" if total_chars > 0 else "0%")
        
    except Exception as e:
        print(f"❌ Error durante la prueba OCR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_function() 