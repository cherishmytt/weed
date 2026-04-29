USE `global_fire_system`;

SET @db_name = DATABASE();

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND column_name = 'acq_time_padded'
    ),
    'SELECT 1',
    'ALTER TABLE `fire_points` ADD COLUMN `acq_time_padded` VARCHAR(8) NULL AFTER `acq_time`'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND column_name = 'source_product'
    ),
    'SELECT 1',
    'ALTER TABLE `fire_points` ADD COLUMN `source_product` VARCHAR(60) NULL AFTER `country_code`'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND column_name = 'area_label'
    ),
    'SELECT 1',
    'ALTER TABLE `fire_points` ADD COLUMN `area_label` VARCHAR(50) NULL AFTER `source_product`'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND index_name = 'idx_fire_area_label'
    ),
    'SELECT 1',
    'CREATE INDEX `idx_fire_area_label` ON `fire_points` (`area_label`)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND index_name = 'idx_fire_source_product'
    ),
    'SELECT 1',
    'CREATE INDEX `idx_fire_source_product` ON `fire_points` (`source_product`)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (
  SELECT IF(
    EXISTS (
      SELECT 1
      FROM information_schema.statistics
      WHERE table_schema = @db_name
        AND table_name = 'fire_points'
        AND index_name = 'idx_fire_area_source_time'
    ),
    'SELECT 1',
    'CREATE INDEX `idx_fire_area_source_time` ON `fire_points` (`area_label`, `source_product`, `acq_datetime`)'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
