from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.services.hotspot_service import get_hotspot_detail


settings = get_settings()
_WEATHER_CACHE: dict[str, tuple[datetime, dict[str, Any]]] = {}


@dataclass(frozen=True)
class WeatherPoint:
    latitude: float
    longitude: float

    @property
    def cache_key(self) -> str:
        return f"{round(self.latitude, 2)}:{round(self.longitude, 2)}"


def _is_cache_valid(expire_at: datetime) -> bool:
    return expire_at > datetime.now(timezone.utc)


def _format_weather_payload(payload: dict[str, Any], *, point: WeatherPoint, cached: bool) -> dict[str, Any]:
    current = payload.get("current", {}) if payload else {}
    daily = payload.get("daily", {}) if payload else {}
    daily_sum = None
    if isinstance(daily.get("precipitation_sum"), list) and daily["precipitation_sum"]:
        daily_sum = daily["precipitation_sum"][0]
    return {
        "latitude": point.latitude,
        "longitude": point.longitude,
        "cached": cached,
        "temperature_2m": current.get("temperature_2m"),
        "precipitation": current.get("precipitation"),
        "precipitation_24h": daily_sum,
        "wind_speed_10m": current.get("wind_speed_10m"),
        "wind_direction_10m": current.get("wind_direction_10m"),
        "weather_time": current.get("time"),
        "source": "open-meteo",
    }


def get_point_weather(latitude: float, longitude: float) -> dict[str, Any]:
    point = WeatherPoint(latitude=latitude, longitude=longitude)
    cache = _WEATHER_CACHE.get(point.cache_key)
    if cache and _is_cache_valid(cache[0]):
        return _format_weather_payload(cache[1], point=point, cached=True)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m",
        "daily": "precipitation_sum",
        "forecast_days": 1,
        "timezone": "auto",
    }
    try:
        response = httpx.get(settings.open_meteo_url, params=params, timeout=12.0)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"天气服务暂不可用: {exc}") from exc

    _WEATHER_CACHE[point.cache_key] = (
        datetime.now(timezone.utc) + timedelta(seconds=settings.weather_cache_ttl_seconds),
        payload,
    )
    return _format_weather_payload(payload, point=point, cached=False)


def get_hotspot_center_weather(db, hotspot_id: str) -> dict[str, Any]:
    hotspot = get_hotspot_detail(db, hotspot_id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="热点区域不存在")
    payload = get_point_weather(hotspot["center_latitude"], hotspot["center_longitude"])
    payload["hotspot"] = {
        "id": hotspot["id"],
        "major_country": hotspot["major_country"],
        "fire_count": hotspot["fire_count"],
    }
    return payload
