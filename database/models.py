from datetime import datetime
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))  # 建议实际使用时加密存储
    created_at = Column(DateTime, default=datetime.now)

    evaluation_results = relationship("EvaluationResult", back_populates="user")

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_path = Column(String(255))
    evaluation_data = Column(Text)  # 存储JSON数据，需确保序列化正确
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="evaluation_results")

class VerificationCode(Base):
    __tablename__ = "verification_codes"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True)
    code = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # 修正为Pydantic V2语法

class EvaluationResultCreate(BaseModel):
    user_id: int
    video_path: str
    evaluation_data: dict

class EvaluationResultResponse(BaseModel):
    id: int
    user_id: int
    video_path: str
    evaluation_data: dict
    created_at: datetime

    class Config:
        from_attributes = True  # 修正为Pydantic V2语法

class VerificationCodeCreate(BaseModel):
    email: EmailStr
    code: str
    expires_at: datetime

class VerificationCodeResponse(BaseModel):
    id: int
    email: EmailStr
    code: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
