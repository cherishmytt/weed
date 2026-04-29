package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.lwr.entity.DetectionRecord;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 检测记录Mapper
 */
@Mapper
public interface DetectionRecordMapper extends BaseMapper<DetectionRecord> {

    /**
     * 分页查询指定时间范围的检测记录
     */
    default Page<DetectionRecord> findByTimeRange(Page<DetectionRecord> page,
                                                   @Param("startTime") LocalDateTime startTime,
                                                   @Param("endTime") LocalDateTime endTime) {
        LambdaQueryWrapper<DetectionRecord> query = new LambdaQueryWrapper<>();
        query.orderByDesc(DetectionRecord::getDetectedAt);
        if (startTime != null) {
            query.ge(DetectionRecord::getDetectedAt, startTime);
        }
        if (endTime != null) {
            query.le(DetectionRecord::getDetectedAt, endTime);
        }
        return this.selectPage(page, query);
    }

    /**
     * 统计今日检测数量和杂草作物数量
     */
    default int countTodayDetected(LocalDateTime startOfDay) {
        LambdaQueryWrapper<DetectionRecord> query = new LambdaQueryWrapper<>();
        query.ge(DetectionRecord::getDetectedAt, startOfDay);
        return Math.toIntExact(this.selectCount(query));
    }

    default int sumTodayWeedCount(LocalDateTime startOfDay) {
        LambdaQueryWrapper<DetectionRecord> query = new LambdaQueryWrapper<>();
        query.ge(DetectionRecord::getDetectedAt, startOfDay);
        List<DetectionRecord> list = this.selectList(query);
        return list.stream().mapToInt(DetectionRecord::getWeedCount).sum();
    }

    default int sumTodayCropCount(LocalDateTime startOfDay) {
        LambdaQueryWrapper<DetectionRecord> query = new LambdaQueryWrapper<>();
        query.ge(DetectionRecord::getDetectedAt, startOfDay);
        List<DetectionRecord> list = this.selectList(query);
        return list.stream().mapToInt(DetectionRecord::getCropCount).sum();
    }
}
