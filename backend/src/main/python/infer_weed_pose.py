#!/usr/bin/env python3
"""
Run YOLOv8 pose inference and export:
1) annotated image
2) JSON with bbox + stem keypoint per detection
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 pose single-image inference.")
    parser.add_argument("--model", type=Path, required=True, help="Path to best.pt")
    parser.add_argument("--input", type=Path, required=True, help="Path to input image")
    parser.add_argument("--output-image", type=Path, required=True, help="Path to save annotated image")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to save JSON result")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--classes", type=str, default="", help="Class ids, e.g. '8' or '0,8'")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    return parser.parse_args()


def parse_classes(raw: str) -> list[int] | None:
    raw = raw.strip()
    if not raw:
        return None
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def to_float(v: Any) -> float:
    return float(v.item()) if hasattr(v, "item") else float(v)


def main() -> None:
    args = parse_args()

    if not args.model.exists():
        raise FileNotFoundError(f"Model not found: {args.model}")
    if not args.input.exists():
        raise FileNotFoundError(f"Input image not found: {args.input}")

    args.output_image.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)

    classes = parse_classes(args.classes)
    model = YOLO(str(args.model))
    results = model.predict(
        source=str(args.input),
        conf=args.conf,
        classes=classes,
        imgsz=args.imgsz,
        verbose=False,
        save=False,
    )
    if not results:
        raise RuntimeError("No result returned by model.predict.")

    result = results[0]
    annotated = result.plot(conf=True, labels=True, boxes=True)
    cv2.imwrite(str(args.output_image), annotated)

    detections: list[dict[str, Any]] = []
    boxes = result.boxes
    keypoints = result.keypoints
    names = result.names if isinstance(result.names, dict) else {}

    if boxes is not None and boxes.xyxy is not None:
        n = len(boxes.xyxy)
        for i in range(n):
            cls_id = int(to_float(boxes.cls[i]))
            conf = to_float(boxes.conf[i])
            x1, y1, x2, y2 = [to_float(v) for v in boxes.xyxy[i]]

            stem_x = 0.0
            stem_y = 0.0
            if keypoints is not None and keypoints.xy is not None and len(keypoints.xy) > i:
                # shape: [N, K, 2], here K=1
                stem_x = to_float(keypoints.xy[i][0][0])
                stem_y = to_float(keypoints.xy[i][0][1])

            detections.append(
                {
                    "classId": cls_id,
                    "className": names.get(cls_id, str(cls_id)),
                    "confidence": conf,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "stem": {"x": stem_x, "y": stem_y},
                }
            )

    h, w = result.orig_shape
    payload = {
        "image": args.input.name,
        "width": int(w),
        "height": int(h),
        "detections": detections,
    }

    with args.output_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"infer ok, detections={len(detections)}")
    print(f"output_image={args.output_image}")
    print(f"output_json={args.output_json}")


if __name__ == "__main__":
    main()
