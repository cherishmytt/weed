from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import get_password_hash
from app.db.schema_compat import ensure_schema_compatibility
from app.db.session import SessionLocal, engine
from app.models import SysConfig, User
from app.models.base import Base
from app.services.sync_service import recover_stale_sync_jobs


settings = get_settings()


def seed_defaults() -> None:
    db = SessionLocal()
    try:
        admin = db.execute(select(User).where(User.username == settings.default_admin_username)).scalar_one_or_none()
        if not admin:
            db.add(
                User(
                    username=settings.default_admin_username,
                    email=settings.default_admin_email,
                    password_hash=get_password_hash(settings.default_admin_password),
                    role="admin",
                    status="active",
                )
            )
        if not db.execute(select(SysConfig).where(SysConfig.config_key == "open_meteo_fields")).scalar_one_or_none():
            db.add(
                SysConfig(
                    config_key="open_meteo_fields",
                    config_value="temperature_2m,precipitation,wind_speed_10m,wind_direction_10m",
                    remark="火点详情天气补充字段",
                )
            )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
    seed_defaults()
    recover_stale_sync_jobs()
    yield


app = FastAPI(
    title=settings.app_name,
    description="全球野火火点监测与时空分析平台 API",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"message": settings.app_name, "docs": "/docs"}


@app.exception_handler(Exception)
async def handle_exception(_: Request, exc: Exception):
    return ORJSONResponse(status_code=500, content={"detail": f"服务器内部错误: {exc}"})
