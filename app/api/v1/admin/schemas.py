from pydantic import BaseModel, EmailStr
from typing import Optional

# ---------- CREATE ----------
class StoreCreateSchema(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: str


# ---------- UPDATE (PARTIAL) ----------
class StoreUpdateSchema(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


# ---------- RESPONSE ----------
class StoreResponseSchema(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    address: str
    is_active: bool
    is_approved: bool

class AdminLoginSchema(BaseModel):
    email: EmailStr
    password: str