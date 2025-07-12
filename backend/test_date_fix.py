#!/usr/bin/env python3
"""
Script de prueba para verificar que el fix de fechas funciona correctamente.
"""

import pytest
import requests
import json
import os

@pytest.fixture
def auth_token():
    """Fixture para obtener un token de autenticación"""
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    response = requests.post("http://localhost:8000/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    # No return None, just let it return implicitly

def test_login():
    """Prueba el login para obtener un token"""
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    
    response = requests.post("http://localhost:8000/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        assert token is not None
        # No return
    else:
        print(f"❌ Error en login: {response.status_code} - {response.text}")
        assert False, f"Login falló con status {response.status_code}"


def test_upload_pdf(auth_token):
    """Prueba subir el PDF de Santander"""
    if not auth_token:
        pytest.skip("No hay token válido para la prueba")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Usar el PDF que ya sabemos que funciona
    pdf_path = "uploaded_pdfs/Estado de cuenta abril 2025-2.pdf"
    
    if not os.path.exists(pdf_path):
        pytest.skip(f"No se encontró el archivo: {pdf_path}")
    
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
            
            assert len(result['transacciones_guardadas']) > 0, "No se guardaron transacciones"
        else:
            print("❌ No se guardaron transacciones")
            assert False, "No se guardaron transacciones"
        # No return
    else:
        print(f"❌ Error subiendo PDF: {response.status_code} - {response.text}")
        assert False, f"Upload PDF falló con status {response.status_code}" 