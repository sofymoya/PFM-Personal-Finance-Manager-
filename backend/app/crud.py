from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash, verify_password

# Funciones para Usuario
def get_user(db: Session, user_id: int):
    """Obtiene un usuario por ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Obtiene un usuario por email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene lista de usuarios"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Crea un nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password, 
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    """Autentica un usuario"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Funciones para Transacción
def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Obtiene transacciones de un usuario"""
    return db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int):
    """Crea una nueva transacción"""
    db_transaction = models.Transaction(**transaction.dict(), user_id=user_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transaction(db: Session, transaction_id: int, user_id: int):
    """Obtiene una transacción específica de un usuario"""
    return db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user_id
    ).first()

def update_transaction(db: Session, transaction_id: int, user_id: int, transaction: schemas.TransactionCreate):
    """Actualiza una transacción"""
    db_transaction = get_transaction(db, transaction_id, user_id)
    if db_transaction:
        for key, value in transaction.dict().items():
            setattr(db_transaction, key, value)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int, user_id: int):
    """Elimina una transacción"""
    db_transaction = get_transaction(db, transaction_id, user_id)
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False