# YOLOv8s-pose 训练 CropAndWeed 数据集方案

## 关键观察

CropAndWeed 的标注格式为 `Left, Top, Right, Bottom, Label ID, Stem X, Stem Y`，每个目标自带 **1 个茎点 (Stem) 坐标**。这正好可以作为 YOLOv8-pose 的 **单关键点 (1 keypoint)** 进行训练 —— pose 模型用在该数据集上是天然契合的建模方式。

最终每个实例同时输出：
- 类别
- 边界框 (bbox)
- 茎点位置 (keypoint)，可用于后续精准除草/定位

---

## 1. 环境准备（conda + RTX 5060 Ti 16G）

> **注意**：RTX 5060 Ti 是 Blackwell 架构（compute capability `sm_120`），需要 **CUDA 12.8 及以上** 的 PyTorch，否则会报 `no kernel image is available for execution on the device`。老的 cu121 轮子不支持。

```bash
# 1) 新建 conda 环境
conda create -n yolopose python=3.11 -y
conda activate yolopose

# 2) 装 CUDA 12.8 版 PyTorch（支持 Blackwell / sm_120）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 若 cu128 稳定版尚不可用，则装 nightly：
# pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128

# 3) 装 ultralytics（自带 YOLOv8 全家族）
pip install ultralytics
```

验证：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# 期望输出类似: 2.5.x  True  NVIDIA GeForce RTX 5060 Ti

yolo checks
```

若 `torch.cuda.is_available()` 为 `True` 但矩阵乘会报 sm_120 错，就说明 torch 还不认 Blackwell —— 换 nightly。

---

## 2. 下载 YOLOv8s-pose 预训练权重

方式 A：首次运行自动下载

```python
from ultralytics import YOLO
YOLO('yolov8s-pose.pt')   # 会下载到当前目录
```

方式 B：从 GitHub Release 手动下载
- 地址：`https://github.com/ultralytics/assets/releases`
- 文件：`yolov8s-pose.pt`
- 放到 `D:\yolo\weights\yolov8s-pose.pt`

---

## 3. 准备 CropAndWeed 原始数据

进入已有的 `cropandweed` 仓库，下载图像并映射到想用的类别变体：

```bash
cd "D:\laser_task_assignment - crossattention_pro\cropandweed"
pip install -r requirements.txt

# 下载所有原始图像与标注（会下载 tar 包并解压到 data/）
python cnw/setup.py

# 映射到推荐变体（9 类，上手更容易）
python cnw/map_dataset.py --dataset_target CropsOrWeed9
```

产出目录结构：

```
cropandweed/data/
├── images/                     # 全部 jpg 图像
├── bboxes/CropsOrWeed9/        # 每张图一个 .csv（Left,Top,Right,Bottom,LabelID,StemX,StemY）
├── labelIds/CropsOrWeed9/      # 语义分割掩码（本任务不用）
└── params/                     # 附加参数（本任务不用）
```

**类别变体选择建议**：

- `CropsOrWeed9`：9 类，样本均衡，推荐首次训练
- `CropAndWeed`：全量 74 类，长尾严重，需要加权/更长 epochs
- 也可以在 `cnw/utilities/datasets.py` 中自定义变体

---

## 4. CNW → YOLO-pose 格式转换

YOLO-pose 的标签格式（每行一个实例）：

```
cls  cx  cy  w  h   kx  ky  v
```

- `cx cy w h` 均归一化到 `[0,1]`（相对图像宽高）
- `kx ky` 关键点坐标，同样归一化
- `v`：可见性，`2=可见`、`1=遮挡`、`0=不存在`

### 4.1 目录规划

```
D:\yolo\datasets\cnw_pose\
├── images\
│   ├── train\  *.jpg
│   ├── val\    *.jpg
│   └── test\   *.jpg
├── labels\
│   ├── train\  *.txt
│   ├── val\    *.txt
│   └── test\   *.txt
└── data.yaml
```

### 4.2 转换脚本（`D:\yolo\tools\cnw2yolo.py`）要做的事

1. 遍历 `cropandweed/data/bboxes/CropsOrWeed9/*.csv`
2. 找到同名 `data/images/*.jpg`，读取图像宽 `W`、高 `H`
3. 对每一行：
   - `cx = (L+R)/2/W`，`cy = (T+B)/2/H`，`w = (R-L)/W`，`h = (B-T)/H`
   - `kx = StemX/W`，`ky = StemY/H`，`v = 2`（若 StemX/Y 为 -1 则 `v=0`）
   - 从 `datasets.py` 里拿到 LabelID → 连续 `cls` 的映射
4. 按 80/10/10 随机划分（固定 random seed） 
5. 图像与 txt 分别拷贝/软链接到 `images/{split}` 和 `labels/{split}`

---

## 5. 编写 `data.yaml`

`D:\yolo\datasets\cnw_pose\data.yaml`：

```yaml
path: D:/yolo/datasets/cnw_pose
train: images/train
val:   images/val
test:  images/test

kpt_shape: [1, 3]        # 1 个关键点，每点 3 维 (x, y, v)
flip_idx: [0]            # 水平翻转后关键点索引不变

names:
  0: Maize
  1: Sugar beet
  2: Soybean
  3: Sunflower
  4: Potato
  5: Pumpkin
  # ... 共 9 类，以 cnw/utilities/datasets.py 中 CropsOrWeed9 的定义为准
```

> ⚠️ 类名与顺序必须与步骤 4 中 `LabelID → cls` 的映射严格一致，否则训练集/评估集对不上号。

---

## 6. 训练

```bash
cd /d D:\yolo
.venv\Scripts\activate

yolo pose train ^
    model=yolov8s-pose.pt ^
    data=D:/yolo/datasets/cnw_pose/data.yaml ^
    epochs=100 ^
    imgsz=640 ^
    batch=32 ^
    device=0 ^
    workers=8 ^
    amp=True ^
    project=D:/yolo/runs ^
    name=cnw_s_pose
```

关键参数说明：

| 参数 | 含义 | 调整建议 |
|---|---|---|
| `epochs` | 训练轮数 | 数据量大可先 50 轮看曲线 |
| `imgsz` | 输入分辨率 | 小目标（杂草幼苗）可加到 960 |
| `batch` | 批大小 | 16 GB 显存建议 **32**（640 输入）；imgsz=960 时降到 16 |
| `device` | GPU 编号 | 多卡 `device=0,1` |
| `patience` | 早停耐心 | 默认 100，够用 |

训练产物：`D:\yolo\runs\cnw_s_pose\weights\{best.pt, last.pt}` 及 `results.png` 曲线。

---

## 7. 验证与推理

```bash
# 在验证集上评估 mAP / OKS
yolo pose val model=D:/yolo/runs/cnw_s_pose/weights/best.pt ^
              data=D:/yolo/datasets/cnw_pose/data.yaml

# 单图推理
yolo pose predict model=D:/yolo/runs/cnw_s_pose/weights/best.pt ^
                  source=D:/yolo/datasets/cnw_pose/images/test ^
                  save=True conf=0.25

# 导出 ONNX（部署用）
yolo export model=D:/yolo/runs/cnw_s_pose/weights/best.pt format=onnx opset=12
```

---

## 8. 调优方向（训练后视结果选做）

- **长尾/小目标**：加大 `imgsz` 到 960，开启 `close_mosaic=10` 最后 10 轮关闭 mosaic
- **关键点定位不准**：增加 `pose` loss 权重（`pose=20.0`，默认 12）
- **过拟合**：加 `mixup=0.1`、`hsv_v=0.5`，减小 epochs
- **欠拟合**：改用 `yolov8m-pose.pt`，或训练更多轮

---

## 执行顺序清单

- [ ] 1. 确认是否有 NVIDIA GPU，装对应 PyTorch
- [ ] 2. `pip install ultralytics`，下载 `yolov8s-pose.pt`
- [ ] 3. 运行 `cnw/setup.py` 和 `map_dataset.py --dataset_target CropsOrWeed9`
- [ ] 4. 写 `D:\yolo\tools\cnw2yolo.py`，产出 YOLO 格式数据集
- [ ] 5. 写 `data.yaml`（类名顺序对齐）
- [ ] 6. `yolo pose train ...` 开始训练
- [ ] 7. `yolo pose val` / `predict` 评估与可视化
