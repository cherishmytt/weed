from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.analysis_service import (
    get_analysis_bundle,
    get_country_bundle,
    get_country_choropleth,
    get_country_detail,
    get_country_daynight_pie,
    get_country_frp_distribution,
    get_country_source_product_pie,
    get_country_trend,
    get_country_top,
    get_daynight_pie,
    get_frp_distribution,
    get_overview,
    get_satellite_pie,
    get_source_product_pie,
    get_timeline,
)
from app.services.fire_query_service import coalesce_date_filters


router = APIRouter()


def _analysis_kwargs(
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


@router.get("/overview")
def overview(
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
        **_analysis_kwargs(
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


@router.get("/bundle")
def bundle(
    days: int = 7,
    hotspot_window: str = "7d",
    hotspot_limit: int = 8,
    include_hotspots: bool = True,
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
    return get_analysis_bundle(
        db,
        days=days,
        hotspot_window=hotspot_window,
        hotspot_limit=hotspot_limit,
        include_hotspots=include_hotspots,
        **_analysis_kwargs(
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


@router.get("/timeline")
def timeline(
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
    return get_timeline(
        db,
        days=days,
        **_analysis_kwargs(
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


@router.get("/country-top")
def country_top(
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_top(
        db,
        limit=limit,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/satellite-pie")
def satellite_pie(
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    country_name: str | None = None,
    daynight: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_satellite_pie(
        db,
        **_analysis_kwargs(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
            source_product=source_product,
            area_label=area_label,
            country_name=country_name,
            daynight=daynight,
        ),
    )


@router.get("/daynight-pie")
def daynight_pie(
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    country_name: str | None = None,
    satellite: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_daynight_pie(
        db,
        **_analysis_kwargs(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
            source_product=source_product,
            area_label=area_label,
            country_name=country_name,
            satellite=satellite,
        ),
    )


@router.get("/source-product-pie")
def source_product_pie(
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    country_name: str | None = None,
    satellite: str | None = None,
    daynight: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_source_product_pie(
        db,
        **_analysis_kwargs(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
            source_product=source_product,
            area_label=area_label,
            country_name=country_name,
            satellite=satellite,
            daynight=daynight,
        ),
    )


@router.get("/frp-distribution")
def frp_distribution(
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    country_name: str | None = None,
    satellite: str | None = None,
    daynight: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_frp_distribution(
        db,
        **_analysis_kwargs(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
            source_product=source_product,
            area_label=area_label,
            country_name=country_name,
            satellite=satellite,
            daynight=daynight,
        ),
    )


@router.get("/country-choropleth")
def country_choropleth(
    metric: str = "count",
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_choropleth(
        db,
        metric=metric,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/country-detail")
def country_detail(
    country: str,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_detail(
        db,
        country=country,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/country-bundle")
def country_bundle(
    country: str,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_bundle(
        db,
        country=country,
        days=days,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/country-trend")
def country_trend(
    country: str,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_trend(
        db,
        country=country,
        days=days,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/country-frp-distribution")
def country_frp_distribution(
    country: str,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_frp_distribution(
        db,
        country=country,
        **_analysis_kwargs(
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
        ),
    )


@router.get("/country-daynight-pie")
def country_daynight_pie(
    country: str,
    start_date: date | None = None,
    end_date: date | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    source_product: str | None = None,
    area_label: str | None = None,
    satellite: str | None = None,
    instrument: str | None = None,
    confidence: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_daynight_pie(
        db,
        country=country,
        **_analysis_kwargs(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
            source_product=source_product,
            area_label=area_label,
            satellite=satellite,
            instrument=instrument,
            confidence=confidence,
        ),
    )


@router.get("/country-source-product-pie")
def country_source_product_pie(
    country: str,
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
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_country_source_product_pie(
        db,
        country=country,
        **_analysis_kwargs(
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
        ),
    )
