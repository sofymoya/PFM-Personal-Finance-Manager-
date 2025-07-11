#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models import User
from app.auth import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.email == "test_pdf@example.com").first()
        if existing_user:
            print("Usuario test_pdf@example.com ya existe")
            return
        
        # Crear nuevo usuario
        hashed_password = get_password_hash("test123")
        new_user = User(
            email="test_pdf@example.com",
            hashed_password=hashed_password,
            name="Usuario Test PDF"
        )
        
        db.add(new_user)
        db.commit()
        print("Usuario test_pdf@example.com creado exitosamente")
        print("Email: test_pdf@example.com")
        print("Password: test123")
        
    except Exception as e:
        print(f"Error creando usuario: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 