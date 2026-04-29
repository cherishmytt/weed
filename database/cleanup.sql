-- Active: 1775555835540@@127.0.0.1@3306@laser_weeding
-- ==========================================
-- 数据库数据清理脚本
-- 数据库: laser_weeding
-- ==========================================

USE laser_weeding;

-- ==========================================
-- 选项1: 清空所有历史数据，保留基础配置
-- 保留: user, robot_info, laser_status
-- ==========================================

-- 禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- 清空机器人运行状态历史表
TRUNCATE TABLE robot_status;

-- 清空检测记录表
TRUNCATE TABLE detection_record;

-- 清空指令队列表
TRUNCATE TABLE robot_command;

-- 清空激光操作日志表
TRUNCATE TABLE laser_operation_log;

-- 清空JWT黑名单表
TRUNCATE TABLE jwt_blacklist;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 选项2: 重置激光状态为初始值
-- ==========================================
-- UPDATE laser_status SET
--   connected = 0,
--   status = 'disconnected',
--   status_text = '设备未连接',
--   last_fire_at = NULL,
--   total_fire_count = 0,
--   total_fire_duration = 0,
--   temperature = NULL,
--   error_code = NULL,
--   updated_at = CURRENT_TIMESTAMP
-- WHERE id = 1;

-- ==========================================
-- 选项3: 重置机器人状态为初始值
-- ==========================================
-- UPDATE robot_info SET
--   current_status = 0,
--   updated_at = CURRENT_TIMESTAMP
-- WHERE id = 1;

-- ==========================================
-- 选项4: 清空所有表（包括配置表）
-- 警告: 执行后需要重新运行 init.sql
-- ==========================================
-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE laser_operation_log;
-- TRUNCATE TABLE robot_command;
-- TRUNCATE TABLE detection_record;
-- TRUNCATE TABLE robot_status;
-- TRUNCATE TABLE jwt_blacklist;
-- TRUNCATE TABLE laser_status;
-- TRUNCATE TABLE robot_info;
-- TRUNCATE TABLE user;
-- SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 选项5: 删除整个数据库
-- ==========================================
-- DROP DATABASE IF EXISTS laser_weeding;

-- ==========================================
-- 清理完成提示
-- ==========================================
SELECT '数据库清理完成' AS message;
