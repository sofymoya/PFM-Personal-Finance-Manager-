from app.database import SessionLocal
from app import crud, schemas

def crear_usuario(email, password, nombre=None):
    db = SessionLocal()
    try:
        usuario = schemas.UsuarioCreate(email=email, password=password, nombre=nombre)
        creado = crud.create_usuario(db, usuario)
        print(f"Usuario creado: {creado.email}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Cambia estos valores si lo deseas
    email = "nuevo@correo.com"
    password = "miclave123"
    nombre = "Usuario Prueba"
    crear_usuario(email, password, nombre) 