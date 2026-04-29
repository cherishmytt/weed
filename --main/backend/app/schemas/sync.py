from datetime import datetime

from pydantic import BaseModel


class SyncEstimateRequest(BaseModel):
    areas: list[str] | None = None
    sources: list[str] | None = None


class SyncEstimateOut(BaseModel):
    window_start: datetime
    window_end: datetime
    strategy: str
    total_tasks: int
    task_targets: list[dict]
    estimated_seconds: int
    estimated_text: str
    areas: list[str]
    sources: list[str]


class SyncRunRequest(BaseModel):
    areas: list[str] | None = None
    sources: list[str] | None = None


class SyncJobDetailOut(BaseModel):
    id: int
    area_label: str
    source_product: str
    status: str
    step: str | None
    started_at: datetime | None
    finished_at: datetime | None
    fetched_count: int
    inserted_count: int
    skipped_count: int
    deleted_count: int
    message: str | None

    model_config = {"from_attributes": True}


class SyncJobOut(BaseModel):
    id: int
    job_name: str
    trigger_time: datetime
    run_type: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    estimated_seconds: int | None
    actual_seconds: int | None
    total_tasks: int
    completed_tasks: int
    current_step: str | None
    current_target: str | None
    fetched_count: int
    inserted_count: int
    skipped_count: int
    deleted_count: int
    message: str | None
    target_areas: list[str] | None
    target_sources: list[str] | None
    details: list[SyncJobDetailOut] | None = None

    model_config = {"from_attributes": True}


class SyncStatusOut(BaseModel):
    job: SyncJobOut | None
    active: bool
    remaining_seconds: int | None = None
