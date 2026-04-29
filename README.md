# 激光除草机器人运行监测系统

基于计算机视觉与激光技术的精准农业除草系统 - 软件监测控制系统。

## 技术栈

- **后端**: Spring Boot 3.2.x + MyBatis Plus + Spring Security + JWT + WebSocket
- **前端**: Vue 3 + Element Plus + Pinia + Axios + ECharts
- **数据库**: MySQL 8.x

## 项目结构

```
.
├── backend/          # Spring Boot 后端
├── frontend/        # Vue 3 前端
├── database/        # 数据库初始化脚本
├── scripts/         # 测试脚本
└── README.md
```

## 快速开始

### 1. 初始化数据库

首先确保你已经安装了MySQL，然后执行初始化脚本：

```bash
mysql -u root -p < database/init.sql
```

数据库连接配置已经在 `backend/src/main/resources/application.yml` 中配置好：
- 用户名: `root`
- 密码: `123456`
- 数据库: `laser_weeding`

### 2. 启动后端

进入backend目录，使用Maven构建并运行：

```bash
cd backend
mvn spring-boot:run
```

后端服务将在 `http://localhost:8080` 启动。

### 3. 启动前端

进入frontend目录，安装依赖并启动：

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 `http://localhost:3000` 启动，打开浏览器访问即可。

### 4. 模拟树莓派测试（可选）

使用Python脚本模拟树莓派上报数据：

```bash
cd scripts
pip install requests
python simulate_raspberry.py
```

登录用户名密码都是 `admin` / `123456`。

## 功能模块

| 模块 | 说明 |
|------|------|
| 用户认证 | JWT登录登出，token认证 |
| 机器人状态监测 | 实时状态上报，历史查询，WebSocket推送 |
| 位置追踪 | GPS轨迹查询 |
| 视觉检测 | 检测结果上报，图片存储，记录查询 |
| 激光控制 | 指令下发，状态查询，操作日志 |
| 指令轮询 | 树莓派轮询获取待执行指令 |
| 仪表盘 | 当日数据统计概览 |

## API接口

所有API都遵循RESTful风格，基础路径 `/api/v1`。

详细接口定义请参考 [接口文档.txt](./接口文档.txt)。

## 主要页面

- **仪表盘**: 实时状态展示，数据统计，WebSocket自动更新
- **状态历史**: 查询指定时间范围内的机器人运行状态
- **检测记录**: 浏览所有检测结果，支持图片预览
- **检测详情**: 查看单条检测的详细信息，包括每个检测目标的坐标、置信度等
- **激光控制**: 发送控制指令，查看设备状态和操作日志

## 通信机制

- **树莓派 → 服务端**: HTTP POST 主动上报（状态每5秒，检测完成上报结果）
- **服务端 → 树莓派**: HTTP GET 轮询获取待执行指令（每1~2秒）
- **前端 → 服务端**: WebSocket 接收实时状态推送

## 说明

本项目为软件系统，不包含硬件驱动和AI模型部分。硬件驱动和AI推理由研究生学长在树莓派端实现，本系统负责数据汇聚、存储和可视化展示。
