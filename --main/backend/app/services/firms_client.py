from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta

import httpx
from fastapi import HTTPException

from app.core.config import get_settings
from app.core.sync_catalog import resolve_area_preset


settings = get_settings()


class FirmsClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.firms_api_key
        self.base_url = settings.firms_api_base_url.rstrip("/")

    def _ensure_key(self) -> None:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="FIRMS API Key 未配置")

    def _request_text(self, path: str) -> str:
        self._ensure_key()
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, timeout=90.0, follow_redirects=True)
            response.raise_for_status()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"FIRMS 接口访问失败: {exc}") from exc
        return response.text

    def get_source_availability(self, source_product: str) -> date | None:
        text = self._request_text(f"/data_availability/csv/{self.api_key}/{source_product}")
        dates: list[date] = []
        try:
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                for value in row.values():
                    raw = (value or "").strip()
                    if len(raw) >= 10:
                        try:
                            dates.append(datetime.fromisoformat(raw[:10]).date())
                        except ValueError:
                            continue
        except Exception:
            pass

        if not dates:
            for token in text.replace("\r", "\n").split("\n"):
                raw = token.strip().split(",")[-1].strip()
                if len(raw) >= 10:
                    try:
                        dates.append(datetime.fromisoformat(raw[:10]).date())
                    except ValueError:
                        continue
        return max(dates) if dates else None

    def fetch_area_records(
        self,
        *,
        source_product: str,
        area_label: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        preset = resolve_area_preset(area_label)
        area_value = preset["bbox"]
        chunk_days = max(1, min(settings.sync_task_chunk_days, 10))
        pointer = start_date
        records: list[dict] = []

        while pointer <= end_date:
            remaining = (end_date - pointer).days + 1
            span = min(chunk_days, remaining)
            text = self._request_text(
                f"/area/csv/{self.api_key}/{source_product}/{area_value}/{span}/{pointer.isoformat()}"
            )
            reader = csv.DictReader(io.StringIO(text))
            records.extend(list(reader))
            pointer = pointer + timedelta(days=span)

        return records
