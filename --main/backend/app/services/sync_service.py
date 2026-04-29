from __future__ import annotations

import threading
from datetime import datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.sync_catalog import SYNC_AREA_PRESETS, SYNC_SOURCE_PRESETS
from app.db.session import SessionLocal
from app.models import FirePoint, SyncJob, SyncJobDetail, User
from app.services.country_matcher import CountryMatcher
from app.services.firms_client import FirmsClient
from app.services.fire_query_service import expand_area_aliases
from app.services.import_service import build_fire_dedupe_key, build_fire_row


settings = get_settings()
_SYNC_LOCK = threading.Lock()
_ACTIVE_THREAD: threading.Thread | None = None
_ACTIVE_JOB_ID: int | None = None


def _now() -> datetime:
    return datetime.now()


def _normalize_target_values(values: list[str] | None, presets: dict[str, dict]) -> list[str]:
    normalized = [value for value in (values or []) if value in presets]
    return normalized or list(presets.keys())


def resolve_sync_targets(
    *,
    areas: list[str] | None = None,
    sources: list[str] | None = None,
) -> list[dict]:
    resolved_areas = _normalize_target_values(areas, SYNC_AREA_PRESETS)
    resolved_sources = _normalize_target_values(sources, SYNC_SOURCE_PRESETS)
    return [
        {"area_label": area_label, "source_product": source_product}
        for area_label in resolved_areas
        for source_product in resolved_sources
    ]


def _estimate_seconds(db: Session, targets: list[dict]) -> int:
    recent_jobs = db.execute(
        select(SyncJob)
        .where(SyncJob.status.in_(["success", "partial_success"]))
        .where(SyncJob.actual_seconds.is_not(None))
        .order_by(SyncJob.started_at.desc())
        .limit(6)
    ).scalars().all()

    historical_per_task = [
        max(1, int((job.actual_seconds or 0) / max(job.total_tasks or 1, 1)))
        for job in recent_jobs
        if job.actual_seconds
    ]
    base_per_task = int(sum(historical_per_task) / len(historical_per_task)) if historical_per_task else settings.sync_default_task_seconds

    total = 0
    for target in targets:
        total += base_per_task
        if target["area_label"] == "world":
            total += settings.sync_world_task_extra_seconds
    return max(total, 45)


def _format_estimated_text(seconds: int) -> str:
    low = max(1, int(seconds * 0.8))
    high = max(low, int(seconds * 1.25))
    if high < 120:
        return f"约 {low}～{high} 秒"
    return f"约 {max(1, round(low / 60))}～{max(1, round(high / 60))} 分钟"


def estimate_sync(db: Session, *, areas: list[str] | None = None, sources: list[str] | None = None) -> dict:
    trigger_time = _now()
    window_start = trigger_time - timedelta(days=settings.sync_window_days)
    targets = resolve_sync_targets(areas=areas, sources=sources)
    estimated_seconds = _estimate_seconds(db, targets)
    resolved_areas = sorted({target["area_label"] for target in targets})
    resolved_sources = sorted({target["source_product"] for target in targets})

    return {
        "window_start": window_start,
        "window_end": trigger_time,
        "strategy": f"手动触发，维持最近 {settings.sync_window_days} 天窗口；先抓取入库，再清理窗口外旧数据。",
        "total_tasks": len(targets),
        "task_targets": targets,
        "estimated_seconds": estimated_seconds,
        "estimated_text": _format_estimated_text(estimated_seconds),
        "areas": resolved_areas,
        "sources": resolved_sources,
    }


def _job_label(target: dict) -> str:
    area_name = SYNC_AREA_PRESETS[target["area_label"]]["label"]
    source_name = SYNC_SOURCE_PRESETS[target["source_product"]]["label"]
    return f"{area_name} / {source_name}"


def _load_job(db: Session, job_id: int) -> SyncJob | None:
    return db.execute(
        select(SyncJob).options(selectinload(SyncJob.details)).where(SyncJob.id == job_id)
    ).scalar_one_or_none()


def _mark_job_failed(db: Session, job: SyncJob, message: str) -> None:
    now = _now()
    job.status = "failed"
    job.finished_at = now
    job.actual_seconds = int((now - (job.started_at or job.trigger_time)).total_seconds())
    job.message = message
    for detail in job.details:
        if detail.status in {"pending", "running"}:
            detail.status = "failed"
            detail.step = "失败"
            detail.finished_at = now
            detail.message = "任务异常终止"
            db.add(detail)
    db.add(job)
    db.commit()


def _load_existing_dedupe_keys(
    db: Session,
    *,
    area_label: str,
    source_product: str,
    window_start: datetime,
    window_end: datetime,
) -> set[str]:
    aliases = expand_area_aliases(area_label) or [area_label]
    stmt = select(
        FirePoint.latitude,
        FirePoint.longitude,
        FirePoint.acq_date,
        FirePoint.acq_time_padded,
        FirePoint.satellite,
        FirePoint.instrument,
        FirePoint.source_product,
        FirePoint.area_label,
    ).where(
        FirePoint.source_product == source_product,
        FirePoint.area_label.in_(aliases),
        FirePoint.acq_datetime.between(window_start, window_end),
    )
    keys = set()
    for row in db.execute(stmt).all():
        keys.add(
            build_fire_dedupe_key(
                latitude=row.latitude,
                longitude=row.longitude,
                acq_date=row.acq_date.isoformat(),
                acq_time_padded=row.acq_time_padded,
                satellite=row.satellite,
                instrument=row.instrument,
                source_product=row.source_product,
                area_label=row.area_label,
            )
        )
    return keys


def _sync_fire_records(
    db: Session,
    *,
    matcher: CountryMatcher,
    rows: list[dict],
    area_label: str,
    source_product: str,
    source_file: str,
    trigger_time: datetime,
    window_start: datetime,
) -> tuple[int, int]:
    existing_keys = _load_existing_dedupe_keys(
        db,
        area_label=area_label,
        source_product=source_product,
        window_start=window_start,
        window_end=trigger_time,
    )

    prepared_rows: list[dict] = []
    skipped = 0

    for row in rows:
        merged_row = dict(row)
        merged_row["source_product"] = source_product
        merged_row["area_label"] = area_label
        merged_row["source_file"] = source_file
        fire_row = build_fire_row(
            merged_row,
            file_name=source_file,
            batch_id=None,
            matcher=matcher,
        )
        if fire_row["acq_datetime"] < window_start or fire_row["acq_datetime"] > trigger_time:
            skipped += 1
            continue

        dedupe_key = build_fire_dedupe_key(
            latitude=fire_row["latitude"],
            longitude=fire_row["longitude"],
            acq_date=fire_row["acq_date"].isoformat(),
            acq_time_padded=fire_row["acq_time_padded"],
            satellite=fire_row["satellite"],
            instrument=fire_row["instrument"],
            source_product=fire_row["source_product"],
            area_label=fire_row["area_label"],
        )
        if dedupe_key in existing_keys:
            skipped += 1
            continue
        existing_keys.add(dedupe_key)
        prepared_rows.append(fire_row)

    inserted = 0
    if prepared_rows:
        db.execute(FirePoint.__table__.insert(), prepared_rows)
        db.commit()
        inserted = len(prepared_rows)

    return inserted, skipped


def _latest_existing_datetime(db: Session, *, area_label: str, source_product: str) -> datetime | None:
    aliases = expand_area_aliases(area_label) or [area_label]
    stmt = select(func.max(FirePoint.acq_datetime)).where(
        FirePoint.area_label.in_(aliases),
        FirePoint.source_product == source_product,
    )
    return db.execute(stmt).scalar_one_or_none()


def _delete_outdated_rows(db: Session, *, area_label: str, source_product: str, window_start: datetime) -> int:
    aliases = expand_area_aliases(area_label) or [area_label]
    stmt = (
        delete(FirePoint)
        .where(FirePoint.area_label.in_(aliases))
        .where(FirePoint.source_product == source_product)
        .where(FirePoint.acq_datetime < window_start)
    )
    result = db.execute(stmt)
    db.commit()
    return int(result.rowcount or 0)


def _update_job_totals(job: SyncJob) -> None:
    job.fetched_count = sum(detail.fetched_count for detail in job.details)
    job.inserted_count = sum(detail.inserted_count for detail in job.details)
    job.skipped_count = sum(detail.skipped_count for detail in job.details)
    job.deleted_count = sum(detail.deleted_count for detail in job.details)
    job.completed_tasks = sum(1 for detail in job.details if detail.status in {"success", "failed", "partial_success", "skipped"})


def _run_sync_job(job_id: int) -> None:
    global _ACTIVE_JOB_ID, _ACTIVE_THREAD
    db = SessionLocal()
    try:
        job = _load_job(db, job_id)
        if not job:
            return

        matcher = CountryMatcher.from_db(db)
        client = FirmsClient()
        window_start = job.trigger_time - timedelta(days=settings.sync_window_days)
        window_end = job.trigger_time
        job.status = "running"
        job.started_at = _now()
        job.current_step = "准备同步"
        db.add(job)
        db.commit()
        db.refresh(job)

        successful_details: list[SyncJobDetail] = []

        for target in job.details:
            detail = target
            detail.started_at = _now()
            detail.status = "running"
            detail.step = "抓取"
            job.current_step = "抓取"
            job.current_target = _job_label(
                {"area_label": detail.area_label, "source_product": detail.source_product}
            )
            db.add_all([job, detail])
            db.commit()

            try:
                available_date = client.get_source_availability(detail.source_product) or window_end.date()
                effective_end = min(window_end.date(), available_date)
                if effective_end < window_start.date():
                    detail.status = "skipped"
                    detail.finished_at = _now()
                    detail.message = "当前数据源暂无落在最近 30 天窗口内的可用数据"
                    _update_job_totals(job)
                    db.add_all([job, detail])
                    db.commit()
                    continue

                latest_dt = _latest_existing_datetime(
                    db,
                    area_label=detail.area_label,
                    source_product=detail.source_product,
                )
                overlap_start = latest_dt - timedelta(hours=settings.sync_overlap_hours) if latest_dt else window_start
                fetch_start = max(window_start.date(), overlap_start.date())

                raw_rows = client.fetch_area_records(
                    source_product=detail.source_product,
                    area_label=detail.area_label,
                    start_date=fetch_start,
                    end_date=effective_end,
                )
                detail.fetched_count = len(raw_rows)
                detail.step = "入库"
                job.current_step = "入库"
                db.add_all([job, detail])
                db.commit()

                inserted, skipped = _sync_fire_records(
                    db,
                    matcher=matcher,
                    rows=raw_rows,
                    area_label=detail.area_label,
                    source_product=detail.source_product,
                    source_file=f"sync:{detail.source_product}:{detail.area_label}:{job.trigger_time.isoformat()}",
                    trigger_time=window_end,
                    window_start=window_start,
                )
                detail.inserted_count = inserted
                detail.skipped_count = skipped
                detail.finished_at = _now()
                detail.status = "success"
                detail.step = "完成"
                detail.message = f"抓取 {detail.fetched_count} 条，新增 {inserted} 条，跳过 {skipped} 条"
                successful_details.append(detail)
            except Exception as exc:
                detail.finished_at = _now()
                detail.status = "failed"
                detail.step = "失败"
                detail.message = str(exc)
            finally:
                _update_job_totals(job)
                db.add_all([job, detail])
                db.commit()

        job.current_step = "清理旧数据"
        job.current_target = "最近 30 天窗口"
        db.add(job)
        db.commit()

        for detail in successful_details:
            detail.step = "清理旧数据"
            db.add(detail)
            db.commit()
            deleted = _delete_outdated_rows(
                db,
                area_label=detail.area_label,
                source_product=detail.source_product,
                window_start=window_start,
            )
            detail.deleted_count = deleted
            detail.step = "完成"
            db.add(detail)
            db.commit()

        db.refresh(job)
        job = _load_job(db, job_id)
        _update_job_totals(job)
        failed_count = sum(1 for detail in job.details if detail.status == "failed")
        skipped_only = sum(1 for detail in job.details if detail.status == "skipped")
        job.finished_at = _now()
        job.actual_seconds = int((job.finished_at - (job.started_at or job.trigger_time)).total_seconds())
        if failed_count and failed_count == len(job.details):
            job.status = "failed"
            job.message = "所有同步任务均失败"
        elif failed_count:
            job.status = "partial_success"
            job.message = f"部分任务失败，共成功 {len(job.details) - failed_count} 项，失败 {failed_count} 项"
        else:
            job.status = "success"
            if skipped_only == len(job.details):
                job.message = "同步完成，当前窗口内没有新增数据"
            else:
                job.message = "同步完成"
        job.current_step = "完成"
        job.current_target = None
        db.add(job)
        db.commit()
    except Exception as exc:
        job = _load_job(db, job_id)
        if job:
            _mark_job_failed(db, job, f"同步异常终止: {exc}")
    finally:
        db.close()
        with _SYNC_LOCK:
            _ACTIVE_JOB_ID = None
            _ACTIVE_THREAD = None


def _ensure_no_running_job(db: Session) -> None:
    running_job = db.execute(
        select(SyncJob).where(SyncJob.status.in_(["pending", "running"])).order_by(SyncJob.trigger_time.desc())
    ).scalar_one_or_none()
    if running_job:
        raise HTTPException(status_code=409, detail="已有同步任务正在执行，请等待当前任务完成")


def run_sync_now(
    db: Session,
    *,
    triggered_by: User,
    areas: list[str] | None = None,
    sources: list[str] | None = None,
) -> SyncJob:
    global _ACTIVE_JOB_ID, _ACTIVE_THREAD
    with _SYNC_LOCK:
        if _ACTIVE_THREAD and _ACTIVE_THREAD.is_alive():
            raise HTTPException(status_code=409, detail="已有同步任务正在执行，请等待当前任务完成")
        _ensure_no_running_job(db)
        estimate = estimate_sync(db, areas=areas, sources=sources)
        now = _now()
        job = SyncJob(
            job_name=f"手动同步-{now.strftime('%Y%m%d%H%M%S')}",
            trigger_time=now,
            run_type="manual",
            status="pending",
            estimated_seconds=estimate["estimated_seconds"],
            total_tasks=estimate["total_tasks"],
            completed_tasks=0,
            current_step="等待启动",
            target_areas=estimate["areas"],
            target_sources=estimate["sources"],
            triggered_by_user_id=triggered_by.id,
            message=f"维持最近 {settings.sync_window_days} 天窗口",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        for target in estimate["task_targets"]:
            db.add(
                SyncJobDetail(
                    job_id=job.id,
                    area_label=target["area_label"],
                    source_product=target["source_product"],
                    status="pending",
                    step="等待启动",
                )
            )
        db.commit()
        db.refresh(job)

        thread = threading.Thread(target=_run_sync_job, args=(job.id,), daemon=True)
        _ACTIVE_JOB_ID = job.id
        _ACTIVE_THREAD = thread
        thread.start()
        return _load_job(db, job.id)


def get_sync_status(db: Session, *, job_id: int | None = None) -> dict:
    if job_id:
        job = _load_job(db, job_id)
    else:
        job = db.execute(
            select(SyncJob)
            .options(selectinload(SyncJob.details))
            .order_by(SyncJob.trigger_time.desc())
            .limit(1)
        ).scalar_one_or_none()

    if not job:
        return {"job": None, "active": False, "remaining_seconds": None}

    active = job.status in {"pending", "running"}
    remaining = None
    if active and job.estimated_seconds and job.started_at:
        elapsed = int((_now() - job.started_at).total_seconds())
        remaining = max(job.estimated_seconds - elapsed, 0)
    return {
        "job": job,
        "active": active,
        "remaining_seconds": remaining,
    }


def get_sync_history(db: Session, *, limit: int = 20) -> list[SyncJob]:
    return db.execute(
        select(SyncJob)
        .options(selectinload(SyncJob.details))
        .order_by(SyncJob.trigger_time.desc())
        .limit(limit)
    ).scalars().all()


def recover_stale_sync_jobs() -> None:
    db = SessionLocal()
    try:
        stale_jobs = db.execute(
            select(SyncJob).where(SyncJob.status.in_(["pending", "running"]))
        ).scalars().all()
        if not stale_jobs:
            return
        now = _now()
        for job in stale_jobs:
            job.status = "failed"
            job.finished_at = now
            job.actual_seconds = int((now - (job.started_at or job.trigger_time)).total_seconds())
            job.current_step = "中断"
            job.message = "服务重启或异常退出，任务已中断"
            for detail in job.details:
                if detail.status in {"pending", "running"}:
                    detail.status = "failed"
                    detail.finished_at = now
                    detail.step = "中断"
                    detail.message = "服务重启导致任务中断"
            db.add(job)
        db.commit()
    finally:
        db.close()
