import requests
import json

# URL base del backend
BASE_URL = "http://localhost:8000"

def test_login():
    """Prueba el login con diferentes usuarios"""
    
    # Usuario 1
    print("=== Probando login con test@example.com ===")
    login_data = {
        "username": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Token obtenido: {token[:20]}...")
        return token
    else:
        print(f"Error: {response.text}")
    
    # Usuario 2
    print("\n=== Probando login con prueba@gmail.com ===")
    login_data = {
        "username": "prueba@gmail.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Token obtenido: {token[:20]}...")
        return token
    else:
        print(f"Error: {response.text}")
    
    return None

def test_transactions(token, user_id):
    """Prueba obtener transacciones con el token"""
    if not token:
        print("No hay token válido")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/usuarios/{user_id}/transacciones/", headers=headers)
    print(f"\n=== Probando obtener transacciones ===")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        transactions = response.json()
        print(f"Transacciones obtenidas: {len(transactions)}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Iniciando pruebas de autenticación...")
    token = test_login()
    if token:
        test_transactions(token, 2)  # Probar con usuario ID 2 