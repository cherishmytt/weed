from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import FirePoint
from app.services.fire_query_service import apply_fire_filters, get_data_anchor_datetime


settings = get_settings()
HOTSPOT_CACHE: dict[tuple, dict] = {}


WINDOW_MAP = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@dataclass
class HotspotQuery:
    window: str = "24h"
    limit: int = 50
    min_points: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    source_product: str | None = None
    area_label: str | None = None
    satellite: str | None = None
    instrument: str | None = None
    confidence: str | None = None
    daynight: str | None = None
    country_name: str | None = None


def _resolve_window(
    db: Session,
    query: HotspotQuery,
) -> tuple[datetime, datetime]:
    if query.start_date or query.end_date:
        end_dt = datetime.combine(query.end_date or query.start_date or date.today(), time.max)
        start_dt = datetime.combine(query.start_date or query.end_date or end_dt.date(), time.min)
        return start_dt, end_dt

    anchor = get_data_anchor_datetime(
        db,
        source_product=query.source_product,
        area_label=query.area_label,
        satellite=query.satellite,
        instrument=query.instrument,
        confidence=query.confidence,
        daynight=query.daynight,
        country_name=query.country_name,
    ) or datetime.now()
    delta = WINDOW_MAP.get(query.window, WINDOW_MAP["24h"])
    return anchor - delta, anchor


def _parse_hotspot_id(hotspot_id: str) -> tuple[str, int, int] | None:
    try:
        window, lat_idx, lon_idx = hotspot_id.split(":", 2)
        return window, int(lat_idx), int(lon_idx)
    except (ValueError, TypeError):
        return None


def _bucket_bounds(lat_idx: int, lon_idx: int, grid_size: float) -> tuple[float, float, float, float]:
    min_lat = lat_idx * grid_size - 90
    max_lat = min_lat + grid_size
    min_lon = lon_idx * grid_size - 180
    max_lon = min_lon + grid_size
    return min_lat, max_lat, min_lon, max_lon


def _bucket_expressions(latitude_column, longitude_column, grid_size: float):
    lat_bucket = func.floor((latitude_column + 90.0) / grid_size)
    lon_bucket = func.floor((longitude_column + 180.0) / grid_size)
    return lat_bucket, lon_bucket


def _hotspot_base_stmt(query: HotspotQuery, *, start_dt: datetime, end_dt: datetime):
    stmt = select(
        FirePoint.id,
        FirePoint.latitude,
        FirePoint.longitude,
        FirePoint.frp,
        FirePoint.country_name,
        FirePoint.acq_datetime,
        FirePoint.area_label,
        FirePoint.source_product,
        FirePoint.satellite,
    ).where(FirePoint.acq_datetime.between(start_dt, end_dt))
    return apply_fire_filters(
        stmt,
        source_product=query.source_product,
        area_label=query.area_label,
        satellite=query.satellite,
        instrument=query.instrument,
        confidence=query.confidence,
        daynight=query.daynight,
        country_name=query.country_name,
    )


def _build_summary_rows(
    db: Session,
    query: HotspotQuery,
    *,
    start_dt: datetime,
    end_dt: datetime,
    effective_min_points: int,
    grid_size: float,
):
    subquery = _hotspot_base_stmt(query, start_dt=start_dt, end_dt=end_dt).subquery()
    lat_bucket_sq, lon_bucket_sq = _bucket_expressions(subquery.c.latitude, subquery.c.longitude, grid_size)
    stmt = (
        select(
            lat_bucket_sq.label("lat_idx"),
            lon_bucket_sq.label("lon_idx"),
            func.avg(subquery.c.latitude).label("center_latitude"),
            func.avg(subquery.c.longitude).label("center_longitude"),
            func.count().label("fire_count"),
            func.avg(subquery.c.frp).label("avg_frp"),
            func.max(subquery.c.frp).label("max_frp"),
            func.min(subquery.c.acq_datetime).label("time_start"),
            func.max(subquery.c.acq_datetime).label("time_end"),
        )
        .group_by(lat_bucket_sq, lon_bucket_sq)
        .having(func.count() >= effective_min_points)
        .order_by(func.count().desc(), func.max(subquery.c.frp).desc())
        .limit(query.limit)
    )
    return db.execute(stmt).all()


def _load_major_countries(
    db: Session,
    query: HotspotQuery,
    *,
    start_dt: datetime,
    end_dt: datetime,
    grid_size: float,
    bucket_keys: list[tuple[int, int]],
) -> dict[tuple[int, int], str | None]:
    if not bucket_keys:
        return {}
    subquery = _hotspot_base_stmt(query, start_dt=start_dt, end_dt=end_dt).subquery()
    lat_bucket, lon_bucket = _bucket_expressions(subquery.c.latitude, subquery.c.longitude, grid_size)
    bucket_filters = [and_(lat_bucket == lat_idx, lon_bucket == lon_idx) for lat_idx, lon_idx in bucket_keys]
    stmt = (
        select(
            lat_bucket.label("lat_idx"),
            lon_bucket.label("lon_idx"),
            subquery.c.country_name,
            func.count().label("value"),
        )
        .where(or_(*bucket_filters), subquery.c.country_name.is_not(None))
        .group_by(lat_bucket, lon_bucket, subquery.c.country_name)
    )
    mapping: dict[tuple[int, int], tuple[str | None, int]] = {}
    for row in db.execute(stmt).all():
        key = (int(row.lat_idx), int(row.lon_idx))
        current = mapping.get(key)
        if not current or row.value > current[1]:
            mapping[key] = (row.country_name, int(row.value))
    return {key: value[0] for key, value in mapping.items()}


def _format_hotspot_rows(rows, *, query: HotspotQuery, grid_size: float, major_countries: dict[tuple[int, int], str | None]) -> list[dict]:
    hotspots: list[dict] = []
    for row in rows:
        lat_idx = int(row.lat_idx)
        lon_idx = int(row.lon_idx)
        hotspots.append(
            {
                "id": f"{query.window}:{lat_idx}:{lon_idx}",
                "window": query.window,
                "center_latitude": round(float(row.center_latitude or 0), 4),
                "center_longitude": round(float(row.center_longitude or 0), 4),
                "fire_count": int(row.fire_count or 0),
                "avg_frp": round(float(row.avg_frp or 0), 2),
                "max_frp": round(float(row.max_frp or 0), 2),
                "major_country": major_countries.get((lat_idx, lon_idx)),
                "time_start": row.time_start,
                "time_end": row.time_end,
                "sample_fire_ids": [],
                "grid_size_deg": grid_size,
                "area_label": query.area_label,
                "source_product": query.source_product,
            }
        )
    return hotspots


def _bucket_range_conditions(latitude_column, longitude_column, lat_idx: int, lon_idx: int, grid_size: float):
    min_lat, max_lat, min_lon, max_lon = _bucket_bounds(lat_idx, lon_idx, grid_size)
    return [
        latitude_column >= min_lat,
        latitude_column < max_lat,
        longitude_column >= min_lon,
        longitude_column < max_lon,
    ]


def _cache_key(query: HotspotQuery, start_dt: datetime, end_dt: datetime, effective_min_points: int) -> tuple:
    return (
        query.window,
        query.limit,
        effective_min_points,
        start_dt.isoformat(),
        end_dt.isoformat(),
        query.source_product or "",
        query.area_label or "",
        query.satellite or "",
        query.instrument or "",
        query.confidence or "",
        query.daynight or "",
        query.country_name or "",
    )


def _build_hotspots(db: Session, query: HotspotQuery) -> list[dict]:
    start_dt, end_dt = _resolve_window(db, query)
    effective_min_points = query.min_points or settings.hotspot_min_points
    cache_key = _cache_key(query, start_dt, end_dt, effective_min_points)
    cached = HOTSPOT_CACHE.get(cache_key)
    now = datetime.now()
    if cached and cached["expires_at"] > now:
        return deepcopy(cached["data"])

    grid_size = settings.hotspot_grid_size_deg
    rows = _build_summary_rows(
        db,
        query,
        start_dt=start_dt,
        end_dt=end_dt,
        effective_min_points=effective_min_points,
        grid_size=grid_size,
    )
    if not rows:
        return []

    bucket_keys = [(int(row.lat_idx), int(row.lon_idx)) for row in rows]
    major_countries = _load_major_countries(
        db,
        query,
        start_dt=start_dt,
        end_dt=end_dt,
        grid_size=grid_size,
        bucket_keys=bucket_keys,
    )
    result = _format_hotspot_rows(rows, query=query, grid_size=grid_size, major_countries=major_countries)
    HOTSPOT_CACHE[cache_key] = {
        "expires_at": now + timedelta(seconds=settings.hotspot_cache_ttl_seconds),
        "data": deepcopy(result),
    }
    stale_keys = [key for key, value in HOTSPOT_CACHE.items() if value["expires_at"] <= now]
    for stale_key in stale_keys:
        HOTSPOT_CACHE.pop(stale_key, None)
    return result


def list_hotspots(db: Session, **kwargs) -> list[dict]:
    return _build_hotspots(db, HotspotQuery(**kwargs))


def get_hotspot_detail(db: Session, hotspot_id: str, **kwargs) -> dict | None:
    parsed = _parse_hotspot_id(hotspot_id)
    if not parsed:
        return None
    window, lat_idx, lon_idx = parsed
    query_kwargs = dict(kwargs)
    query_kwargs["window"] = window
    query = HotspotQuery(limit=500, **query_kwargs)
    start_dt, end_dt = _resolve_window(db, query)
    grid_size = settings.hotspot_grid_size_deg
    subquery = _hotspot_base_stmt(query, start_dt=start_dt, end_dt=end_dt).subquery()
    bucket_conditions = _bucket_range_conditions(subquery.c.latitude, subquery.c.longitude, lat_idx, lon_idx, grid_size)

    aggregate = db.execute(
        select(
            func.avg(subquery.c.latitude).label("center_latitude"),
            func.avg(subquery.c.longitude).label("center_longitude"),
            func.count().label("fire_count"),
            func.avg(subquery.c.frp).label("avg_frp"),
            func.max(subquery.c.frp).label("max_frp"),
            func.min(subquery.c.acq_datetime).label("time_start"),
            func.max(subquery.c.acq_datetime).label("time_end"),
        ).where(*bucket_conditions)
    ).one()
    if not aggregate.fire_count:
        return None

    dominant_country = db.execute(
        select(subquery.c.country_name, func.count().label("value"))
        .where(*bucket_conditions, subquery.c.country_name.is_not(None))
        .group_by(subquery.c.country_name)
        .order_by(func.count().desc())
        .limit(1)
    ).first()

    sample_stmt = (
        select(FirePoint)
        .where(FirePoint.acq_datetime.between(start_dt, end_dt), *_bucket_range_conditions(FirePoint.latitude, FirePoint.longitude, lat_idx, lon_idx, grid_size))
        .order_by(FirePoint.acq_datetime.desc())
        .limit(12)
    )
    sample_stmt = apply_fire_filters(
        sample_stmt,
        source_product=query.source_product,
        area_label=query.area_label,
        satellite=query.satellite,
        instrument=query.instrument,
        confidence=query.confidence,
        daynight=query.daynight,
        country_name=query.country_name,
    )
    rows = db.execute(sample_stmt).scalars().all()

    hotspot = {
        "id": hotspot_id,
        "window": query.window,
        "center_latitude": round(float(aggregate.center_latitude or 0), 4),
        "center_longitude": round(float(aggregate.center_longitude or 0), 4),
        "fire_count": int(aggregate.fire_count or 0),
        "avg_frp": round(float(aggregate.avg_frp or 0), 2),
        "max_frp": round(float(aggregate.max_frp or 0), 2),
        "major_country": dominant_country.country_name if dominant_country else None,
        "time_start": aggregate.time_start,
        "time_end": aggregate.time_end,
        "sample_fire_ids": [row.id for row in rows],
        "grid_size_deg": grid_size,
        "area_label": query.area_label,
        "source_product": query.source_product,
    }
    hotspot["sample_points"] = [
        {
            "id": row.id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "country_name": row.country_name,
            "frp": row.frp,
            "acq_datetime": row.acq_datetime,
            "source_product": row.source_product,
            "area_label": row.area_label,
        }
        for row in rows
    ]
    return hotspot


def top_hotspots(db: Session, *, limit: int = 10, **kwargs) -> list[dict]:
    return _build_hotspots(db, HotspotQuery(limit=limit, **kwargs))


def get_cruise_points(db: Session, *, limit: int | None = None, **kwargs) -> list[dict]:
    cruise_limit = limit or settings.cruise_default_limit
    points = top_hotspots(db, limit=cruise_limit, **kwargs)
    return [
        {
            "id": item["id"],
            "name": item["major_country"] or f"热点 {index + 1}",
            "longitude": item["center_longitude"],
            "latitude": item["center_latitude"],
            "fire_count": item["fire_count"],
            "max_frp": item["max_frp"],
            "area_label": item["area_label"],
            "source_product": item["source_product"],
        }
        for index, item in enumerate(points)
    ]
