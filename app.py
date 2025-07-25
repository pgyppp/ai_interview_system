from contextlib import asynccontextmanager

import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.crud import CRUD
from database.database import get_db
from database.database import Base, engine
from database.models import EvaluationResult, User
from routes import auth_routes, interview_routes, report_routes, user_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AI面试评估系统API",
    description="提供视频处理、AI多维度评估、雷达图生成和PDF报告生成的后端服务。",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，开发环境使用
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)



app.include_router(user_routes.router)
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(interview_routes.router)
app.include_router(report_routes.router)

# 挂载静态文件目录
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(current_dir, "ui")

app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")

@app.get("/ui")
async def read_ui_root():
    return FileResponse(os.path.join(ui_dir, "dashboard.html"))
app.mount("/output_reports", StaticFiles(directory="output_reports"), name="output_reports")
app.mount("/audio/questions", StaticFiles(directory="question_audio"), name="question_audio")
app.mount("/output_chart", StaticFiles(directory="output_chart"), name="output_chart")
app.mount("/img", StaticFiles(directory="img"), name="img")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the AI Interview System"}