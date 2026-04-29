from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import get_settings
from app.db.schema_compat import ensure_schema_compatibility
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.services.import_service import import_merged_fire_folder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量导入 FIRMS merged CSV 数据")
    parser.add_argument(
        "--folder",
        default=None,
        help="包含 *_merged.csv 的目录，默认使用 settings.merged_fire_data_dir",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    folder = Path(args.folder or settings.merged_fire_data_dir).resolve()

    if not folder.exists():
        raise FileNotFoundError(f"目录不存在: {folder}")

    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)

    db = SessionLocal()
    try:
        batches = import_merged_fire_folder(db, folder)
        print(f"已导入 {len(batches)} 个批次，目录：{folder}")
        for batch in batches:
            print(
                f"- 批次#{batch.id} | 文件={batch.file_name} | 状态={batch.status} | "
                f"记录数={batch.record_count} | 备注={batch.remark or ''}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
