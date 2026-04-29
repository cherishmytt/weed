CREATE DATABASE IF NOT EXISTS `global_fire_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `global_fire_system`;

CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` VARCHAR(20) NOT NULL DEFAULT 'viewer',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_user_username` (`username`),
  UNIQUE KEY `uk_sys_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `import_batches` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `batch_name` VARCHAR(120) NOT NULL,
  `source_type` VARCHAR(50) NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `record_count` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `import_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `remark` TEXT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `country_boundaries` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `country_name` VARCHAR(120) NOT NULL,
  `country_code` VARCHAR(10) NULL,
  `geojson` JSON NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_country_name` (`country_name`),
  KEY `idx_country_code` (`country_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `fire_points` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `latitude` DOUBLE NOT NULL,
  `longitude` DOUBLE NOT NULL,
  `bright_ti4` DOUBLE NULL,
  `scan` DOUBLE NULL,
  `track` DOUBLE NULL,
  `acq_date` DATE NOT NULL,
  `acq_time` VARCHAR(8) NOT NULL,
  `acq_time_padded` VARCHAR(8) NULL,
  `acq_datetime` DATETIME NOT NULL,
  `satellite` VARCHAR(30) NULL,
  `instrument` VARCHAR(30) NULL,
  `confidence` VARCHAR(20) NULL,
  `version` VARCHAR(30) NULL,
  `bright_ti5` DOUBLE NULL,
  `frp` DOUBLE NULL,
  `daynight` VARCHAR(5) NULL,
  `country_name` VARCHAR(120) NULL,
  `country_code` VARCHAR(10) NULL,
  `source_product` VARCHAR(60) NULL,
  `area_label` VARCHAR(50) NULL,
  `source_file` VARCHAR(255) NULL,
  `import_batch_id` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_fire_acq_date` (`acq_date`),
  KEY `idx_fire_acq_datetime` (`acq_datetime`),
  KEY `idx_fire_area_label` (`area_label`),
  KEY `idx_fire_source_product` (`source_product`),
  KEY `idx_fire_satellite` (`satellite`),
  KEY `idx_fire_instrument` (`instrument`),
  KEY `idx_fire_confidence` (`confidence`),
  KEY `idx_fire_daynight` (`daynight`),
  KEY `idx_fire_country_name` (`country_name`),
  KEY `idx_fire_country_code` (`country_code`),
  KEY `idx_fire_batch_id` (`import_batch_id`),
  KEY `idx_fire_area_source_time` (`area_label`, `source_product`, `acq_datetime`),
  KEY `idx_fire_area_time` (`area_label`, `acq_datetime`),
  KEY `idx_fire_area_date` (`area_label`, `acq_date`),
  KEY `idx_fire_country_time` (`country_name`, `acq_datetime`),
  KEY `idx_fire_area_time_country` (`area_label`, `acq_datetime`, `country_name`),
  KEY `idx_fire_area_time_daynight` (`area_label`, `acq_datetime`, `daynight`),
  KEY `idx_fire_area_time_source` (`area_label`, `acq_datetime`, `source_product`),
  KEY `idx_fire_area_time_date` (`area_label`, `acq_datetime`, `acq_date`),
  CONSTRAINT `fk_fire_batch` FOREIGN KEY (`import_batch_id`) REFERENCES `import_batches` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `sys_config` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `config_key` VARCHAR(100) NOT NULL,
  `config_value` TEXT NOT NULL,
  `remark` VARCHAR(255) NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sys_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `sync_jobs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `job_name` VARCHAR(120) NOT NULL,
  `trigger_time` DATETIME NOT NULL,
  `run_type` VARCHAR(30) NOT NULL DEFAULT 'manual',
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `started_at` DATETIME NULL,
  `finished_at` DATETIME NULL,
  `estimated_seconds` INT NULL,
  `actual_seconds` INT NULL,
  `total_tasks` INT NOT NULL DEFAULT 0,
  `completed_tasks` INT NOT NULL DEFAULT 0,
  `current_step` VARCHAR(60) NULL,
  `current_target` VARCHAR(120) NULL,
  `fetched_count` INT NOT NULL DEFAULT 0,
  `inserted_count` INT NOT NULL DEFAULT 0,
  `skipped_count` INT NOT NULL DEFAULT 0,
  `deleted_count` INT NOT NULL DEFAULT 0,
  `message` TEXT NULL,
  `target_areas` JSON NULL,
  `target_sources` JSON NULL,
  `triggered_by_user_id` BIGINT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sync_jobs_status` (`status`),
  KEY `idx_sync_jobs_triggered_by` (`triggered_by_user_id`),
  KEY `idx_sync_jobs_trigger_time` (`trigger_time`),
  CONSTRAINT `fk_sync_jobs_user` FOREIGN KEY (`triggered_by_user_id`) REFERENCES `sys_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `sync_job_details` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `job_id` BIGINT NOT NULL,
  `area_label` VARCHAR(60) NOT NULL,
  `source_product` VARCHAR(60) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'pending',
  `step` VARCHAR(60) NULL,
  `started_at` DATETIME NULL,
  `finished_at` DATETIME NULL,
  `fetched_count` INT NOT NULL DEFAULT 0,
  `inserted_count` INT NOT NULL DEFAULT 0,
  `skipped_count` INT NOT NULL DEFAULT 0,
  `deleted_count` INT NOT NULL DEFAULT 0,
  `message` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sync_job_details_job_id` (`job_id`),
  KEY `idx_sync_job_details_area_label` (`area_label`),
  KEY `idx_sync_job_details_source_product` (`source_product`),
  KEY `idx_sync_job_details_status` (`status`),
  CONSTRAINT `fk_sync_job_details_job` FOREIGN KEY (`job_id`) REFERENCES `sync_jobs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
