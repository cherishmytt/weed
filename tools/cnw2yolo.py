#!/usr/bin/env python3
"""
Convert CropAndWeed bbox CSV annotations to YOLOv8 pose format (1 keypoint).

Input CSV row format:
    Left,Top,Right,Bottom,LabelID,StemX,StemY

Output YOLO pose row format:
    cls cx cy w h kx ky v
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # type: ignore

from PIL import Image


@dataclass(frozen=True)
class Sample:
    stem: str
    csv_path: Path
    image_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert CropAndWeed annotations to YOLOv8 pose format."
    )
    parser.add_argument(
        "--cnw-root",
        type=Path,
        default=Path("D:/yolo/cropandweed"),
        help="CropAndWeed repository root (contains cnw/ and data/).",
    )
    parser.add_argument(
        "--bbox-dataset",
        type=str,
        default="CropsOrWeed9",
        help="Dataset name under data/bboxes used for train/val (default: CropsOrWeed9).",
    )
    parser.add_argument(
        "--test-bbox-dataset",
        type=str,
        default=None,
        help=(
            "Optional dataset name under data/bboxes used as test split only "
            "(e.g. CropsOrWeed9Eval)."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("D:/yolo/datasets/cnw_pose"),
        help="Output dataset root.",
    )
    parser.add_argument(
        "--label-mode",
        choices=("dataset", "crop-weed", "weed-only"),
        default="dataset",
        help=(
            "Output label mode: dataset keeps dataset classes, crop-weed maps crops to "
            "0 and weed to 1, weed-only keeps only weed as class 0."
        ),
    )
    parser.add_argument(
        "--weed-label-id",
        type=int,
        default=8,
        help="Weed class id in the mapped dataset. For CropsOrWeed9 this is 8.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Val split ratio.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--link-mode",
        choices=("hardlink", "copy"),
        default="hardlink",
        help="How to place images into output splits.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove existing images/* and labels/* split folders before conversion.",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=500,
        help="Print progress every N images.",
    )
    return parser.parse_args()


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def reset_split_dirs(output_root: Path) -> None:
    for root_name in ("images", "labels"):
        for split in ("train", "val", "test"):
            split_dir = output_root / root_name / split
            if split_dir.exists():
                shutil.rmtree(split_dir)


def place_image(src: Path, dst: Path, mode: str) -> None:
    if dst.exists():
        dst.unlink()
    if mode == "copy":
        shutil.copy2(src, dst)
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def read_image_size(image_path: Path) -> Tuple[int, int]:
    # Prefer Pillow to reduce environment requirements. Fall back to OpenCV when needed.
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height
    except Exception:
        if cv2 is None:
            raise RuntimeError(f"Failed to read image size (Pillow): {image_path}")
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Failed to read image: {image_path}")
        height, width = image.shape[:2]
        return width, height


def scan_label_ids(bbox_dir: Path) -> Set[int]:
    label_ids: Set[int] = set()
    for csv_path in bbox_dir.glob("*.csv"):
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    label_ids.add(int(float(row[4])))
    return label_ids


def load_class_mapping(
    cnw_root: Path,
    dataset_name: str,
    observed_label_ids: Set[int],
    label_mode: str,
    weed_label_id: int,
) -> Tuple[Dict[int, int], List[str]]:
    sys.path.insert(0, str(cnw_root))
    from cnw.utilities.datasets import DATASETS  # type: ignore

    if dataset_name not in DATASETS:
        available = ", ".join(sorted(DATASETS.keys()))
        raise ValueError(f"Unknown dataset '{dataset_name}'. Available: {available}")

    dataset = DATASETS[dataset_name]
    label_ids = sorted(int(x) for x in dataset.get_label_ids())
    reindex = {old_id: new_id for new_id, old_id in enumerate(label_ids)}

    # map_dataset.py writes already-mapped class ids for CropsOrWeed9 (0..8).
    # Raw CropAndWeed annotations use source ids (1..99), so choose the mapping
    # based on the actual label ids observed in the bbox CSV files.
    if observed_label_ids and observed_label_ids.issubset(set(label_ids)):
        source_to_dataset_cls = {label_id: reindex[label_id] for label_id in label_ids}
    else:
        source_to_dataset_cls: Dict[int, int] = {}
        for source_id, target_id in dataset.mapping.items():
            target_id = int(target_id)
            source_id = int(source_id)
            if target_id in reindex:
                source_to_dataset_cls[source_id] = reindex[target_id]

    weed_dataset_cls = reindex.get(weed_label_id, weed_label_id)
    if label_mode == "dataset":
        source_to_cls = source_to_dataset_cls
        class_names = [dataset.get_label_name(old_id) for old_id in label_ids]
    elif label_mode == "crop-weed":
        source_to_cls = {
            source_id: 1 if dataset_cls == weed_dataset_cls else 0
            for source_id, dataset_cls in source_to_dataset_cls.items()
        }
        class_names = ["Crop", "Weed"]
    elif label_mode == "weed-only":
        source_to_cls = {
            source_id: 0
            for source_id, dataset_cls in source_to_dataset_cls.items()
            if dataset_cls == weed_dataset_cls
        }
        class_names = ["Weed"]
    else:
        raise ValueError(f"Unsupported label mode: {label_mode}")

    return source_to_cls, class_names


def collect_samples(bbox_dir: Path, images_dir: Path) -> Tuple[List[Sample], List[Path]]:
    samples: List[Sample] = []
    missing_images: List[Path] = []
    for csv_path in sorted(bbox_dir.glob("*.csv")):
        image_path = images_dir / f"{csv_path.stem}.jpg"
        if not image_path.exists():
            missing_images.append(csv_path)
            continue
        samples.append(Sample(stem=csv_path.stem, csv_path=csv_path, image_path=image_path))
    return samples, missing_images


def row_to_yolo(
    row: Sequence[str],
    width: int,
    height: int,
    source_to_cls: Dict[int, int],
) -> Optional[str]:
    if len(row) < 7:
        return None

    left = float(row[0])
    top = float(row[1])
    right = float(row[2])
    bottom = float(row[3])
    source_label = int(float(row[4]))
    stem_x = float(row[5])
    stem_y = float(row[6])

    cls = source_to_cls.get(source_label)
    if cls is None:
        return None

    left = max(0.0, min(float(width), left))
    right = max(0.0, min(float(width), right))
    top = max(0.0, min(float(height), top))
    bottom = max(0.0, min(float(height), bottom))
    if right <= left or bottom <= top:
        return None

    cx = clamp01(((left + right) * 0.5) / width)
    cy = clamp01(((top + bottom) * 0.5) / height)
    bw = clamp01((right - left) / width)
    bh = clamp01((bottom - top) / height)
    if bw <= 0.0 or bh <= 0.0:
        return None

    if stem_x < 0 or stem_y < 0 or stem_x > width or stem_y > height:
        kx = 0.0
        ky = 0.0
        v = 0
    else:
        kx = clamp01(stem_x / width)
        ky = clamp01(stem_y / height)
        v = 2

    return f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f} {kx:.6f} {ky:.6f} {v}"


def split_random_80_10_10(
    samples: List[Sample], train_ratio: float, val_ratio: float, seed: int
) -> Tuple[List[Sample], List[Sample], List[Sample]]:
    if train_ratio <= 0 or val_ratio <= 0 or train_ratio + val_ratio >= 1:
        raise ValueError("train_ratio and val_ratio must be >0 and train_ratio+val_ratio < 1.")

    rng = random.Random(seed)
    rng.shuffle(samples)
    total = len(samples)
    n_train = int(total * train_ratio)
    n_val = int(total * val_ratio)

    if total >= 3:
        n_train = max(1, min(total - 2, n_train))
        n_val = max(1, min(total - n_train - 1, n_val))

    train_samples = samples[:n_train]
    val_samples = samples[n_train : n_train + n_val]
    test_samples = samples[n_train + n_val :]
    return train_samples, val_samples, test_samples


def split_with_fixed_test(
    trainval_samples: List[Sample],
    fixed_test_samples: List[Sample],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> Tuple[List[Sample], List[Sample], List[Sample]]:
    if train_ratio <= 0 or val_ratio <= 0:
        raise ValueError("train_ratio and val_ratio must be >0.")

    rng = random.Random(seed)
    rng.shuffle(trainval_samples)
    total = len(trainval_samples)
    train_share = train_ratio / (train_ratio + val_ratio)
    n_train = int(total * train_share)
    if total >= 2:
        n_train = max(1, min(total - 1, n_train))

    train_samples = trainval_samples[:n_train]
    val_samples = trainval_samples[n_train:]
    test_samples = fixed_test_samples
    return train_samples, val_samples, test_samples


def convert_split(
    split_name: str,
    split_samples: Sequence[Sample],
    output_root: Path,
    source_to_cls: Dict[int, int],
    link_mode: str,
    log_every: int,
) -> Tuple[int, int, int]:
    images_out = output_root / "images" / split_name
    labels_out = output_root / "labels" / split_name
    ensure_dir(images_out)
    ensure_dir(labels_out)

    image_count = 0
    object_count = 0
    skipped_count = 0

    total = len(split_samples)
    for idx, sample in enumerate(split_samples, start=1):
        dst_image = images_out / sample.image_path.name
        place_image(sample.image_path, dst_image, mode=link_mode)

        width, height = read_image_size(sample.image_path)
        yolo_lines: List[str] = []

        with sample.csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                yolo_line = row_to_yolo(row, width, height, source_to_cls)
                if yolo_line is None:
                    skipped_count += 1
                    continue
                yolo_lines.append(yolo_line)

        label_file = labels_out / f"{sample.stem}.txt"
        label_file.write_text("\n".join(yolo_lines), encoding="utf-8")

        image_count += 1
        object_count += len(yolo_lines)

        if log_every > 0 and (idx % log_every == 0 or idx == total):
            print(f"[{split_name}] {idx}/{total} images")

    return image_count, object_count, skipped_count


def write_data_yaml(output_root: Path, class_names: Sequence[str]) -> Path:
    yaml_path = output_root / "data.yaml"
    lines = [
        f"path: {output_root.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        "kpt_shape: [1, 3]",
        "flip_idx: [0]",
        "",
        "names:",
    ]
    for idx, name in enumerate(class_names):
        safe = str(name).replace('"', '\\"')
        lines.append(f'  {idx}: "{safe}"')

    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return yaml_path


def main() -> None:
    args = parse_args()

    cnw_root = args.cnw_root.resolve()
    data_root = cnw_root / "data"
    images_dir = data_root / "images"
    bbox_dir = data_root / "bboxes" / args.bbox_dataset
    output_root = args.output_root.resolve()

    if not cnw_root.exists():
        raise FileNotFoundError(f"cnw root not found: {cnw_root}")
    if not images_dir.exists():
        raise FileNotFoundError(f"images dir not found: {images_dir}")
    if not bbox_dir.exists():
        raise FileNotFoundError(f"bbox dir not found: {bbox_dir}")

    test_bbox_dir: Optional[Path] = None
    if args.test_bbox_dataset:
        test_bbox_dir = data_root / "bboxes" / args.test_bbox_dataset
        if not test_bbox_dir.exists():
            raise FileNotFoundError(f"test bbox dir not found: {test_bbox_dir}")

    observed_label_ids = scan_label_ids(bbox_dir)
    source_to_cls, class_names = load_class_mapping(
        cnw_root=cnw_root,
        dataset_name=args.bbox_dataset,
        observed_label_ids=observed_label_ids,
        label_mode=args.label_mode,
        weed_label_id=args.weed_label_id,
    )
    main_samples, missing_main = collect_samples(bbox_dir, images_dir)

    if missing_main:
        print(f"[warn] missing images for {len(missing_main)} CSV files in {bbox_dir}")
        for path in missing_main[:10]:
            print(f"  - {path.name}")
        if len(missing_main) > 10:
            print("  ...")

    if not main_samples:
        raise RuntimeError(f"No usable samples found in: {bbox_dir}")

    if test_bbox_dir is not None:
        test_samples_fixed, missing_test = collect_samples(test_bbox_dir, images_dir)
        if missing_test:
            print(f"[warn] missing images for {len(missing_test)} test CSV files in {test_bbox_dir}")
        if not test_samples_fixed:
            raise RuntimeError(f"No usable test samples found in: {test_bbox_dir}")
        train_samples, val_samples, test_samples = split_with_fixed_test(
            trainval_samples=main_samples,
            fixed_test_samples=test_samples_fixed,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            seed=args.seed,
        )
    else:
        train_samples, val_samples, test_samples = split_random_80_10_10(
            samples=main_samples,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            seed=args.seed,
        )

    ensure_dir(output_root)
    if not args.no_clean:
        reset_split_dirs(output_root)

    split_map = {
        "train": train_samples,
        "val": val_samples,
        "test": test_samples,
    }

    print(f"Output root: {output_root}")
    print(f"Class count: {len(class_names)}")
    print(f"Label mode: {args.label_mode}")
    print(f"Observed CSV labels: {sorted(observed_label_ids)}")
    print(
        "Split images: "
        f"train={len(train_samples)}, val={len(val_samples)}, test={len(test_samples)}"
    )

    total_images = 0
    total_objects = 0
    total_skipped = 0

    for split_name, split_samples in split_map.items():
        img_count, obj_count, skipped_count = convert_split(
            split_name=split_name,
            split_samples=split_samples,
            output_root=output_root,
            source_to_cls=source_to_cls,
            link_mode=args.link_mode,
            log_every=args.log_every,
        )
        total_images += img_count
        total_objects += obj_count
        total_skipped += skipped_count
        print(
            f"[{split_name}] images={img_count}, objects={obj_count}, skipped_rows={skipped_count}"
        )

    yaml_path = write_data_yaml(output_root, class_names)
    print(f"Wrote data yaml: {yaml_path}")
    print(
        f"Done. images={total_images}, objects={total_objects}, skipped_rows={total_skipped}"
    )


if __name__ == "__main__":
    main()
