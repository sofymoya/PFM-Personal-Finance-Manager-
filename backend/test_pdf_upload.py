import requests
import json
import os

def test_pdf_upload():
    """Prueba la carga del PDF directamente en el backend"""
    
    # URL del endpoint de prueba (sin autenticación)
    url = "http://localhost:8000/test_upload_pdf"
    
    # Archivo PDF a subir
    pdf_file = "uploaded_pdfs/test_statement.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Error: El archivo {pdf_file} no existe")
        return
    
    # Preparar el archivo para la subida
    with open(pdf_file, 'rb') as f:
        files = {'file': ('test_statement.pdf', f, 'application/pdf')}
        
        # Headers necesarios (sin autenticación por ahora)
        headers = {}
        
        try:
            print("Subiendo PDF al backend...")
            response = requests.post(url, files=files, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ ÉXITO - PDF procesado correctamente")
                print(f"Archivo: {result.get('filename', 'N/A')}")
                print(f"Banco detectado: {result.get('banco', 'N/A')}")
                print(f"Transacciones extraídas: {len(result.get('transacciones_extraidas', []))}")
                print(f"Mensaje: {result.get('message', 'N/A')}")
                
                # Mostrar las transacciones extraídas
                if result.get('transacciones_extraidas'):
                    print("\n📊 TRANSACCIONES EXTRAÍDAS:")
                    for i, txn in enumerate(result['transacciones_extraidas'], 1):
                        print(f"{i}. {txn.get('description', 'N/A')} - ${txn.get('amount', 0):,.2f} - {txn.get('category', 'N/A')}")
                
                # Mostrar parte del texto extraído
                texto_extraido = result.get('texto_extraido', '')
                if texto_extraido:
                    print(f"\n📄 TEXTO EXTRAÍDO (primeros 500 caracteres):")
                    print(texto_extraido[:500] + "..." if len(texto_extraido) > 500 else texto_extraido)
                
            else:
                print(f"\n❌ ERROR - Status Code: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error: {error_detail}")
                except:
                    print(f"Error: {response.text}")
                    
        except requests.exceptions.ConnectionError:
            print("❌ ERROR: No se pudo conectar al backend. Asegúrate de que esté corriendo en http://localhost:8000")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_pdf_upload() 