from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


FIRE_POINT_COLUMNS = {
    "acq_time_padded": "ALTER TABLE fire_points ADD COLUMN acq_time_padded VARCHAR(8) NULL AFTER acq_time",
    "source_product": "ALTER TABLE fire_points ADD COLUMN source_product VARCHAR(60) NULL AFTER country_code",
    "area_label": "ALTER TABLE fire_points ADD COLUMN area_label VARCHAR(60) NULL AFTER source_product",
}

FIRE_POINT_INDEXES = {
    "idx_fire_acq_datetime": "CREATE INDEX idx_fire_acq_datetime ON fire_points (acq_datetime)",
    "idx_fire_area_label": "CREATE INDEX idx_fire_area_label ON fire_points (area_label)",
    "idx_fire_source_product": "CREATE INDEX idx_fire_source_product ON fire_points (source_product)",
    "idx_fire_country_name": "CREATE INDEX idx_fire_country_name ON fire_points (country_name)",
    "idx_fire_daynight": "CREATE INDEX idx_fire_daynight ON fire_points (daynight)",
    "idx_fire_confidence": "CREATE INDEX idx_fire_confidence ON fire_points (confidence)",
    "idx_fire_area_source_time": "CREATE INDEX idx_fire_area_source_time ON fire_points (area_label, source_product, acq_datetime)",
    "idx_fire_area_time": "CREATE INDEX idx_fire_area_time ON fire_points (area_label, acq_datetime)",
    "idx_fire_area_date": "CREATE INDEX idx_fire_area_date ON fire_points (area_label, acq_date)",
    "idx_fire_country_time": "CREATE INDEX idx_fire_country_time ON fire_points (country_name, acq_datetime)",
    "idx_fire_area_time_country": "CREATE INDEX idx_fire_area_time_country ON fire_points (area_label, acq_datetime, country_name)",
    "idx_fire_area_time_daynight": "CREATE INDEX idx_fire_area_time_daynight ON fire_points (area_label, acq_datetime, daynight)",
    "idx_fire_area_time_source": "CREATE INDEX idx_fire_area_time_source ON fire_points (area_label, acq_datetime, source_product)",
    "idx_fire_area_time_date": "CREATE INDEX idx_fire_area_time_date ON fire_points (area_label, acq_datetime, acq_date)",
}


def ensure_schema_compatibility(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "fire_points" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("fire_points")}
    indexes = {index["name"] for index in inspector.get_indexes("fire_points")}

    with engine.begin() as connection:
        for column_name, ddl in FIRE_POINT_COLUMNS.items():
            if column_name not in columns:
                connection.execute(text(ddl))

        for index_name, ddl in FIRE_POINT_INDEXES.items():
            if index_name not in indexes:
                connection.execute(text(ddl))
