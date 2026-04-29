from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user, get_db
from app.models import User
from app.schemas.sync import SyncEstimateOut, SyncEstimateRequest, SyncJobOut, SyncRunRequest, SyncStatusOut
from app.services.sync_service import estimate_sync, get_sync_history, get_sync_status, run_sync_now


router = APIRouter()


@router.post("/estimate", response_model=SyncEstimateOut)
def sync_estimate(
    payload: SyncEstimateRequest,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return estimate_sync(db, areas=payload.areas, sources=payload.sources)


@router.post("/run-now", response_model=SyncJobOut)
def sync_run_now(
    payload: SyncRunRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return run_sync_now(db, triggered_by=current_user, areas=payload.areas, sources=payload.sources)


@router.get("/status", response_model=SyncStatusOut)
def sync_status(
    job_id: int | None = Query(default=None, alias="job_id"),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return get_sync_status(db, job_id=job_id)


@router.get("/history", response_model=list[SyncJobOut])
def sync_history(
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return get_sync_history(db, limit=limit)
