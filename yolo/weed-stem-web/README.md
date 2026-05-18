# Weed Stem Web (Spring Boot)

这个项目把你训练好的 YOLOv8s pose 模型接入了一个 Spring Boot 页面，支持：

- 上传图片
- 检测杂草（可配置 `classes`）
- 展示结果图（框 + 茎点）
- 返回每个目标的 `bbox` 和 `stem(x,y)` 坐标

当前推荐配套模型为两类模型：

- `0 = Crop`
- `1 = Weed`
- 权重路径：`D:/yolo/runs/cnw_crop_weed_pose/weights/best.pt`

## 1. 环境要求

- JDK 17+
- Maven 3.9+
- Python 环境（建议与你训练一致）：`D:/anaconda3/envs/yolopose/python.exe`
- 该 Python 环境需安装：`requirements.txt`

```powershell
cd D:\yolo\weed-stem-web
pip install -r requirements.txt
```

## 2. 关键配置

编辑 [application.yml](/D:/yolo/weed-stem-web/src/main/resources/application.yml):

- `app.model.python-executable`
- `app.model.script-path`
- `app.model.weight-path`
- `app.model.output-root`
- `app.model.classes` (`1` 代表 Weed，使用 `cnw_crop_weed_pose` 两类模型时)
- `server.port`（当前为 `6080`）

页面和 API 也都支持传入 `classes` 参数（如 `1` 或 `0,1`）。

## 3. 训练模型

两类模型训练脚本：

```powershell
D:\yolo\tools\train_crop_weed_pose.ps1
```

训练数据配置：

```text
D:/yolo/datasets/cnw_crop_weed_pose/data.yaml
```

## 4. 启动

在项目目录执行：

```powershell
cd D:\yolo\weed-stem-web
mvn -U clean spring-boot:run
```

启动后访问：`http://localhost:6080`

## 5. API 调用

`POST /api/predict`，`form-data`：

- `file`: 图片文件
- `conf`: 置信度（可选，默认 `0.25`）
- `classes`: 类别过滤（可选，默认 `1`，留空表示不过滤）

返回 JSON 包含：

- `result.detections[].bbox`
- `result.detections[].stem`
- `outputImageUrl`
