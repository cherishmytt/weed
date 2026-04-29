from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CountryBoundary(Base):
    __tablename__ = "country_boundaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    country_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
