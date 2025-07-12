#!/usr/bin/env python3
"""
Script de prueba para verificar que el fix de fechas funciona correctamente.
"""

import requests
import json
import os

def test_login():
    """Prueba el login para obtener un token"""
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    
    response = requests.post("http://localhost:8000/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"❌ Error en login: {response.status_code} - {response.text}")
        return None

def test_upload_pdf(token):
    """Prueba subir el PDF de Santander"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usar el PDF que ya sabemos que funciona
    pdf_path = "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ No se encontró el archivo: {pdf_path}")
        return
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("Estado de cuenta abril 2025-2.pdf", f, "application/pdf")}
        response = requests.post("http://localhost:8000/upload_pdf", headers=headers, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ PDF procesado exitosamente")
        print(f"🏦 Banco detectado: {result['banco']}")
        print(f"📊 Transacciones guardadas: {len(result['transacciones_guardadas'])}")
        
        if result['transacciones_guardadas']:
            print("\n📋 Transacciones guardadas:")
            for i, trans in enumerate(result['transacciones_guardadas'][:5], 1):
                print(f"  {i}. {trans['date']} - {trans['description'][:50]} - ${trans['amount']}")
            
            if len(result['transacciones_guardadas']) > 5:
                print(f"  ... y {len(result['transacciones_guardadas']) - 5} más")
        else:
            print("❌ No se guardaron transacciones")
            
        return result
    else:
        print(f"❌ Error subiendo PDF: {response.status_code} - {response.text}")
        return None

def main():
    print("🧪 Probando fix de fechas...")
    
    # Probar login
    token = test_login()
    if not token:
        print("❌ No se pudo obtener token. Abortando.")
        return
    
    print("✅ Login exitoso")
    
    # Probar upload
    result = test_upload_pdf(token)
    
    if result and result['transacciones_guardadas']:
        print("\n🎉 ¡Fix de fechas exitoso! Las transacciones se guardaron correctamente.")
    else:
        print("\n❌ El fix no funcionó. Revisar logs del backend.")

if __name__ == "__main__":
    main() 