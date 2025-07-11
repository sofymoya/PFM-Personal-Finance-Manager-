import requests
import os

def test_real_pdf_upload():
    """Prueba la carga del PDF real con OCR"""
    
    pdf_file = "uploaded_pdfs/2025-05-16_Estado_de_cuenta.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ Error: El archivo {pdf_file} no existe")
        return
    
    print("🚀 Probando carga del PDF REAL con OCR...")
    print("=" * 60)
    
    # URL del endpoint de prueba
    url = "http://localhost:8000/test_upload_pdf"
    
    try:
        with open(pdf_file, "rb") as f:
            files = {"file": (os.path.basename(pdf_file), f, "application/pdf")}
            
            print("📤 Subiendo PDF al backend...")
            response = requests.post(url, files=files)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n✅ ÉXITO - PDF procesado correctamente")
                print(f"Archivo: {result['filename']}")
                print(f"Banco detectado: {result['banco']}")
                print(f"Transacciones extraídas: {len(result['transacciones_extraidas'])}")
                print(f"Mensaje: {result['message']}")
                
                print("\n📊 TRANSACCIONES EXTRAÍDAS:")
                for i, trans in enumerate(result['transacciones_extraidas'], 1):
                    print(f"{i}. {trans['description']} - ${trans['amount']:.2f} - {trans['category']}")
                
                print(f"\n📄 TEXTO EXTRAÍDO (primeros 500 caracteres):")
                texto = result['texto_extraido']
                print(texto[:500] + "..." if len(texto) > 500 else texto)
                
                # Verificar si se usó OCR
                if "(cid:" in texto:
                    print("\n⚠️  ADVERTENCIA: El texto aún contiene códigos (cid:XXX)")
                    print("   Esto indica que el OCR no funcionó completamente")
                else:
                    print("\n✅ El texto extraído es legible (sin códigos cid:XXX)")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error durante la carga: {e}")

if __name__ == "__main__":
    test_real_pdf_upload() 