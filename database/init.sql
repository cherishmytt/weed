-- Active: 1775555835540@@127.0.0.1@3306@laser_weeding
-- 创建数据库
CREATE DATABASE IF NOT EXISTS laser_weeding DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE laser_weeding;

-- 1. 用户表
CREATE TABLE `user` (
  `user_id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码（BCrypt加密）',
  `email` VARCHAR(255) COMMENT '邮箱',
  `role` VARCHAR(20) NOT NULL DEFAULT 'USER' COMMENT '角色',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 初始用户 admin / 123456 (BCrypt加密)
-- BCrypt hash of '123456'
INSERT INTO `user` (`username`, `password`, `email`, `role`) VALUES
('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMye.IjzqAKL9xL5jvMFVdNJHvGCgTq/VEq', 'admin@example.com', 'ADMIN'),
('user', '$2a$10$N9qo8uLOickgx2ZMRZoMye.IjzqAKL9xL5jvMFVdNJHvGCgTq/VEq', 'user@example.com', 'USER');

-- 2. 机器人基本信息表 (本系统仅一台机器人)
CREATE TABLE `robot_info` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `robot_code` VARCHAR(50) NOT NULL COMMENT '机器人编号',
  `name` VARCHAR(100) NOT NULL COMMENT '机器人名称',
  `model` VARCHAR(50) NOT NULL COMMENT '型号',
  `current_status` INT COMMENT '当前状态: 0-离线 1-待机 2-作业中 3-故障',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器人基本信息';

INSERT INTO `robot_info` (`robot_code`, `name`, `model`, `current_status`) VALUES
('ROBOT-001', '激光除草机器人', 'LWR-2025A', 0);

-- 3. 机器人运行状态历史表
CREATE TABLE `robot_status` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `battery` FLOAT COMMENT '电量百分比',
  `speed` FLOAT COMMENT '推行速度 m/s',
  `temperature` FLOAT COMMENT '机身温度 ℃',
  `laser_on` TINYINT(1) COMMENT '激光设备是否开启',
  `cpu_usage` FLOAT COMMENT 'CPU使用率 %',
  `longitude` DOUBLE COMMENT 'GPS经度',
  `latitude` DOUBLE COMMENT 'GPS纬度',
  `imu_data` JSON COMMENT 'IMU数据: 加速度、角速度、俯仰角、横滚角',
  `reported_at` DATETIME NOT NULL COMMENT '上报时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器人运行状态历史';

-- 创建索引用于时间范围查询和多条件组合筛选
CREATE INDEX idx_reported_at ON robot_status(reported_at);
-- 复合索引优化常用组合查询
CREATE INDEX idx_reported_laser ON robot_status(reported_at, laser_on);
-- 为高频筛选字段单独创建索引
CREATE INDEX idx_battery ON robot_status(battery);
CREATE INDEX idx_temperature ON robot_status(temperature);
CREATE INDEX idx_cpu_usage ON robot_status(cpu_usage);

-- 4. 检测记录表
CREATE TABLE `detection_record` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `raw_image_path` VARCHAR(500) COMMENT '原始图片路径',
  `result_image_path` VARCHAR(500) COMMENT '结果图片路径',
  `weed_count` INT NOT NULL DEFAULT 0 COMMENT '杂草数量',
  `crop_count` INT NOT NULL DEFAULT 0 COMMENT '作物数量',
  `inference_time` INT COMMENT '推理耗时 ms',
  `detections_json` JSON NOT NULL COMMENT '检测结果JSON',
  `detected_at` DATETIME NOT NULL COMMENT '检测时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视觉检测记录表';

CREATE INDEX idx_detected_at ON detection_record(detected_at);

-- 5. 待执行指令表 (激光控制指令队列)
CREATE TABLE `robot_command` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `command_id` VARCHAR(64) UNIQUE NOT NULL COMMENT '指令ID(对外标识)',
  `action` VARCHAR(30) NOT NULL COMMENT '指令类型: ENABLE/DISABLE/FIRE/STOP/SET_POWER/AIM/SELF_TEST/RESET',
  `params_json` JSON COMMENT '指令参数JSON',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/SENT/ACKED',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `acknowledged_at` DATETIME COMMENT '确认时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器人指令队列';

CREATE INDEX idx_status ON robot_command(status);

-- 6. 激光操作日志表
CREATE TABLE `laser_operation_log` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `command_id` VARCHAR(64) NOT NULL COMMENT '对应指令ID',
  `action` VARCHAR(30) NOT NULL COMMENT '指令类型',
  `target_x` FLOAT COMMENT '目标X坐标',
  `target_y` FLOAT COMMENT '目标Y坐标',
  `depth` FLOAT COMMENT '深度',
  `duration` INT COMMENT '照射时长 ms',
  `result` VARCHAR(20) COMMENT '执行结果: SUCCESS/FAILED/TIMEOUT',
  `message` VARCHAR(500) COMMENT '附加说明',
  `executed_at` DATETIME NOT NULL COMMENT '执行时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激光操作日志';

-- 创建复合索引，优化常用查询：时间范围 + 指令类型 + 结果筛选
CREATE INDEX idx_created_at_action_result ON laser_operation_log(created_at, action, result);
CREATE INDEX idx_executed_at ON laser_operation_log(executed_at);
-- 单独给 action 和 result 创建索引用于独立筛选
CREATE INDEX idx_action ON laser_operation_log(action);
CREATE INDEX idx_result ON laser_operation_log(result);

-- 7. 激光设备状态表 (维护当前状态)
CREATE TABLE `laser_status` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `connected` TINYINT(1) DEFAULT 0 COMMENT '是否已连接',
  `status` VARCHAR(20) COMMENT '状态: disconnected/standby/aiming/firing/cooling/error',
  `status_text` VARCHAR(100) COMMENT '状态说明',
  `last_fire_at` DATETIME COMMENT '上次发射时间',
  `total_fire_count` INT DEFAULT 0 COMMENT '累计发射次数',
  `total_fire_duration` INT DEFAULT 0 COMMENT '累计发射时长 ms',
  `temperature` FLOAT COMMENT '当前温度（保留字段，暂不显示）',
  `power` FLOAT COMMENT '当前功率 W',
  `error_code` VARCHAR(50) COMMENT '错误码',
  `aim_target_x` FLOAT COMMENT '当前瞄准X坐标',
  `aim_target_y` FLOAT COMMENT '当前瞄准Y坐标',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激光设备当前状态';

-- 初始化一条记录
INSERT INTO `laser_status` (`connected`, `status`, `status_text`, `total_fire_count`, `total_fire_duration`) VALUES
(0, 'disconnected', '设备未连接', 0, 0);

-- 8. JWT黑名单表 (用于登出时使token失效)
CREATE TABLE `jwt_blacklist` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `token` VARCHAR(500) NOT NULL UNIQUE COMMENT '失效的JWT Token',
  `expires_at` DATETIME NOT NULL COMMENT 'Token原过期时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入黑名单时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='JWT黑名单';

CREATE INDEX idx_expires_at ON jwt_blacklist(expires_at);