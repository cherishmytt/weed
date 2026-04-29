from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "全球野火火点监测与时空分析平台"
    api_prefix: str = "/api"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    secret_key: str = "replace-with-a-strong-secret-key"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_cache_ttl_seconds: int = 900
    hotspot_grid_size_deg: float = 1.8
    hotspot_min_points: int = 4
    hotspot_cache_ttl_seconds: int = 600
    analysis_cache_ttl_seconds: int = 600
    cruise_default_limit: int = 8
    import_chunk_size: int = 2000
    sync_window_days: int = 30
    sync_overlap_hours: int = 24
    sync_task_chunk_days: int = 5
    sync_poll_interval_seconds: int = 3
    sync_default_task_seconds: int = 55
    sync_world_task_extra_seconds: int = 35
    sync_progress_cache_ttl_seconds: int = 900
    firms_api_base_url: str = "https://firms.modaps.eosdis.nasa.gov/api"
    firms_api_key: str = ""

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "your_mysql_user"
    mysql_password: str = "your_mysql_password"
    mysql_db: str = "global_fire_system"
    database_url: str | None = None

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    default_admin_username: str = "admin"
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "replace-with-admin-password"
    sample_country_geojson_path: str = str(ROOT_DIR / "data" / "ne_10m_admin_0_countries.json")
    sample_fire_csv_path: str = str(ROOT_DIR / "data" / "firms_world_1day_viirs_snpp.csv")
    merged_fire_data_dir: str = str(ROOT_DIR / "data" / "firms_downloads")

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
