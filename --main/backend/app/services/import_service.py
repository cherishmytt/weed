from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import CountryBoundary, FirePoint, ImportBatch
from app.services.country_matcher import CountryMatcher


settings = get_settings()


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


def build_fire_dedupe_key(
    *,
    latitude: float,
    longitude: float,
    acq_date: str,
    acq_time_padded: str | None,
    satellite: str | None,
    instrument: str | None,
    source_product: str | None = None,
    area_label: str | None = None,
) -> str:
    return "|".join(
        [
            f"{float(latitude):.4f}",
            f"{float(longitude):.4f}",
            acq_date,
            (acq_time_padded or "").strip(),
            (satellite or "").strip().upper(),
            (instrument or "").strip().upper(),
            (source_product or "").strip().upper(),
            normalize_area_label(area_label) or "",
        ]
    )


def safe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_time(value: str | None) -> str:
    raw = (value or "0000").strip()
    if raw.isdigit():
        raw = raw.zfill(4)
    if len(raw) == 4:
        return f"{raw[:2]}:{raw[2:]}"
    return raw


def parse_datetime(date_str: str, time_str: str) -> datetime:
    normalized_time = normalize_time(time_str).replace(":", "")
    return datetime.strptime(f"{date_str}{normalized_time}", "%Y-%m-%d%H%M")


def parse_datetime_value(row: dict) -> datetime:
    raw = (row.get("acq_datetime") or "").strip()
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", ""))
        except ValueError:
            pass
    return parse_datetime(row["acq_date"], str(row.get("acq_time")))


def infer_source_product(row: dict, file_name: str) -> str | None:
    explicit = (row.get("source_product") or "").strip()
    if explicit:
        return explicit
    sample = " ".join(filter(None, [row.get("source_file"), file_name])).upper()
    if "SNPP" in sample:
        return "VIIRS_SNPP_NRT"
    if "NOAA20" in sample or "NOAA-20" in sample or "N20" in sample:
        return "VIIRS_NOAA20_NRT"
    return None


def infer_area_label(row: dict, file_name: str) -> str | None:
    explicit = normalize_area_label(row.get("area_label"))
    if explicit:
        return explicit
    sample = " ".join(filter(None, [row.get("source_file"), file_name])).lower()
    for label in ("seasia", "world", "australia", "south_america"):
        if label in sample:
            return normalize_area_label(label)
    return None


def create_batch(
    db: Session,
    *,
    batch_name: str,
    source_type: str,
    file_name: str,
    remark: str | None = None,
) -> ImportBatch:
    batch = ImportBatch(
        batch_name=batch_name,
        source_type=source_type,
        file_name=file_name,
        remark=remark,
        status="processing",
        record_count=0,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def finish_batch(
    db: Session,
    batch: ImportBatch,
    *,
    record_count: int,
    status: str,
    remark: str | None = None,
) -> None:
    batch.record_count = record_count
    batch.status = status
    batch.remark = remark
    db.add(batch)
    db.commit()


def _flush_fire_rows(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    db.execute(insert(FirePoint), rows)


def build_fire_row(
    row: dict,
    *,
    file_name: str,
    batch_id: int | None,
    matcher: CountryMatcher,
) -> dict:
    latitude = float(row["latitude"])
    longitude = float(row["longitude"])
    acq_time_padded = (row.get("acq_time_padded") or "").strip() or normalize_time(str(row.get("acq_time")))
    acq_datetime = parse_datetime_value(row)
    country_name = (row.get("country_name") or "").strip() or None
    country_code = (row.get("country_code") or "").strip() or None
    if not country_name or not country_code:
        country = matcher.match(longitude, latitude)
        country_name = country_name or country.name
        country_code = country_code or country.code

    return {
        "latitude": latitude,
        "longitude": longitude,
        "bright_ti4": safe_float(row.get("bright_ti4")),
        "scan": safe_float(row.get("scan")),
        "track": safe_float(row.get("track")),
        "acq_date": datetime.strptime(row["acq_date"], "%Y-%m-%d").date(),
        "acq_time": normalize_time(str(row.get("acq_time"))),
        "acq_time_padded": acq_time_padded,
        "acq_datetime": acq_datetime,
        "satellite": (row.get("satellite") or "").strip() or None,
        "instrument": (row.get("instrument") or "").strip() or None,
        "confidence": (str(row.get("confidence", "")).strip() or None),
        "version": (row.get("version") or "").strip() or None,
        "bright_ti5": safe_float(row.get("bright_ti5")),
        "frp": safe_float(row.get("frp")),
        "daynight": (row.get("daynight") or "").strip() or None,
        "country_name": country_name,
        "country_code": country_code,
        "source_product": infer_source_product(row, file_name),
        "area_label": infer_area_label(row, file_name),
        "source_file": (row.get("source_file") or "").strip() or file_name,
        "import_batch_id": batch_id,
    }


def import_fire_csv(db: Session, file_name: str, content: bytes) -> ImportBatch:
    batch = create_batch(
        db,
        batch_name=f"火点导入-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        source_type="fire_csv",
        file_name=file_name,
        remark="FIRMS CSV 导入",
    )
    matcher = CountryMatcher.from_db(db)
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    buffer: list[dict] = []
    total = 0
    source_products: set[str] = set()
    area_labels: set[str] = set()
    min_dt: datetime | None = None
    max_dt: datetime | None = None
    try:
        for row in reader:
            fire_row = build_fire_row(row, file_name=file_name, batch_id=batch.id, matcher=matcher)
            source_product = fire_row.get("source_product")
            area_label = fire_row.get("area_label")
            if source_product:
                source_products.add(source_product)
            if area_label:
                area_labels.add(area_label)
            min_dt = fire_row["acq_datetime"] if min_dt is None else min(min_dt, fire_row["acq_datetime"])
            max_dt = fire_row["acq_datetime"] if max_dt is None else max(max_dt, fire_row["acq_datetime"])
            buffer.append(fire_row)
            total += 1
            if len(buffer) >= settings.import_chunk_size:
                _flush_fire_rows(db, buffer)
                buffer = []
        if buffer:
            _flush_fire_rows(db, buffer)
        db.commit()
        summary = "；".join(
            filter(
                None,
                [
                    f"source_product={','.join(sorted(source_products))}" if source_products else None,
                    f"area_label={','.join(sorted(area_labels))}" if area_labels else None,
                    f"time_range={min_dt} ~ {max_dt}" if min_dt and max_dt else None,
                ],
            )
        )
        finish_batch(db, batch, record_count=total, status="success", remark=summary or "导入完成")
        return batch
    except Exception as exc:
        db.rollback()
        finish_batch(db, batch, record_count=total, status="failed", remark=str(exc))
        raise


def import_fire_csv_files(db: Session, files: list[tuple[str, bytes]]) -> list[ImportBatch]:
    return [import_fire_csv(db, file_name, content) for file_name, content in files]


def extract_country_name(feature: dict) -> str:
    properties = feature.get("properties", {})
    return (
        properties.get("NAME_ZH")
        or properties.get("ADMIN")
        or properties.get("NAME")
        or properties.get("SOVEREIGNT")
        or "未知国家"
    )


def extract_country_code(feature: dict) -> str | None:
    properties = feature.get("properties", {})
    return properties.get("ISO_A3") or properties.get("ADM0_A3") or properties.get("WB_A3")


def import_country_boundaries(db: Session, file_name: str, content: bytes) -> ImportBatch:
    batch = create_batch(
        db,
        batch_name=f"国家边界导入-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        source_type="country_boundary",
        file_name=file_name,
        remark="国家边界 GeoJSON 导入",
    )
    payload = json.loads(content.decode("utf-8-sig"))
    features = payload.get("features", [])
    count = 0
    try:
        db.execute(delete(CountryBoundary))
        for feature in features:
            db.add(
                CountryBoundary(
                    country_name=extract_country_name(feature),
                    country_code=extract_country_code(feature),
                    geojson=feature["geometry"],
                )
            )
            count += 1
        db.commit()
        finish_batch(db, batch, record_count=count, status="success")
        return batch
    except Exception as exc:
        db.rollback()
        finish_batch(db, batch, record_count=count, status="failed", remark=str(exc))
        raise


def get_batches(db: Session) -> list[ImportBatch]:
    return db.execute(select(ImportBatch).order_by(ImportBatch.import_time.desc())).scalars().all()


def delete_batch(db: Session, batch_id: int) -> None:
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        return
    db.execute(delete(FirePoint).where(FirePoint.import_batch_id == batch_id))
    db.delete(batch)
    db.commit()


def import_merged_fire_folder(db: Session, folder_path: str | Path | None = None) -> list[ImportBatch]:
    folder = Path(folder_path or settings.merged_fire_data_dir)
    files = sorted(folder.glob("*_merged.csv"))
    imported_batches: list[ImportBatch] = []
    for file_path in files:
        imported_batches.append(import_fire_csv(db, file_path.name, file_path.read_bytes()))
    return imported_batches
