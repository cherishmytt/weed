from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trigger_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    run_type: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    estimated_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(60), nullable=True)
    current_target: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fetched_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_areas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    target_sources: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    triggered_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, server_default=func.now())

    details = relationship("SyncJobDetail", back_populates="job", cascade="all, delete-orphan")
