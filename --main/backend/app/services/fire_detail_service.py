from __future__ import annotations

from datetime import timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import FirePoint


def _serialize_fire_point(row: FirePoint) -> dict:
    return {
        "id": row.id,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "bright_ti4": row.bright_ti4,
        "scan": row.scan,
        "track": row.track,
        "acq_date": row.acq_date,
        "acq_time": row.acq_time,
        "acq_time_padded": row.acq_time_padded,
        "acq_datetime": row.acq_datetime,
        "satellite": row.satellite,
        "instrument": row.instrument,
        "confidence": row.confidence,
        "version": row.version,
        "bright_ti5": row.bright_ti5,
        "frp": row.frp,
        "daynight": row.daynight,
        "country_name": row.country_name,
        "country_code": row.country_code,
        "source_product": row.source_product,
        "area_label": row.area_label,
        "source_file": row.source_file,
        "import_batch_id": row.import_batch_id,
        "created_at": row.created_at,
    }


def get_related_fire_context(db: Session, fire_id: int) -> dict | None:
    current = db.get(FirePoint, fire_id)
    if not current:
        return None

    nearby_stmt = (
        select(FirePoint)
        .where(
            FirePoint.id != current.id,
            FirePoint.latitude.between(current.latitude - 1.2, current.latitude + 1.2),
            FirePoint.longitude.between(current.longitude - 1.2, current.longitude + 1.2),
            FirePoint.acq_datetime.between(
                current.acq_datetime - timedelta(days=2),
                current.acq_datetime + timedelta(days=2),
            ),
            FirePoint.area_label == current.area_label,
        )
        .order_by(FirePoint.acq_datetime.desc())
        .limit(16)
    )

    country_stmt = (
        select(FirePoint)
        .where(
            FirePoint.id != current.id,
            FirePoint.country_name == current.country_name,
            FirePoint.acq_datetime.between(
                current.acq_datetime - timedelta(days=7),
                current.acq_datetime + timedelta(days=1),
            ),
        )
        .order_by(FirePoint.acq_datetime.desc())
        .limit(12)
    )

    country_summary_stmt = select(
        func.count().label("total"),
        func.max(FirePoint.frp).label("max_frp"),
        func.avg(FirePoint.frp).label("avg_frp"),
    ).where(
        FirePoint.country_name == current.country_name,
        FirePoint.acq_datetime.between(
            current.acq_datetime - timedelta(days=7),
            current.acq_datetime + timedelta(days=1),
        ),
    )

    same_period_stmt = select(
        func.count().label("same_period_count"),
        func.count(func.distinct(FirePoint.country_name)).label("country_count"),
    ).where(
        FirePoint.area_label == current.area_label,
        FirePoint.acq_datetime.between(
            current.acq_datetime - timedelta(hours=12),
            current.acq_datetime + timedelta(hours=12),
        ),
    )

    nearby_points = db.execute(nearby_stmt).scalars().all()
    same_country_points = db.execute(country_stmt).scalars().all()
    country_summary = db.execute(country_summary_stmt).one()
    same_period_summary = db.execute(same_period_stmt).one()

    return {
        "current_fire": _serialize_fire_point(current),
        "nearby_points": [_serialize_fire_point(item) for item in nearby_points],
        "same_country_points": [_serialize_fire_point(item) for item in same_country_points],
        "summary": {
            "country_recent_total": int(country_summary.total or 0),
            "country_recent_max_frp": float(country_summary.max_frp or 0),
            "country_recent_avg_frp": float(country_summary.avg_frp or 0),
            "same_period_count": int(same_period_summary.same_period_count or 0),
            "same_period_country_count": int(same_period_summary.country_count or 0),
        },
    }
