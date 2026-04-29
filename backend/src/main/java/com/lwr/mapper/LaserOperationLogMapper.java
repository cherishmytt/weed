package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.LaserOperationLog;
import org.apache.ibatis.annotations.Mapper;

import java.time.LocalDateTime;

/**
 * 激光操作日志Mapper
 */
@Mapper
public interface LaserOperationLogMapper extends BaseMapper<LaserOperationLog> {

    /**
     * 分页查询日志
     */
    default Page<LaserOperationLog> findByTimeRange(Page<LaserOperationLog> page,
                                                    LocalDateTime startTime,
                                                    LocalDateTime endTime) {
        LambdaQueryWrapper<LaserOperationLog> query = new LambdaQueryWrapper<>();
        query.orderByDesc(LaserOperationLog::getExecutedAt);
        if (startTime != null) {
            query.ge(LaserOperationLog::getExecutedAt, startTime);
        }
        if (endTime != null) {
            query.le(LaserOperationLog::getExecutedAt, endTime);
        }
        return this.selectPage(page, query);
    }

    /**
     * 统计今日激光发射次数
     */
    default int countTodayFire(LocalDateTime startOfDay) {
        LambdaQueryWrapper<LaserOperationLog> query = new LambdaQueryWrapper<>();
        query.ge(LaserOperationLog::getExecutedAt, startOfDay)
              .eq(LaserOperationLog::getResult, "SUCCESS");
        return Math.toIntExact(this.selectCount(query));
    }
}
