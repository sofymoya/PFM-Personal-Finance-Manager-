from app.database import SessionLocal
from app import crud, schemas

def crear_usuario(email, password, nombre=None):
    db = SessionLocal()
    try:
        usuario = schemas.UserCreate(email=email, password=password, name=nombre)
        creado = crud.create_user(db, usuario)
        print(f"Usuario creado: {creado.email}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Usuario de prueba único
    email = "prueba_front@correo.com"
    password = "claveFront123"
    nombre = "Usuario Frontend"
    crear_usuario(email, password, nombre) 