from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.fire_query_service import coalesce_date_filters
from app.services.hotspot_service import get_hotspot_detail, list_hotspots, top_hotspots


router = APIRouter()


def _hotspot_kwargs(
    *,
    window: str = "24h",
    limit: int = 50,
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
) -> dict:
    normalized_start, normalized_end = coalesce_date_filters(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    return {
        "window": window,
        "limit": limit,
        "start_date": normalized_start,
        "end_date": normalized_end,
        "source_product": source_product,
        "area_label": area_label,
        "satellite": satellite,
        "instrument": instrument,
        "confidence": confidence,
        "daynight": daynight,
        "country_name": country_name,
    }


@router.get("/list")
def hotspot_list(
    window: str = "24h",
    limit: int = 50,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_hotspots(
        db,
        **_hotspot_kwargs(
            window=window,
            limit=limit,
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
        ),
    )


@router.get("/top")
def hotspot_top(
    window: str = "24h",
    limit: int = 10,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return top_hotspots(
        db,
        **_hotspot_kwargs(
            window=window,
            limit=limit,
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
        ),
    )


@router.get("/{hotspot_id}")
def hotspot_detail(
    hotspot_id: str,
    window: str = "24h",
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hotspot = get_hotspot_detail(
        db,
        hotspot_id,
        **_hotspot_kwargs(
            window=window,
            limit=500,
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
        ),
    )
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点区域不存在")
    return hotspot
