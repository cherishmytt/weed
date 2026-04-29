from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from app.models import FirePoint


@dataclass(slots=True)
class FireQueryParams:
    start_date: date | None = None
    end_date: date | None = None
    satellite: str | None = None
    instrument: str | None = None
    confidence: str | None = None
    daynight: str | None = None
    country_name: str | None = None
    batch_id: int | None = None
    datetime_start: datetime | None = None
    datetime_end: datetime | None = None
    source_product: str | None = None
    area_label: str | None = None
    bbox: tuple[float, float, float, float] | None = None


def normalize_area_label(value: str | None) -> str | None:
    raw = (value or "").strip().lower()
    if not raw:
        return None
    raw = raw.replace("-", "_").replace(" ", "_")
    alias_map = {
        "seasia_snpp": "seasia",
        "world_snpp": "world",
        "australia_snpp": "australia",
        "south_america_snpp": "south_america",
        "seasia_noaa20": "seasia",
        "world_noaa20": "world",
        "australia_noaa20": "australia",
        "south_america_noaa20": "south_america",
    }
    return alias_map.get(raw, raw)


def expand_area_aliases(value: str | None) -> list[str]:
    normalized = normalize_area_label(value)
    if not normalized:
        return []

    aliases = {
        normalized,
        f"{normalized}_snpp",
        f"{normalized}_noaa20",
    }
    return sorted(aliases)


def normalize_optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized or normalized.lower() == "all":
        return None
    return normalized


def coalesce_date_filters(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
) -> tuple[date | None, date | None]:
    return start_date or date_start, end_date or date_end


def parse_bbox(
    *,
    bbox: str | None = None,
    min_lon: float | None = None,
    min_lat: float | None = None,
    max_lon: float | None = None,
    max_lat: float | None = None,
) -> tuple[float, float, float, float] | None:
    if bbox:
        parts = [part.strip() for part in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox 参数格式应为 min_lon,min_lat,max_lon,max_lat")
        values = tuple(float(part) for part in parts)
        return values  # type: ignore[return-value]
    if None not in (min_lon, min_lat, max_lon, max_lat):
        return float(min_lon), float(min_lat), float(max_lon), float(max_lat)
    return None


def range_to_datetimes(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[datetime | None, datetime | None]:
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    return start_dt, end_dt


def make_fire_query_params(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    daynight: str | None = None,
    country_name: str | None = None,
    batch_id: int | None = None,
    datetime_start: datetime | None = None,
    datetime_end: datetime | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    bbox: str | None = None,
    min_lon: float | None = None,
    min_lat: float | None = None,
    max_lon: float | None = None,
    max_lat: float | None = None,
) -> FireQueryParams:
    normalized_start, normalized_end = coalesce_date_filters(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    return FireQueryParams(
        start_date=normalized_start,
        end_date=normalized_end,
        satellite=normalize_optional_text(satellite),
        instrument=normalize_optional_text(instrument),
        confidence=normalize_optional_text(confidence),
        daynight=normalize_optional_text(daynight),
        country_name=normalize_optional_text(country_name),
        batch_id=batch_id,
        datetime_start=datetime_start,
        datetime_end=datetime_end,
        source_product=normalize_optional_text(source_product),
        area_label=normalize_area_label(area_label),
        bbox=parse_bbox(
            bbox=bbox,
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
        ),
    )


def build_fire_conditions(params: FireQueryParams) -> list:
    conditions = []
    if params.start_date:
        conditions.append(FirePoint.acq_date >= params.start_date)
    if params.end_date:
        conditions.append(FirePoint.acq_date <= params.end_date)
    if params.satellite:
        conditions.append(FirePoint.satellite == params.satellite)
    if params.instrument:
        conditions.append(FirePoint.instrument == params.instrument)
    if params.confidence:
        conditions.append(FirePoint.confidence == params.confidence)
    if params.daynight:
        conditions.append(FirePoint.daynight == params.daynight)
    if params.country_name:
        conditions.append(FirePoint.country_name == params.country_name)
    if params.batch_id:
        conditions.append(FirePoint.import_batch_id == params.batch_id)
    if params.datetime_start:
        conditions.append(FirePoint.acq_datetime >= params.datetime_start)
    if params.datetime_end:
        conditions.append(FirePoint.acq_datetime <= params.datetime_end)
    if params.source_product:
        conditions.append(FirePoint.source_product == params.source_product)
    if params.area_label:
        area_aliases = expand_area_aliases(params.area_label)
        if area_aliases:
            conditions.append(FirePoint.area_label.in_(area_aliases))
    if params.bbox:
        min_lon, min_lat, max_lon, max_lat = params.bbox
        conditions.extend(
            [
                FirePoint.longitude >= min_lon,
                FirePoint.longitude <= max_lon,
                FirePoint.latitude >= min_lat,
                FirePoint.latitude <= max_lat,
            ]
        )
    return conditions


def apply_fire_filters(stmt: Select, **kwargs) -> Select:
    params = kwargs.get("params") if isinstance(kwargs.get("params"), FireQueryParams) else make_fire_query_params(**kwargs)
    conditions = build_fire_conditions(params)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


def get_data_anchor_datetime(db: Session, **kwargs) -> datetime | None:
    stmt = apply_fire_filters(select(func.max(FirePoint.acq_datetime)), **kwargs)
    return db.execute(stmt).scalar_one_or_none()


def get_data_anchor_date(db: Session, **kwargs) -> date | None:
    stmt = apply_fire_filters(select(func.max(FirePoint.acq_date)), **kwargs)
    return db.execute(stmt).scalar_one_or_none()


def get_latest_fire_points(db: Session, *, hours: int = 24, limit: int = 1000, **kwargs):
    latest_time = get_data_anchor_datetime(db, **kwargs)
    if not latest_time:
        return []
    since = latest_time - timedelta(hours=hours)
    stmt = (
        select(FirePoint)
        .where(FirePoint.acq_datetime.between(since, latest_time))
        .order_by(FirePoint.acq_datetime.desc())
        .limit(limit)
    )
    stmt = apply_fire_filters(stmt, **kwargs)
    return db.execute(stmt).scalars().all()


def get_bbox_fire_points(db: Session, *, limit: int = 3000, **kwargs):
    stmt = select(FirePoint).order_by(FirePoint.acq_datetime.desc())
    stmt = apply_fire_filters(stmt, **kwargs)
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


def count_fire_points(db: Session, stmt: Select) -> int:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    return db.execute(count_stmt).scalar_one()


def get_filter_options(db: Session) -> dict:
    raw_area_labels = [
        row[0]
        for row in db.execute(
            select(FirePoint.area_label)
            .where(FirePoint.area_label.is_not(None))
            .distinct()
            .order_by(FirePoint.area_label.asc())
        ).all()
    ]
    area_labels = sorted({normalize_area_label(value) for value in raw_area_labels if normalize_area_label(value)})
    source_products = [
        row[0]
        for row in db.execute(
            select(FirePoint.source_product)
            .where(FirePoint.source_product.is_not(None))
            .distinct()
            .order_by(FirePoint.source_product.asc())
        ).all()
    ]
    satellites = [
        row[0]
        for row in db.execute(
            select(FirePoint.satellite)
            .where(FirePoint.satellite.is_not(None))
            .distinct()
            .order_by(FirePoint.satellite.asc())
        ).all()
    ]
    instruments = [
        row[0]
        for row in db.execute(
            select(FirePoint.instrument)
            .where(FirePoint.instrument.is_not(None))
            .distinct()
            .order_by(FirePoint.instrument.asc())
        ).all()
    ]
    min_date = db.execute(select(func.min(FirePoint.acq_date))).scalar_one_or_none()
    max_date = db.execute(select(func.max(FirePoint.acq_date))).scalar_one_or_none()
    return {
        "area_labels": area_labels,
        "source_products": source_products,
        "satellites": satellites,
        "instruments": instruments,
        "date_min": min_date,
        "date_max": max_date,
    }
