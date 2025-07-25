from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from database.database import get_db
from database.models import UserCreate
from services.auth_service import AuthService
from pydantic import BaseModel, EmailStr
import time

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    email: str
    verification_code: str

class LoginRequest(BaseModel):
    email: str
    password: str

class SendVerificationCodeRequest(BaseModel):
    email: str

@router.post("/register")
async def register(request: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两次输入的密码不一致")
    
    auth_service = AuthService(db);
    user_create = UserCreate(username=request.username, password=request.password, email=request.email)
    try:
        new_user = auth_service.validate_register(user_create, request.verification_code)
        return {"message": "注册成功", "user": new_user.username}
    except HTTPException as e:
        raise e

@router.post("/send_verification_code")
async def send_code(request: SendVerificationCodeRequest, db: Annotated[Session, Depends(get_db)]):
    auth_service = AuthService(db)
    try:
        auth_service.send_verification_code(request.email)
        return {"message": "验证码已发送到您的邮箱"}
    except HTTPException as e:
        raise e

@router.post("/login")
async def login(request: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    auth_service = AuthService(db)
    try:
        user_info = auth_service.login_user(request.email, request.password)
        return {"message": "登录成功", "token": user_info["access_token"], "user": user_info["user"].username, "redirect": "dashboard.html", "expiration": int(time.time() * 1000) + 3600 * 1000} # 1 hour expiration
    except HTTPException as e:
        raise e