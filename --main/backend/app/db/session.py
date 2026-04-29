from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


settings = get_settings()


def ensure_database_exists() -> None:
    if settings.database_url:
      return
    server_url = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/?charset=utf8mb4"
    )
    engine_without_db = create_engine(server_url, pool_pre_ping=True, future=True, isolation_level="AUTOCOMMIT")
    with engine_without_db.connect() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_db}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    engine_without_db.dispose()

ensure_database_exists()
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)
