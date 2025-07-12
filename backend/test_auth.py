import pytest
import requests
import json

# URL base del backend
BASE_URL = "http://localhost:8000"

@pytest.fixture
def auth_token():
    """Fixture para obtener un token de autenticación"""
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    # No return

@pytest.fixture
def user_id():
    """Fixture para el ID del usuario de prueba"""
    return 1

def test_login():
    """Prueba el login con diferentes usuarios"""
    
    # Usuario 1
    print("=== Probando login con prueba_front@correo.com ===")
    login_data = {
        "username": "prueba_front@correo.com",
        "password": "claveFront123"
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Token obtenido: {token[:20]}...")
        assert token is not None
    else:
        print(f"Error: {response.text}")
        assert False, f"Login falló con status {response.status_code}"
    
    # Usuario 2 - probar con un usuario que no existe para verificar manejo de errores
    print("\n=== Probando login con usuario inexistente ===")
    login_data = {
        "username": "usuario_inexistente@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    print(f"Status: {response.status_code}")
    assert response.status_code == 401, "Login con usuario inexistente debería fallar con 401"

def test_transactions(auth_token, user_id):
    """Prueba obtener transacciones con el token"""
    if not auth_token:
        pytest.skip("No hay token válido para la prueba")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/transactions/", headers=headers)
    print(f"\n=== Probando obtener transacciones ===")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        transactions = response.json()
        print(f"Transacciones obtenidas: {len(transactions)}")
        assert isinstance(transactions, list)
    else:
        print(f"Error: {response.text}")
        assert False, f"Obtener transacciones falló con status {response.status_code}" 