from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.services.weather_service import get_hotspot_center_weather, get_point_weather


router = APIRouter()


@router.get("/point")
def point_weather(
    latitude: float,
    longitude: float,
    _: User = Depends(get_current_user),
):
    return get_point_weather(latitude, longitude)


@router.get("/hotspot-center")
def hotspot_center_weather(
    hotspot_id: str = Query(alias="hotspotId"),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_hotspot_center_weather(db, hotspot_id)
