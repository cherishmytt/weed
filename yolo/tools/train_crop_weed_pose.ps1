$ErrorActionPreference = "Stop"

$YoloExe = "D:/anaconda3/envs/yolopose/Scripts/yolo.exe"
if (-not (Test-Path $YoloExe)) {
  $YoloExe = "yolo"
}

& $YoloExe pose train `
  model=D:/yolo/yolov8s-pose.pt `
  data=D:/yolo/datasets/cnw_crop_weed_pose/data.yaml `
  epochs=80 `
  imgsz=640 `
  batch=32 `
  device=0 `
  workers=0 `
  amp=True `
  plots=False `
  cache=False `
  project=D:/yolo/runs `
  name=cnw_crop_weed_pose `
  exist_ok=True
 