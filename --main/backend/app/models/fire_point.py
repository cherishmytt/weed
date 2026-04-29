from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FirePoint(Base):
    __tablename__ = "fire_points"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    bright_ti4: Mapped[float | None] = mapped_column(Float, nullable=True)
    scan: Mapped[float | None] = mapped_column(Float, nullable=True)
    track: Mapped[float | None] = mapped_column(Float, nullable=True)
    acq_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    acq_time: Mapped[str] = mapped_column(String(8), nullable=False)
    acq_time_padded: Mapped[str | None] = mapped_column(String(8), nullable=True)
    acq_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    satellite: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    instrument: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bright_ti5: Mapped[float | None] = mapped_column(Float, nullable=True)
    frp: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    daynight: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)
    country_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    source_product: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    area_label: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )

    import_batch = relationship("ImportBatch")
