#!/usr/bin/env python3
import requests
import os

def test_pdf_upload():
    # Configurar la URL del backend
    base_url = 'http://localhost:8000'
    login_url = f'{base_url}/login'
    upload_url = f'{base_url}/upload_pdf'
    
    # Credenciales de prueba
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    
    print('🔐 Autenticando...')
    
    try:
        # Login
        login_response = requests.post(login_url, data=login_data)
        print('🔎 Respuesta login:', login_response.status_code, login_response.text)
        
        if login_response.status_code != 200:
            print(f'❌ Error de autenticación: {login_response.status_code}')
            print(login_response.text)
            return
        
        # Obtener token
        token = login_response.json().get('access_token')
        headers = {"Authorization": f"Bearer {token}"}
        
        print('✅ Autenticación exitosa')
        
        # Buscar el archivo PDF
        pdf_path = 'uploaded_pdfs/Estado de cuenta abril 2025-2.pdf'
        
        if not os.path.exists(pdf_path):
            print(f'❌ Archivo no encontrado: {pdf_path}')
            return
        
        print(f'📄 Subiendo PDF: {pdf_path}')
        
        # Leer el archivo
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            
            # Hacer la petición con el header de autorización
            response = requests.post(upload_url, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Resultado:')
                print(f'   Archivo: {result.get("filename", "N/A")}')
                print(f'   Banco: {result.get("banco", "N/A")}')
                print(f'   Transacciones guardadas: {len(result.get("transacciones_guardadas", []))}')
                
                # Mostrar transacciones
                for i, tx in enumerate(result.get('transacciones_guardadas', []), 1):
                    print(f'   {i}. {tx.get("date", "N/A")} - {tx.get("description", "N/A")} (${tx.get("amount", "N/A")}) [{tx.get("category", "N/A")}]')
            else:
                print(f'❌ Error: {response.status_code}')
                print(response.text)
                
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_pdf_upload() 