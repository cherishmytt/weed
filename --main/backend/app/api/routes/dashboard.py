from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.analysis_service import get_dashboard_rankings, get_dashboard_trends, get_overview
from app.services.fire_query_service import coalesce_date_filters
from app.services.hotspot_service import get_cruise_points, list_hotspots


router = APIRouter()


def _dashboard_kwargs(
    *,
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


@router.get("/summary")
def summary(
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
    return get_overview(
        db,
        **_dashboard_kwargs(
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


@router.get("/hotspots")
def hotspots(
    window: str = "24h",
    limit: int = 12,
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
        window=window,
        limit=limit,
        **_dashboard_kwargs(
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


@router.get("/rankings")
def rankings(
    country_limit: int = 8,
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
    return get_dashboard_rankings(
        db,
        country_limit=country_limit,
        **_dashboard_kwargs(
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


@router.get("/trends")
def trends(
    days: int = 7,
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
    return get_dashboard_trends(
        db,
        days=days,
        **_dashboard_kwargs(
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


@router.get("/cruise-points")
def cruise_points(
    limit: int = 8,
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
    return get_cruise_points(
        db,
        limit=limit,
        window=window,
        **_dashboard_kwargs(
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
