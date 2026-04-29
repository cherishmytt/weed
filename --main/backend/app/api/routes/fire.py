import csv
import io
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import FirePoint, User
from app.schemas.fire import FireFilterOptionsOut, FireListResponse, FirePointOut
from app.services.fire_query_service import (
    apply_fire_filters,
    count_fire_points,
    get_data_anchor_datetime,
    get_filter_options,
    make_fire_query_params,
)
from app.services.fire_detail_service import get_related_fire_context


router = APIRouter()


@router.get("/filter-options", response_model=FireFilterOptionsOut)
def filter_options(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_filter_options(db)


@router.get("/list", response_model=FireListResponse)
def get_fire_list(
    page: int = 1,
    page_size: int = Query(default=20, le=200),
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    batch_id: int | None = None,
    bbox: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params = make_fire_query_params(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        source_product=source_product,
        area_label=area_label,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        daynight=daynight,
        country_name=country_name,
        batch_id=batch_id,
        bbox=bbox,
    )
    stmt = apply_fire_filters(select(FirePoint).order_by(FirePoint.acq_datetime.desc()), params=params)
    total = count_fire_points(db, stmt)
    items = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return FireListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/latest", response_model=list[FirePointOut])
def latest_fire_points(
    hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=1000, ge=1, le=8000),
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params = make_fire_query_params(
        source_product=source_product,
        area_label=area_label,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        daynight=daynight,
        country_name=country_name,
    )
    latest_time = get_data_anchor_datetime(db, params=params)
    if not latest_time:
        return []
    since = latest_time - timedelta(hours=hours)
    stmt = apply_fire_filters(
        select(FirePoint)
        .where(FirePoint.acq_datetime.between(since, latest_time))
        .order_by(FirePoint.acq_datetime.desc())
        .limit(limit),
        params=params,
    )
    return db.execute(stmt).scalars().all()


@router.get("/range", response_model=list[FirePointOut])
def range_fire_points(
    start: datetime,
    end: datetime,
    limit: int = Query(default=5000, ge=1, le=12000),
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    bbox: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params = make_fire_query_params(
        datetime_start=start,
        datetime_end=end,
        source_product=source_product,
        area_label=area_label,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        daynight=daynight,
        country_name=country_name,
        bbox=bbox,
    )
    stmt = apply_fire_filters(select(FirePoint).order_by(FirePoint.acq_datetime.desc()).limit(limit), params=params)
    return db.execute(stmt).scalars().all()


@router.get("/bbox", response_model=list[FirePointOut])
def bbox_fire_points(
    bbox: str | None = None,
    min_lon: float | None = None,
    min_lat: float | None = None,
    max_lon: float | None = None,
    max_lat: float | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    limit: int = Query(default=3000, ge=1, le=12000),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params = make_fire_query_params(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        source_product=source_product,
        area_label=area_label,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        daynight=daynight,
        country_name=country_name,
        bbox=bbox,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )
    stmt = apply_fire_filters(select(FirePoint).order_by(FirePoint.acq_datetime.desc()).limit(limit), params=params)
    return db.execute(stmt).scalars().all()


@router.get("/export")
def export_fire_csv(
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    batch_id: int | None = None,
    bbox: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    params = make_fire_query_params(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        source_product=source_product,
        area_label=area_label,
        satellite=satellite,
        instrument=instrument,
        confidence=confidence,
        daynight=daynight,
        country_name=country_name,
        batch_id=batch_id,
        bbox=bbox,
    )
    stmt = apply_fire_filters(select(FirePoint).order_by(FirePoint.acq_datetime.desc()), params=params)
    rows = db.execute(stmt.limit(50000)).scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "latitude",
            "longitude",
            "bright_ti4",
            "scan",
            "track",
            "acq_date",
            "acq_time",
            "acq_time_padded",
            "acq_datetime",
            "satellite",
            "instrument",
            "confidence",
            "version",
            "bright_ti5",
            "frp",
            "daynight",
            "country_name",
            "country_code",
            "source_product",
            "area_label",
            "source_file",
            "import_batch_id",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.latitude,
                row.longitude,
                row.bright_ti4,
                row.scan,
                row.track,
                row.acq_date,
                row.acq_time,
                row.acq_time_padded,
                row.acq_datetime,
                row.satellite,
                row.instrument,
                row.confidence,
                row.version,
                row.bright_ti5,
                row.frp,
                row.daynight,
                row.country_name,
                row.country_code,
                row.source_product,
                row.area_label,
                row.source_file,
                row.import_batch_id,
            ]
        )
    output.seek(0)
    file_name = f"fire-points-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@router.get("/{fire_id}", response_model=FirePointOut)
def get_fire_detail(fire_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fire_point = db.get(FirePoint, fire_id)
    if not fire_point:
        raise HTTPException(status_code=404, detail="火点不存在")
    return fire_point


@router.get("/{fire_id}/related")
def get_fire_related(fire_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = get_related_fire_context(db, fire_id)
    if not payload:
        raise HTTPException(status_code=404, detail="火点不存在")
    return payload


@router.delete("/{fire_id}")
def delete_fire_point(fire_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fire_point = db.get(FirePoint, fire_id)
    if not fire_point:
        raise HTTPException(status_code=404, detail="火点不存在")
    db.delete(fire_point)
    db.commit()
    return {"message": "删除成功"}
