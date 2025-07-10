import requests
import json

# URL base del backend
BASE_URL = "http://localhost:8000"

def test_transaction_creation():
    """Prueba la creación de transacciones con categorización automática"""
    
    # 1. Login para obtener token
    print("=== Login ===")
    login_data = {
        "username": "nuevo@correo.com",
        "password": "miclave123"
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code != 200:
        print(f"Error en login: {response.status_code} - {response.text}")
        return
    
    token = response.json().get("access_token")
    print(f"Token obtenido: {token[:20]}...")
    
    # 2. Crear transacción con categoría
    print("\n=== Creando transacción con categoría ===")
    transaction_data = {
        "fecha": "2025-01-15",
        "descripcion": "Comida en restaurante mexicano",
        "monto": -45.50,
        "categoria": "Comida y Restaurantes"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/usuarios/2/transacciones/", 
        json=transaction_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Transacción creada: {result}")
    else:
        print(f"Error: {response.text}")
    
    # 3. Listar transacciones para verificar
    print("\n=== Listando transacciones ===")
    response = requests.get(
        f"{BASE_URL}/usuarios/2/transacciones/",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        transactions = response.json()
        print(f"Transacciones encontradas: {len(transactions)}")
        for txn in transactions:
            categoria_nombre = "Sin categoría"
            if txn.get('categoria'):
                categoria_nombre = txn['categoria'].get('nombre', 'Sin categoría')
            print(f"- {txn['descripcion']}: ${txn['monto']} | Categoría: {categoria_nombre}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_transaction_creation() 