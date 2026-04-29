package com.lwr.service.impl;

import com.lwr.common.result.Result;
import com.lwr.entity.RobotInfo;
import com.lwr.entity.RobotStatus;
import com.lwr.mapper.DetectionRecordMapper;
import com.lwr.mapper.LaserOperationLogMapper;
import com.lwr.mapper.RobotInfoMapper;
import com.lwr.mapper.RobotStatusMapper;
import com.lwr.service.StatisticsService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 统计服务实现
 */
@Service
public class StatisticsServiceImpl implements StatisticsService {

    private final RobotInfoMapper robotInfoMapper;
    private final RobotStatusMapper robotStatusMapper;
    private final DetectionRecordMapper detectionRecordMapper;
    private final LaserOperationLogMapper laserOperationLogMapper;

    public StatisticsServiceImpl(RobotInfoMapper robotInfoMapper,
                                 RobotStatusMapper robotStatusMapper,
                                 DetectionRecordMapper detectionRecordMapper,
                                 LaserOperationLogMapper laserOperationLogMapper) {
        this.robotInfoMapper = robotInfoMapper;
        this.robotStatusMapper = robotStatusMapper;
        this.detectionRecordMapper = detectionRecordMapper;
        this.laserOperationLogMapper = laserOperationLogMapper;
    }

    @Override
    public Result<?> getDashboardData() {
        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();

        // 获取机器人状态
        RobotInfo robotInfo = robotInfoMapper.getCurrent();
        Integer robotStatus = robotInfo != null ? robotInfo.getCurrentStatus() : 0;
        String statusText = getStatusText(robotStatus);

        // 获取最新电量
        Float currentBattery = null;
        RobotStatus latestStatus = robotStatusMapper.findLatest();
        if (latestStatus != null) {
            currentBattery = latestStatus.getBattery();
        }

        // 统计今日数据
        int weedTotalToday = detectionRecordMapper.sumTodayWeedCount(startOfDay);
        int cropTotalToday = detectionRecordMapper.sumTodayCropCount(startOfDay);
        int detectCountToday = detectionRecordMapper.countTodayDetected(startOfDay);
        int laserFireToday = laserOperationLogMapper.countTodayFire(startOfDay);

        Map<String, Object> data = new HashMap<>();
        data.put("robotStatus", robotStatus);
        data.put("robotStatusText", statusText);
        data.put("battery", currentBattery);
        data.put("weedTotalToday", weedTotalToday);
        data.put("cropTotalToday", cropTotalToday);
        data.put("laserFireToday", laserFireToday);
        data.put("detectCountToday", detectCountToday);

        return Result.success(data);
    }

    private String getStatusText(Integer status) {
        return switch (status == null ? 0 : status) {
            case 0 -> "离线";
            case 1 -> "待机";
            case 2 -> "作业中";
            case 3 -> "故障";
            default -> "未知";
        };
    }
}
