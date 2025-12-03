from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .routers import upload, features, detection, results, emails


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLMPhish - 混合威胁钓鱼邮件检测系统",
        description="支持传统钓鱼、LLM生成钓鱼与混合攻击链检测的后端服务",
        version="0.1.0",
    )

    # CORS 设置，开发阶段允许所有源，后续可按需收紧
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
    app.include_router(features.router, prefix="/api/features", tags=["features"])
    app.include_router(detection.router, prefix="/api/detection", tags=["detection"])
    app.include_router(results.router, prefix="/api/results", tags=["results"])
    app.include_router(emails.router, prefix="/api/emails", tags=["emails"])

    return app


app = create_app()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


