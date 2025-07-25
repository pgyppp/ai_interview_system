import re
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from werkzeug.security import generate_password_hash, check_password_hash

import jwt
import re
from database.models import UserCreate, VerificationCodeCreate, User, VerificationCode
from services.email_service import EmailService, VERIFICATION_CODE_CONFIG
from database.crud import CRUD
from config.db_config import SECRET_KEY, ALGORITHM

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.crud = CRUD(db)

    def validate_register(self, user: UserCreate, verification_code: str):
        # 检查验证码是否正确
        verification = self.crud.get_verification_code(user.email, verification_code)
        if not verification:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

        # 检查用户名和邮箱是否已存在
        if self.crud.get_user_by_username(user.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
        if self.crud.get_user_by_email(user.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册")

        # 创建新用户
        hashed_password = generate_password_hash(user.password)
        user.password = hashed_password # Update the password in the Pydantic model
        new_user = self.crud.create_user(user)
        self.crud.delete_verification_code(verification.id)  # 删除已使用的验证码
        return new_user

    def send_verification_code(self, email: str):
        # 验证邮箱格式
        if not email or not re.match(r'^[a-zA-Z0-9]+([._-][a-zA-Z0-9]+)*@qq\.com$', email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='请输入有效的QQ邮箱')

        # 检查是否有最近发送的验证码（防止频繁请求）
        recent_code = self.crud.get_latest_verification_code(email)
        if recent_code:
            current_time = datetime.datetime.now()
            time_diff = (current_time - recent_code.created_at).total_seconds()
            if time_diff < 60:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"请求过于频繁，请{60-int(time_diff)}秒后再试")

        # 生成验证码
        email_service = EmailService()
        code = email_service.generate_verification_code(VERIFICATION_CODE_CONFIG['code_length'])

        # 存储验证码到数据
        try:
            self.crud.create_verification_code(email, code)

        except Exception as e:
            print(f"保存验证码 {code} 到数据库失败: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="验证码保存失败")

        # 发送邮件
        success, message = email_service.send_verification_email(email, code)
        if not success:
            # self.db.rollback() # CRUD methods handle commit/rollback internally
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    def login_user(self, email: str, password: str):
        user = self.crud.get_user_by_email(email)
        if not user or not check_password_hash(user.password, password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
        
        access_token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": access_token, "user": user}