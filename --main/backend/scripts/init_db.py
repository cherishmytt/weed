from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.schema_compat import ensure_schema_compatibility
from app.db.session import SessionLocal, engine
from app.models import SysConfig, User
from app.models.base import Base


def main():
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
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
                    remark="Open-Meteo 展示字段",
                )
            )
        db.commit()
        print("Database initialized successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
