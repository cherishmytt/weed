from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta

from sqlalchemy import Float, and_, case, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import FirePoint
from app.services.fire_query_service import (
    apply_fire_filters,
    get_data_anchor_date,
    get_data_anchor_datetime,
    make_fire_query_params,
    range_to_datetimes,
)
from app.services.hotspot_service import top_hotspots
from app.core.config import get_settings


settings = get_settings()
ANALYSIS_CACHE: dict[tuple, tuple[datetime, object]] = {}


def _cache_key(name: str, **kwargs) -> tuple:
    normalized = tuple(sorted((key, str(value)) for key, value in kwargs.items()))
    return (name, normalized)


def _get_cached(name: str, **kwargs):
    key = _cache_key(name, **kwargs)
    cached = ANALYSIS_CACHE.get(key)
    if not cached:
        return None
    expires_at, payload = cached
    if expires_at <= datetime.now():
        ANALYSIS_CACHE.pop(key, None)
        return None
    return deepcopy(payload)


def _set_cached(name: str, payload, **kwargs):
    key = _cache_key(name, **kwargs)
    ANALYSIS_CACHE[key] = (
        datetime.now() + timedelta(seconds=settings.analysis_cache_ttl_seconds),
        deepcopy(payload),
    )


def high_confidence_filter():
    return or_(func.lower(FirePoint.confidence) == "h", cast(FirePoint.confidence, Float) >= 80)


def _base_filtered_stmt(**kwargs):
    stmt = select(FirePoint)
    return apply_fire_filters(stmt, **kwargs)


def _country_kwargs(country: str, **kwargs) -> dict:
    scoped = dict(kwargs)
    scoped["country_name"] = country
    return scoped


def _datetime_range_params(**kwargs):
    params = make_fire_query_params(**kwargs)
    if params.start_date or params.end_date:
        start_dt, end_dt = range_to_datetimes(start_date=params.start_date, end_date=params.end_date)
        params.start_date = None
        params.end_date = None
        params.datetime_start = start_dt
        params.datetime_end = end_dt
    return params


def _is_high_confidence(value) -> bool:
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized == "h":
        return True
    try:
        return float(normalized) >= 80
    except ValueError:
        return False


def _frp_bucket(value) -> str | None:
    if value is None:
        return None
    if value < 5:
        return "0-5"
    if value < 20:
        return "5-20"
    if value < 50:
        return "20-50"
    if value < 100:
        return "50-100"
    return "100+"


def get_overview(db: Session, **kwargs) -> dict:
    cached = _get_cached("overview", **kwargs)
    if cached is not None:
        return cached

    base_stmt = _base_filtered_stmt(**kwargs)
    metrics_stmt = base_stmt.subquery()
    aggregate = db.execute(
        select(
            func.count().label("total"),
            func.sum(
                case(
                    (or_(func.lower(metrics_stmt.c.confidence) == "h", cast(metrics_stmt.c.confidence, Float) >= 80), 1),
                    else_=0,
                )
            ).label("high_confidence_count"),
            func.sum(case((metrics_stmt.c.daynight == "N", 1), else_=0)).label("night_count"),
            func.max(metrics_stmt.c.acq_datetime).label("latest_update"),
            func.max(metrics_stmt.c.frp).label("max_frp"),
        )
    ).one()

    latest_update = aggregate.latest_update
    latest_date = (latest_update.date() if latest_update else None) or get_data_anchor_date(db, **kwargs) or date.today()
    today_stmt = apply_fire_filters(
        select(FirePoint).where(FirePoint.acq_date == latest_date),
        **{key: value for key, value in kwargs.items() if key not in {"start_date", "end_date", "date_start", "date_end"}},
    )
    today_count = db.execute(select(func.count()).select_from(today_stmt.subquery())).scalar_one()

    payload = {
        "total_fire_points": int(aggregate.total or 0),
        "today_fire_points": today_count,
        "high_confidence_fire_points": int(aggregate.high_confidence_count or 0),
        "night_fire_points": int(aggregate.night_count or 0),
        "max_frp": aggregate.max_frp or 0,
        "latest_update": latest_update,
        "anchor_date": latest_date,
    }
    _set_cached("overview", payload, **kwargs)
    return payload


def get_timeline(
    db: Session,
    *,
    days: int = 7,
    start_date: date | None = None,
    end_date: date | None = None,
    **kwargs,
) -> list[dict]:
    cached = _get_cached("timeline", days=days, start_date=start_date, end_date=end_date, **kwargs)
    if cached is not None:
        return cached
    anchor_date = end_date or get_data_anchor_date(db, start_date=start_date, end_date=end_date, **kwargs) or date.today()
    timeline_start = start_date or (anchor_date - timedelta(days=days - 1))
    grouped = apply_fire_filters(
        select(FirePoint.acq_date, func.count().label("value"))
        .group_by(FirePoint.acq_date)
        .order_by(FirePoint.acq_date.asc()),
        params=_datetime_range_params(start_date=timeline_start, end_date=anchor_date, **kwargs),
    )
    rows = db.execute(grouped).all()
    mapping = {row.acq_date: row.value for row in rows}
    total_days = max((anchor_date - timeline_start).days + 1, 1)
    payload = [
        {"date": timeline_start + timedelta(days=index), "value": mapping.get(timeline_start + timedelta(days=index), 0)}
        for index in range(total_days)
    ]
    _set_cached("timeline", payload, days=days, start_date=start_date, end_date=end_date, **kwargs)
    return payload


def get_country_top(db: Session, *, limit: int = 10, **kwargs) -> list[dict]:
    cached = _get_cached("country_top", limit=limit, **kwargs)
    if cached is not None:
        return cached
    grouped = apply_fire_filters(
        select(FirePoint.country_name, func.count().label("value"))
        .where(FirePoint.country_name.is_not(None))
        .group_by(FirePoint.country_name)
        .order_by(func.count().desc())
        .limit(limit),
        params=_datetime_range_params(**kwargs),
    )
    payload = [{"name": row.country_name or "未知", "value": row.value} for row in db.execute(grouped).all()]
    _set_cached("country_top", payload, limit=limit, **kwargs)
    return payload


def get_satellite_pie(db: Session, **kwargs) -> list[dict]:
    cached = _get_cached("satellite_pie", **kwargs)
    if cached is not None:
        return cached
    stmt = _base_filtered_stmt(**kwargs).where(FirePoint.satellite.is_not(None))
    subquery = stmt.subquery()
    grouped = (
        select(subquery.c.satellite, func.count().label("value"))
        .group_by(subquery.c.satellite)
        .order_by(func.count().desc())
    )
    payload = [{"name": row.satellite, "value": row.value} for row in db.execute(grouped).all()]
    _set_cached("satellite_pie", payload, **kwargs)
    return payload


def get_source_product_pie(db: Session, **kwargs) -> list[dict]:
    cached = _get_cached("source_product_pie", **kwargs)
    if cached is not None:
        return cached
    grouped = apply_fire_filters(
        select(FirePoint.source_product, func.count().label("value"))
        .where(FirePoint.source_product.is_not(None))
        .group_by(FirePoint.source_product)
        .order_by(func.count().desc()),
        params=_datetime_range_params(**kwargs),
    )
    payload = [{"name": row.source_product, "value": row.value} for row in db.execute(grouped).all()]
    _set_cached("source_product_pie", payload, **kwargs)
    return payload


def get_daynight_pie(db: Session, **kwargs) -> list[dict]:
    cached = _get_cached("daynight_pie", **kwargs)
    if cached is not None:
        return cached
    grouped = apply_fire_filters(
        select(FirePoint.daynight, func.count().label("value"))
        .where(FirePoint.daynight.is_not(None))
        .group_by(FirePoint.daynight)
        .order_by(func.count().desc()),
        params=_datetime_range_params(**kwargs),
    )
    payload = [{"name": row.daynight, "value": row.value} for row in db.execute(grouped).all()]
    _set_cached("daynight_pie", payload, **kwargs)
    return payload


def get_frp_distribution(db: Session, **kwargs) -> list[dict]:
    cached = _get_cached("frp_distribution", **kwargs)
    if cached is not None:
        return cached
    bucket = case(
        (FirePoint.frp < 5, "0-5"),
        (and_(FirePoint.frp >= 5, FirePoint.frp < 20), "5-20"),
        (and_(FirePoint.frp >= 20, FirePoint.frp < 50), "20-50"),
        (and_(FirePoint.frp >= 50, FirePoint.frp < 100), "50-100"),
        else_="100+",
    ).label("bucket")
    grouped = apply_fire_filters(
        select(bucket, func.count().label("value"))
        .where(FirePoint.frp.is_not(None))
        .group_by(bucket)
        .order_by(bucket),
        params=_datetime_range_params(**kwargs),
    )
    payload = [{"name": row.bucket, "value": row.value} for row in db.execute(grouped).all()]
    _set_cached("frp_distribution", payload, **kwargs)
    return payload


def get_country_choropleth(db: Session, *, metric: str = "count", **kwargs) -> list[dict]:
    cached = _get_cached("country_choropleth", metric=metric, **kwargs)
    if cached is not None:
        return cached
    metric_expr = func.count().label("value") if metric != "avg_frp" else func.avg(FirePoint.frp).label("value")
    grouped = apply_fire_filters(
        select(FirePoint.country_name, FirePoint.country_code, metric_expr)
        .where(FirePoint.country_name.is_not(None))
        .group_by(FirePoint.country_name, FirePoint.country_code)
        .order_by(metric_expr.desc())
        ,
        params=_datetime_range_params(**kwargs),
    )
    payload = [
        {
            "name": row.country_name,
            "code": row.country_code,
            "value": float(row.value or 0),
            "metric": metric,
        }
        for row in db.execute(grouped).all()
    ]
    _set_cached("country_choropleth", payload, metric=metric, **kwargs)
    return payload


def get_country_detail(db: Session, *, country: str, start_date: date | None = None, end_date: date | None = None, **kwargs) -> dict:
    cached = _get_cached("country_detail", country=country, start_date=start_date, end_date=end_date, **kwargs)
    if cached is not None:
        return cached
    country_scope = _country_kwargs(country, **kwargs)
    stmt = _base_filtered_stmt(start_date=start_date, end_date=end_date, **country_scope)
    subquery = stmt.subquery()
    aggregate = db.execute(
        select(
            func.count().label("total"),
            func.sum(
                case(
                    (or_(func.lower(subquery.c.confidence) == "h", cast(subquery.c.confidence, Float) >= 80), 1),
                    else_=0,
                )
            ).label("high_confidence_count"),
            func.sum(case((subquery.c.daynight == "N", 1), else_=0)).label("night_count"),
            func.avg(subquery.c.frp).label("avg_frp"),
            func.max(subquery.c.frp).label("max_frp"),
            func.max(subquery.c.acq_datetime).label("latest_update"),
        )
        .select_from(subquery)
    ).one()

    anchor_date = end_date or get_data_anchor_date(db, start_date=start_date, end_date=end_date, **country_scope) or date.today()
    timeline = get_timeline(
        db,
        days=7,
        start_date=max(anchor_date - timedelta(days=6), start_date) if start_date else anchor_date - timedelta(days=6),
        end_date=anchor_date,
        **country_scope,
    )

    satellites = db.execute(
        select(subquery.c.satellite, func.count().label("value"))
        .where(subquery.c.satellite.is_not(None))
        .group_by(subquery.c.satellite)
        .order_by(func.count().desc())
    ).all()

    payload = {
        "country_name": country,
        "total_fire_points": int(aggregate.total or 0),
        "high_confidence_fire_points": int(aggregate.high_confidence_count or 0),
        "night_fire_points": int(aggregate.night_count or 0),
        "avg_frp": float(aggregate.avg_frp or 0),
        "max_frp": float(aggregate.max_frp or 0),
        "latest_update": aggregate.latest_update,
        "timeline": timeline,
        "satellites": [{"name": row.satellite, "value": row.value} for row in satellites],
    }
    _set_cached("country_detail", payload, country=country, start_date=start_date, end_date=end_date, **kwargs)
    return payload


def get_country_trend(
    db: Session,
    *,
    country: str,
    days: int = 7,
    start_date: date | None = None,
    end_date: date | None = None,
    **kwargs,
) -> list[dict]:
    cached = _get_cached(
        "country_trend",
        country=country,
        days=days,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )
    if cached is not None:
        return cached
    country_scope = _country_kwargs(country, **kwargs)
    payload = get_timeline(
        db,
        days=days,
        start_date=start_date,
        end_date=end_date,
        **country_scope,
    )
    _set_cached(
        "country_trend",
        payload,
        country=country,
        days=days,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )
    return payload


def get_country_frp_distribution(db: Session, *, country: str, **kwargs) -> list[dict]:
    cached = _get_cached("country_frp_distribution", country=country, **kwargs)
    if cached is not None:
        return cached
    payload = get_frp_distribution(db, **_country_kwargs(country, **kwargs))
    _set_cached("country_frp_distribution", payload, country=country, **kwargs)
    return payload


def get_country_daynight_pie(db: Session, *, country: str, **kwargs) -> list[dict]:
    cached = _get_cached("country_daynight_pie", country=country, **kwargs)
    if cached is not None:
        return cached
    payload = get_daynight_pie(db, **_country_kwargs(country, **kwargs))
    _set_cached("country_daynight_pie", payload, country=country, **kwargs)
    return payload


def get_country_source_product_pie(db: Session, *, country: str, **kwargs) -> list[dict]:
    cached = _get_cached("country_source_product_pie", country=country, **kwargs)
    if cached is not None:
        return cached
    payload = get_source_product_pie(db, **_country_kwargs(country, **kwargs))
    _set_cached("country_source_product_pie", payload, country=country, **kwargs)
    return payload


def get_analysis_bundle(
    db: Session,
    *,
    days: int = 7,
    hotspot_window: str = "7d",
    hotspot_limit: int = 8,
    country_limit: int = 10,
    include_hotspots: bool = True,
    **kwargs,
) -> dict:
    cached = _get_cached(
        "analysis_bundle",
        days=days,
        hotspot_window=hotspot_window,
        hotspot_limit=hotspot_limit,
        country_limit=country_limit,
        include_hotspots=include_hotspots,
        **kwargs,
    )
    if cached is not None:
        return cached

    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    row_stmt = apply_fire_filters(
        select(
            FirePoint.acq_date,
            FirePoint.acq_datetime,
            FirePoint.confidence,
            FirePoint.daynight,
            FirePoint.frp,
            FirePoint.country_name,
            FirePoint.country_code,
            FirePoint.source_product,
        ),
        params=_datetime_range_params(**kwargs),
    )
    total = 0
    high_confidence = 0
    night_count = 0
    latest_update = None
    max_frp = 0.0
    timeline_counts: dict[date, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    daynight_counts: dict[str, int] = defaultdict(int)
    country_counts: dict[tuple[str, str | None], int] = defaultdict(int)

    for row in db.execute(row_stmt):
        total += 1
        if _is_high_confidence(row.confidence):
            high_confidence += 1
        if row.daynight == "N":
            night_count += 1
        if row.acq_datetime and (latest_update is None or row.acq_datetime > latest_update):
            latest_update = row.acq_datetime
        if row.frp is not None:
            max_frp = max(max_frp, float(row.frp))
        if row.acq_date:
            timeline_counts[row.acq_date] += 1
        if row.source_product:
            source_counts[row.source_product] += 1
        if row.daynight:
            daynight_counts[row.daynight] += 1
        if row.country_name:
            country_counts[(row.country_name, row.country_code)] += 1

    anchor_date = (end_date or (latest_update.date() if latest_update else None) or date.today())
    timeline_start = start_date or (anchor_date - timedelta(days=days - 1))
    total_days = max((anchor_date - timeline_start).days + 1, 1)
    timeline = [
        {"date": timeline_start + timedelta(days=index), "value": timeline_counts.get(timeline_start + timedelta(days=index), 0)}
        for index in range(total_days)
    ]
    country_rows = sorted(
        (
            {
                "name": country_name,
                "code": country_code,
                "value": float(count),
                "metric": "count",
            }
            for (country_name, country_code), count in country_counts.items()
        ),
        key=lambda item: item["value"],
        reverse=True,
    )
    payload = {
        "overview": {
            "total_fire_points": int(total),
            "today_fire_points": int(timeline_counts.get(anchor_date, 0)),
            "high_confidence_fire_points": int(high_confidence),
            "night_fire_points": int(night_count),
            "max_frp": max_frp,
            "latest_update": latest_update,
            "anchor_date": anchor_date,
        },
        "timeline": timeline,
        "countryTop": [{"name": item["name"], "value": item["value"]} for item in country_rows[:country_limit]],
        "sourceProductPie": [
            {"name": name, "value": value}
            for name, value in sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "daynightPie": [
            {"name": name, "value": value}
            for name, value in sorted(daynight_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "choropleth": country_rows,
    }
    if include_hotspots:
        payload["hotspots"] = top_hotspots(db, limit=hotspot_limit, window=hotspot_window, **kwargs)
    _set_cached(
        "analysis_bundle",
        payload,
        days=days,
        hotspot_window=hotspot_window,
        hotspot_limit=hotspot_limit,
        country_limit=country_limit,
        include_hotspots=include_hotspots,
        **kwargs,
    )
    return payload


def get_country_bundle(
    db: Session,
    *,
    country: str,
    days: int = 7,
    **kwargs,
) -> dict:
    cached = _get_cached("country_bundle", country=country, days=days, **kwargs)
    if cached is not None:
        return cached

    start_date = kwargs.get("start_date")
    end_date = kwargs.get("end_date")
    country_scope = _country_kwargs(country, **kwargs)
    row_stmt = apply_fire_filters(
        select(
            FirePoint.acq_date,
            FirePoint.acq_datetime,
            FirePoint.confidence,
            FirePoint.daynight,
            FirePoint.frp,
            FirePoint.satellite,
            FirePoint.source_product,
        ),
        params=_datetime_range_params(**country_scope),
    )

    total = 0
    high_confidence = 0
    night_count = 0
    latest_update = None
    max_frp = 0.0
    frp_sum = 0.0
    frp_count = 0
    timeline_counts: dict[date, int] = defaultdict(int)
    frp_counts: dict[str, int] = defaultdict(int)
    daynight_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    satellite_counts: dict[str, int] = defaultdict(int)

    for row in db.execute(row_stmt):
        total += 1
        if _is_high_confidence(row.confidence):
            high_confidence += 1
        if row.daynight == "N":
            night_count += 1
        if row.acq_datetime and (latest_update is None or row.acq_datetime > latest_update):
            latest_update = row.acq_datetime
        if row.frp is not None:
            frp_value = float(row.frp)
            frp_sum += frp_value
            frp_count += 1
            max_frp = max(max_frp, frp_value)
            bucket = _frp_bucket(frp_value)
            if bucket:
                frp_counts[bucket] += 1
        if row.acq_date:
            timeline_counts[row.acq_date] += 1
        if row.daynight:
            daynight_counts[row.daynight] += 1
        if row.source_product:
            source_counts[row.source_product] += 1
        if row.satellite:
            satellite_counts[row.satellite] += 1

    anchor_date = (end_date or (latest_update.date() if latest_update else None) or date.today())
    timeline_start = start_date or (anchor_date - timedelta(days=days - 1))
    total_days = max((anchor_date - timeline_start).days + 1, 1)
    trend = [
        {"date": timeline_start + timedelta(days=index), "value": timeline_counts.get(timeline_start + timedelta(days=index), 0)}
        for index in range(total_days)
    ]

    payload = {
        "detail": {
            "country_name": country,
            "total_fire_points": int(total),
            "high_confidence_fire_points": int(high_confidence),
            "night_fire_points": int(night_count),
            "avg_frp": round(frp_sum / frp_count, 2) if frp_count else 0,
            "max_frp": max_frp,
            "latest_update": latest_update,
            "timeline": trend[-7:],
            "satellites": [
                {"name": name, "value": value}
                for name, value in sorted(satellite_counts.items(), key=lambda item: item[1], reverse=True)
            ],
        },
        "trend": trend,
        "frpDistribution": [
            {"name": bucket, "value": frp_counts.get(bucket, 0)}
            for bucket in ["0-5", "5-20", "20-50", "50-100", "100+"]
        ],
        "daynightPie": [
            {"name": name, "value": value}
            for name, value in sorted(daynight_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "sourceProductPie": [
            {"name": name, "value": value}
            for name, value in sorted(source_counts.items(), key=lambda item: item[1], reverse=True)
        ],
    }
    _set_cached("country_bundle", payload, country=country, days=days, **kwargs)
    return payload


def get_dashboard_rankings(db: Session, *, country_limit: int = 8, **kwargs) -> dict:
    cached = _get_cached("dashboard_rankings", country_limit=country_limit, **kwargs)
    if cached is not None:
        return cached
    payload = {
        "countryTop": get_country_top(db, limit=country_limit, **kwargs),
        "satellitePie": get_satellite_pie(db, **kwargs),
        "sourceProductPie": get_source_product_pie(db, **kwargs),
        "daynightPie": get_daynight_pie(db, **kwargs),
    }
    _set_cached("dashboard_rankings", payload, country_limit=country_limit, **kwargs)
    return payload


def get_dashboard_trends(
    db: Session,
    *,
    days: int = 7,
    start_date: date | None = None,
    end_date: date | None = None,
    **kwargs,
) -> dict:
    cached = _get_cached("dashboard_trends", days=days, start_date=start_date, end_date=end_date, **kwargs)
    if cached is not None:
        return cached
    latest_dt = end_date and datetime.combine(end_date, datetime.max.time()) or get_data_anchor_datetime(
        db,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    ) or datetime.now()
    timeline = get_timeline(
        db,
        days=days,
        start_date=start_date or (latest_dt.date() - timedelta(days=days - 1)),
        end_date=end_date or latest_dt.date(),
        **kwargs,
    )
    latest_stmt = apply_fire_filters(
        select(FirePoint.country_name, FirePoint.acq_datetime, FirePoint.frp)
        .order_by(FirePoint.acq_datetime.desc())
        .limit(12),
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )
    messages = [
        {
            "country_name": row.country_name or "未知区域",
            "acq_datetime": row.acq_datetime,
            "frp": row.frp,
            "message": f"{row.country_name or '未知区域'} 火点活跃，FRP {row.frp or 0:.1f}",
        }
        for row in db.execute(latest_stmt).all()
    ]
    payload = {"timeline": timeline, "messages": messages}
    _set_cached("dashboard_trends", payload, days=days, start_date=start_date, end_date=end_date, **kwargs)
    return payload
