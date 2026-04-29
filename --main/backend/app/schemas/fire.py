from datetime import date, datetime

from pydantic import BaseModel


class FirePointOut(BaseModel):
    id: int
    latitude: float
    longitude: float
    bright_ti4: float | None
    scan: float | None
    track: float | None
    acq_date: date
    acq_time: str
    acq_time_padded: str | None
    acq_datetime: datetime
    satellite: str | None
    instrument: str | None
    confidence: str | None
    version: str | None
    bright_ti5: float | None
    frp: float | None
    daynight: str | None
    country_name: str | None
    country_code: str | None
    source_product: str | None
    area_label: str | None
    source_file: str | None
    import_batch_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FireListResponse(BaseModel):
    items: list[FirePointOut]
    total: int
    page: int
    page_size: int


class FireFilterOptionsOut(BaseModel):
    area_labels: list[str]
    source_products: list[str]
    satellites: list[str]
    instruments: list[str]
    date_min: date | None
    date_max: date | None
