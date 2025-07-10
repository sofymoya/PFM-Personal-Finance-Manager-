from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

# Schemas para Usuario
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schemas para Transacción
class TransactionBase(BaseModel):
    description: str
    amount: float
    date: date
    category: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schema para Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class TokenData(BaseModel):
    email: Optional[str] = None
