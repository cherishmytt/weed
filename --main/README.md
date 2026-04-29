# 全球野火火点监测与时空分析平台

基于 `Vue 3 + Vite + Cesium + ECharts + Element Plus` 与 `FastAPI + MySQL` 的完整 WebGIS 示例项目，包含：

- 登录注册与 JWT 鉴权
- 用户与权限管理
- FIRMS 火点 CSV 导入
- FIRMS 多天 merged CSV 批量导入
- 国家边界 GeoJSON 导入
- 全球三维火点展示与时间回放
- 统计分析页面
- 国家专题分析页面
- 火点详情与天气联动页面
- 手动数据同步管理
- 科技风全屏数据大屏

## 目录结构

```text
global_fire_system/
├─ backend/                    # FastAPI 后端
│  ├─ app/
│  │  ├─ api/routes/           # 认证、用户、导入、火点、分析、大屏接口
│  │  ├─ core/                 # 配置、鉴权、依赖注入、日志
│  │  ├─ db/                   # 数据库连接
│  │  ├─ models/               # SQLAlchemy 模型
│  │  ├─ schemas/              # Pydantic 模型
│  │  └─ services/             # 导入、国家匹配、分析服务
│  ├─ scripts/                 # 初始化与样例数据导入脚本
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/                   # Vue 3 前端
│  ├─ public/data/             # 世界国家 GeoJSON
│  ├─ src/
│  │  ├─ api/                  # Axios 请求层
│  │  ├─ components/           # Cesium、图表、卡片、时间轴组件
│  │  ├─ layout/               # 后台布局
│  │  ├─ router/               # 路由与守卫
│  │  ├─ stores/               # Pinia 状态
│  │  ├─ styles/               # 全局主题样式
│  │  └─ views/                # 登录、总览、数据、地图、分析、大屏、用户页
│  ├─ package.json
│  └─ .env.example
├─ data/                       # 本地样例数据（公开仓库默认不提交大体量 CSV）
├─ sql/schema.sql              # MySQL 建表 SQL
└─ README.md
```

## 技术栈

- 前端：Vue 3、Vite、Cesium、ECharts、Element Plus、Pinia、Vue Router
- 后端：FastAPI、SQLAlchemy、JWT、Shapely
- 数据库：MySQL 8+

## MySQL 配置

公开仓库版本不包含真实数据库密码或 API 密钥，请按自己的环境配置：

- Host: `127.0.0.1`
- Port: `3306`
- User: `your_mysql_user`
- Password: `your_mysql_password`
- Database: `global_fire_system`

如果你希望改配置，可复制 `backend/.env.example` 为 `backend/.env` 后修改。

同步相关默认配置也已在示例环境文件中给出，包括：

- `FIRMS_API_KEY`
- `SYNC_WINDOW_DAYS`
- `SYNC_OVERLAP_HOURS`
- `SYNC_TASK_CHUNK_DAYS`

## 一、初始化数据库

### 方式 1：执行 SQL

运行 `sql/schema.sql`。

### 方式 2：由 FastAPI 自动建表

后端启动时会自动 `create_all`，并自动写入：

- 默认管理员账号由 `DEFAULT_ADMIN_USERNAME` 与 `DEFAULT_ADMIN_PASSWORD` 控制，建议在 `backend/.env` 中自行配置。
- `sys_config` 中的 Open-Meteo 字段配置

## 二、启动后端

```powershell
Set-Location path\to\global_fire_system\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\init_db.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端文档：

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 导入样例数据

```powershell
Set-Location path\to\global_fire_system\backend
.\.venv\Scripts\Activate.ps1
python .\scripts\import_sample_data.py
```

## 二点五、导入多天 merged CSV

当前项目兼容你自行放在 `data/firms_downloads` 目录下的 merged CSV，包括：

- `firms_seasia_30days_merged.csv`
- `firms_world_7days_merged.csv`
- `firms_australia_30days_merged.csv`
- `firms_south_america_30days_merged.csv`
- `firms_seasia_30days_snpp_merged.csv`
- `firms_world_7days_snpp_merged.csv`

这些 merged CSV 已经自带：

- `source_product`
- `area_label`
- `source_file`
- `acq_time_padded`
- `acq_datetime`

系统会优先使用这些字段，不会重复生成。

### 方式 1：后台多文件上传

进入“数据管理”页面后，可一次选择多份 CSV 上传。后端会：

- 为每个文件单独生成导入批次
- 自动写入 `import_batch_id`
- 保留 `source_product / area_label / source_file`
- 使用 `acq_datetime` 作为统一时间主字段
- 自动补全缺失的国家信息

### 方式 2：命令行批量导入目录

```powershell
Set-Location path\to\global_fire_system\backend
.\.venv\Scripts\Activate.ps1
python .\scripts\import_merged_data.py
```

如需指定目录：

```powershell
python .\scripts\import_merged_data.py --folder "path\to\global_fire_system\data\firms_downloads"
```

### 导入前建议

- 先确保国家边界已导入，否则新火点无法自动匹配国家。
- 先运行一次 `backend/scripts/init_db.py`，它会自动补齐 `fire_points` 表缺失字段与索引。
- 如果你是基于旧库升级，也可以手动执行 `sql/alter_fire_points_multiday.sql`。

### 多区域数据使用建议

由于 `world` 与 `seasia / australia / south_america` 本身存在空间范围重叠，导入到同一张表后属于“按 `area_label` 区分的并行数据集”。  
实际展示时建议：

- 首页 / 大屏默认使用 `area_label=world`
- 区域地图回放和分析使用具体区域 `area_label`
- 若不加 `area_label` 直接全库统计，会把全球与区域数据一起算进去

## 三、启动前端

```powershell
Set-Location path\to\global_fire_system\frontend
npm install
npm run dev
```

前端地址：

- `http://127.0.0.1:5173`

如需修改接口地址，可复制 `frontend/.env.example` 为 `frontend/.env`。

## 默认账号说明

公开仓库版本不内置可直接使用的默认密码，请在 `backend/.env` 中自行配置管理员账号与密码。

## 开源仓库说明

- 仓库默认不提交本地虚拟环境、构建产物、`node_modules`、缓存文件与大体量 CSV 数据。
- `data` 目录中的示例数据文件建议由使用者自行准备。
- 天地图 Key、FIRMS API Key、数据库账号密码等敏感配置需要使用者自行填写。

## 已实现接口

### 认证接口

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/profile`
- `POST /api/auth/change-password`

### 用户管理接口

- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`

### 导入接口

- `POST /api/import/fire-csv`
- `POST /api/import/country-boundary`
- `GET /api/import/batches`
- `DELETE /api/import/batches/{id}`

### 火点接口

- `GET /api/fire/filter-options`
- `GET /api/fire/list`
- `GET /api/fire/latest`
- `GET /api/fire/range`
- `GET /api/fire/bbox`
- `GET /api/fire/{id}`
- `GET /api/fire/{id}/related`
- `DELETE /api/fire/{id}`
- `GET /api/fire/export`

### 分析接口

- `GET /api/analysis/overview`
- `GET /api/analysis/timeline`
- `GET /api/analysis/country-top`
- `GET /api/analysis/satellite-pie`
- `GET /api/analysis/daynight-pie`
- `GET /api/analysis/frp-distribution`
- `GET /api/analysis/country-choropleth`
- `GET /api/analysis/country-detail`
- `GET /api/analysis/country-trend`
- `GET /api/analysis/country-frp-distribution`
- `GET /api/analysis/country-daynight-pie`
- `GET /api/analysis/country-source-product-pie`

### 大屏接口

- `GET /api/dashboard/summary`
- `GET /api/dashboard/hotspots`
- `GET /api/dashboard/rankings`
- `GET /api/dashboard/trends`
- `GET /api/dashboard/cruise-points`

### 同步接口

- `POST /api/sync/estimate`
- `POST /api/sync/run-now`
- `GET /api/sync/status`
- `GET /api/sync/history`

## 页面说明

- 登录/注册页：科技感登录与注册入口
- 平台总览：关键指标卡片与模块快捷入口
- 数据展示与分析：适合日常查看与截图展示的综合分析页
- 数据管理页：数据导入、筛选、导出、批次管理
- 三维地图页：Cesium 地球、火点点击详情、时间回放
- 分析页：趋势、排行、占比、世界着色图
- 国家专题分析：围绕国家维度的排行、专题图、趋势与结构分析
- 火点详情页：单条火点属性、定位、天气与相关火点联动
- 数据同步管理：手动触发最近 30 天窗口同步、预估耗时、查看进度与历史
- 大屏页：独立全屏科技风展示页
- 用户管理页：管理员维护账号与角色

## 说明

- 国家匹配基于 `Shapely + STRtree`，依赖已导入的国家边界数据。
- 第一版时间轴支持按天和按小时分组回放，其中按天更稳定。
- 大屏页使用独立路由 `/screen`，方便演示时直接全屏展示。
- Cesium 默认使用本地 NaturalEarthII 底图资源，不依赖 Cesium Ion Token。

## 开源协议

本项目采用 `MIT License` 开源，详见仓库根目录下的 `LICENSE` 文件。

## 手动同步说明

系统新增了“数据同步管理”页面，仅管理员可见。当前同步策略为：

- 手动触发，不自动定时执行
- 以点击“开始同步”时的系统时间为基准
- 维持最近 30 天在线数据窗口
- 先抓取和入库，再清理窗口外旧数据
- 同步前会先估算任务范围和预计耗时
- 同步中会显示步骤、进度、当前目标和历史记录

默认同步目标包括：

- 区域：`world`、`seasia`、`australia`、`south_america`
- 数据源：`VIIRS_NOAA20_NRT`、`VIIRS_SNPP_NRT`
