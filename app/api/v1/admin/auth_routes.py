from fastapi import APIRouter
from app.api.v1.admin.schemas import AdminLoginSchema
from app.api.v1.admin.service import admin_login

router = APIRouter()

@router.post("/login")
async def login(payload: AdminLoginSchema):
    token = await admin_login(payload.email, payload.password)
    return {"access_token": token}
