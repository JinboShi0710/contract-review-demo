# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.api.v1.endpoints import api_router
from app.core.dependencies import AuthError


async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


class UnifyErrorFormatMiddleware(BaseHTTPMiddleware):
    """
    将 FastAPI 默认的 {"detail": ...} 格式统一为 {code, message, data}
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code in (401, 403, 404, 422) and \
                response.headers.get("content-type", "").startswith("application/json"):
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                data = json.loads(body)
                if "detail" in data and "code" not in data:
                    detail = data["detail"]
                    if isinstance(detail, dict):
                        new_body = json.dumps({
                            "code": detail.get("code", response.status_code),
                            "message": detail.get("message", str(detail)),
                            "data": None,
                        })
                    else:
                        new_body = json.dumps({
                            "code": response.status_code,
                            "message": str(detail),
                            "data": None,
                        })
                    return Response(
                        content=new_body,
                        status_code=response.status_code,
                        media_type="application/json",
                    )
            except Exception:
                pass
            return Response(
                content=body,
                status_code=response.status_code,
                media_type=response.media_type,
            )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    db = SessionLocal()
    try:
        from app.services.auth_service import init_admin
        init_admin(db)
    finally:
        db.close()
    yield
    # 关闭时
    print("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    exception_handlers={AuthError: auth_error_handler},
)

# 错误格式统一中间件（先于 CORS 加，LIFO 顺序确保它最后执行）
app.add_middleware(UnifyErrorFormatMiddleware)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo 环境允许所有来源
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(api_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
