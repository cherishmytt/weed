from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.import_service import import_country_boundaries, import_fire_csv


def main():
    settings = get_settings()
    db = SessionLocal()
    try:
        boundary_path = Path(settings.sample_country_geojson_path)
        fire_path = Path(settings.sample_fire_csv_path)
        if boundary_path.exists():
            import_country_boundaries(db, boundary_path.name, boundary_path.read_bytes())
        if fire_path.exists():
            import_fire_csv(db, fire_path.name, fire_path.read_bytes())
        print("Sample data imported.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
